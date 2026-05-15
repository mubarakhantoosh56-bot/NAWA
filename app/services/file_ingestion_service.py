"""Synchronous RAG file ingestion service for MVP text files."""

import logging
import shutil
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg

from app.repositories.department_repository import DepartmentRepository
from app.repositories.file_chunk_repository import FileChunkRepository
from app.repositories.file_repository import FileRepository
from app.services.rag.embeddings import store_chunk_embeddings
from app.services.rag.chunking import chunk_text
from app.services.rag.extractors import SUPPORTED_EXTENSIONS, extract_text

RowDict = dict[str, object]

STORAGE_ROOT = Path("storage") / "files"
logger = logging.getLogger(__name__)


class FileIngestionService:
    """Ingest local text-like files into tenant-scoped RAG tables."""

    def __init__(
        self,
        db: asyncpg.Connection | asyncpg.Pool,
        storage_root: Path | str = STORAGE_ROOT,
    ) -> None:
        """Initialize the service with a database handle and storage root."""
        self.db = db
        self.storage_root = Path(storage_root)
        self.file_repo = FileRepository(db)
        self.file_chunk_repo = FileChunkRepository(db)
        self.department_repo = DepartmentRepository(db)

    async def ingest_file(
        self,
        company_id: UUID,
        uploaded_by_user_id: UUID,
        source_path: Path | str,
        filename: str,
        content_type: str,
        department_id: UUID | None = None,
    ) -> RowDict:
        """Store, extract, chunk, and record an MVP text-like file."""
        source = Path(source_path)
        self._validate_supported_filename(filename)
        await self._validate_department(company_id, department_id)

        file_id = uuid4()
        storage_path = self._storage_path(company_id=company_id, file_id=file_id)
        file_record = await self.file_repo.create_file(
            company_id=company_id,
            uploaded_by_user_id=uploaded_by_user_id,
            filename=filename,
            content_type=content_type,
            file_size_bytes=source.stat().st_size,
            storage_path=str(storage_path),
            department_id=department_id,
            status="processing",
            metadata={},
            created_by_user_id=uploaded_by_user_id,
            file_id=file_id,
        )

        try:
            self._save_source_file(source=source, destination=storage_path)
            extracted = extract_text(storage_path, filename=filename, content_type=content_type)
            text = str(extracted.get("text") or "")
            chunks = chunk_text(text)
            if not chunks:
                raise ValueError("file contains no extractable text")

            created_chunks = await self.file_chunk_repo.create_chunks(
                company_id=company_id,
                file_id=file_record["id"],
                department_id=department_id,
                chunks=chunks,
            )

            embedding_status = "skipped"
            embedding_count = 0
            try:
                embedding_count = await store_chunk_embeddings(
                    db=self.db,
                    company_id=company_id,
                    file_id=file_record["id"],
                    department_id=department_id,
                    chunks=created_chunks,
                )
                if embedding_count == len(created_chunks):
                    embedding_status = "ready"
                elif embedding_count > 0:
                    embedding_status = "partial"
                else:
                    embedding_status = "failed"
                logger.info(
                    "rag_embeddings_generated",
                    extra={
                        "company_id": str(company_id),
                        "file_id": str(file_record["id"]),
                        "department_id": str(department_id) if department_id else None,
                        "chunks_total": len(created_chunks),
                        "embeddings_stored": embedding_count,
                        "embedding_status": embedding_status,
                    },
                )
            except Exception as exc:
                embedding_status = "failed"
                logger.warning(
                    "rag_embeddings_failed",
                    extra={
                        "company_id": str(company_id),
                        "file_id": str(file_record["id"]),
                        "department_id": str(department_id) if department_id else None,
                        "chunks_total": len(created_chunks),
                        "embeddings_stored": embedding_count,
                        "error_type": type(exc).__name__,
                    },
                )

            ready_file = await self.file_repo.update_file_status(
                company_id=company_id,
                file_id=file_record["id"],
                status="ready",
                metadata={
                    "extraction": extracted.get("metadata") or {},
                    "chunk_count": len(created_chunks),
                    "embedding_status": embedding_status,
                    "embedding_count": embedding_count,
                },
                updated_by_user_id=uploaded_by_user_id,
            )
            return {
                "file": ready_file or file_record,
                "chunks": created_chunks,
            }
        except (OSError, ValueError, KeyError) as exc:
            failed_file = await self.file_repo.update_file_status(
                company_id=company_id,
                file_id=file_record["id"],
                status="failed",
                metadata={"error": self._safe_error(exc)},
                updated_by_user_id=uploaded_by_user_id,
            )
            return {
                "file": failed_file or file_record,
                "chunks": [],
                "error": self._safe_error(exc),
            }

    async def list_files(
        self,
        company_id: UUID,
        department_id: UUID | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RowDict]:
        """Return files for one tenant, optionally filtered by department/status."""
        await self._validate_department(company_id, department_id)
        return await self.file_repo.list_files(
            company_id=company_id,
            department_id=department_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_file(
        self,
        company_id: UUID,
        file_id: UUID,
    ) -> RowDict | None:
        """Return one tenant file with active chunk count."""
        file_record = await self.file_repo.get_file_by_id(
            company_id=company_id,
            file_id=file_id,
        )
        if file_record is None:
            return None

        chunk_count = await self.file_chunk_repo.count_chunks_by_file(
            company_id=company_id,
            file_id=file_id,
        )
        return {
            **file_record,
            "chunk_count": chunk_count,
        }

    async def _validate_department(
        self,
        company_id: UUID,
        department_id: UUID | None,
    ) -> None:
        if department_id is None:
            return

        department = await self.department_repo.get_by_id(
            company_id=company_id,
            department_id=department_id,
        )
        if department is None:
            raise ValueError("invalid department")

    def _storage_path(self, company_id: UUID, file_id: UUID) -> Path:
        return self.storage_root / str(company_id) / str(file_id) / "source"

    @staticmethod
    def _save_source_file(source: Path, destination: Path) -> None:
        resolved_destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, resolved_destination)

    @staticmethod
    def _validate_supported_filename(filename: str) -> None:
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("unsupported file type")

    @staticmethod
    def _safe_error(error: Exception) -> str:
        if isinstance(error, ValueError):
            return str(error)
        return type(error).__name__
