"""Files API routes for MVP RAG ingestion."""

import logging
import tempfile
from pathlib import Path
from uuid import UUID

import asyncpg
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.models.response import FileDetailResponse, FileListResponse, FileResponse
from app.services.file_ingestion_service import FileIngestionService

router = APIRouter(prefix="/files", tags=["Files"])
logger = logging.getLogger(__name__)


async def get_file_ingestion_service(request: Request) -> FileIngestionService:
    """Return a FileIngestionService backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return FileIngestionService(pool)


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    department_id: UUID | None = None,
    auth_context: AuthContext = Depends(require_permission("files.upload")),
    file_service: FileIngestionService = Depends(get_file_ingestion_service),
) -> FileResponse:
    """Upload and synchronously ingest one MVP text-like file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)

        try:
            result = await file_service.ingest_file(
                company_id=UUID(auth_context.company_id),
                uploaded_by_user_id=UUID(auth_context.user_id),
                source_path=temp_path,
                filename=file.filename or "upload",
                content_type=file.content_type or "",
                department_id=department_id,
            )
        finally:
            temp_path.unlink(missing_ok=True)

        file_record = result["file"]
        if file_record.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(result.get("error") or "file ingestion failed"),
            )
        return FileResponse.model_validate(file_record)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("File upload failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("File upload endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File service unavailable",
        ) from exc


@router.get("", response_model=FileListResponse)
async def list_files(
    department_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth_context: AuthContext = Depends(require_permission("files.read")),
    file_service: FileIngestionService = Depends(get_file_ingestion_service),
) -> FileListResponse:
    """List files for the authenticated tenant."""
    try:
        files = await file_service.list_files(
            company_id=UUID(auth_context.company_id),
            department_id=department_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        return FileListResponse.model_validate({"files": files})
    except ValueError as exc:
        logger.info("List files failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("List files endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File service unavailable",
        ) from exc


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file(
    file_id: UUID,
    auth_context: AuthContext = Depends(require_permission("files.read")),
    file_service: FileIngestionService = Depends(get_file_ingestion_service),
) -> FileDetailResponse:
    """Return safe file metadata for the authenticated tenant."""
    try:
        file_record = await file_service.get_file(
            company_id=UUID(auth_context.company_id),
            file_id=file_id,
        )
        if file_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        return FileDetailResponse.model_validate(file_record)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("Get file failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Get file endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File service unavailable",
        ) from exc
