"""PostgreSQL retrieval service for NAWA RAG."""

import json
from uuid import UUID

import asyncpg

from app.core.config import settings
from app.services.rag.embeddings import EmbeddingService, vector_to_pg_literal

RowDict = dict[str, object]

DEFAULT_LIMIT = 10
MAX_LIMIT = 100


class RetrievalService:
    """Retrieve tenant-scoped file chunks with keyword or semantic search."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the service with an asyncpg connection or pool."""
        self.db = db

    async def search_chunks(
        self,
        company_id: UUID,
        query: str,
        department_id: UUID | None = None,
        file_id: UUID | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[RowDict]:
        """Return active chunks matching a keyword query for one tenant."""
        if company_id is None:
            raise ValueError("company_id is required")

        normalized_query = query.strip()
        if not normalized_query:
            return []

        rows = await self.db.fetch(
            """
            SELECT c.*
            FROM file_chunks c
            INNER JOIN files f
                ON f.id = c.file_id
               AND f.company_id = c.company_id
               AND f.deleted_at IS NULL
            WHERE c.company_id = $1
              AND c.deleted_at IS NULL
              AND c.content ILIKE $2
              AND ($3::uuid IS NULL OR c.department_id = $3)
              AND ($4::uuid IS NULL OR c.file_id = $4)
            ORDER BY c.file_id ASC, c.chunk_index ASC
            LIMIT $5
            """,
            company_id,
            f"%{normalized_query}%",
            department_id,
            file_id,
            self._safe_limit(limit),
        )
        return [self._row_to_dict(row) for row in rows]

    async def search_semantic_chunks(
        self,
        company_id: UUID,
        query: str,
        department_id: UUID | None = None,
        file_id: UUID | None = None,
        limit: int = DEFAULT_LIMIT,
        embedding_service: EmbeddingService | None = None,
    ) -> list[RowDict]:
        """Return active chunks by pgvector cosine distance for one tenant."""
        if company_id is None:
            raise ValueError("company_id is required")

        normalized_query = query.strip()
        if not normalized_query:
            return []

        service = embedding_service or EmbeddingService()
        query_embedding = await service.embed_text(normalized_query)

        rows = await self.db.fetch(
            """
            SELECT
                c.*,
                e.embedding <=> $2::vector AS semantic_distance
            FROM file_chunk_embeddings e
            INNER JOIN file_chunks c
                ON c.id = e.chunk_id
               AND c.company_id = e.company_id
               AND c.deleted_at IS NULL
            INNER JOIN files f
                ON f.id = c.file_id
               AND f.company_id = c.company_id
               AND f.deleted_at IS NULL
            WHERE e.company_id = $1
              AND e.deleted_at IS NULL
              AND e.embedding_model = $3
              AND e.embedding_dimensions = $4
              AND ($5::uuid IS NULL OR e.department_id = $5)
              AND ($6::uuid IS NULL OR e.file_id = $6)
            ORDER BY e.embedding <=> $2::vector
            LIMIT $7
            """,
            company_id,
            vector_to_pg_literal(query_embedding),
            service.model,
            service.dimensions,
            department_id,
            file_id,
            self._safe_limit(limit),
        )
        return [self._row_to_dict(row) for row in rows]

    async def search_best_chunks(
        self,
        company_id: UUID,
        query: str,
        department_id: UUID | None = None,
        file_id: UUID | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> tuple[list[RowDict], str, bool]:
        """Use semantic retrieval when enabled, falling back to keyword search."""
        retrieval_mode = settings.RAG_RETRIEVAL_MODE.strip().lower()
        if retrieval_mode != "semantic":
            chunks = await self.search_chunks(
                company_id=company_id,
                query=query,
                department_id=department_id,
                file_id=file_id,
                limit=limit,
            )
            return chunks, "keyword_ilike", False

        try:
            semantic_chunks = await self.search_semantic_chunks(
                company_id=company_id,
                query=query,
                department_id=department_id,
                file_id=file_id,
                limit=limit,
            )
            if semantic_chunks:
                return semantic_chunks, "semantic_pgvector", False
        except Exception:
            keyword_chunks = await self.search_chunks(
                company_id=company_id,
                query=query,
                department_id=department_id,
                file_id=file_id,
                limit=limit,
            )
            return keyword_chunks, "keyword_ilike", True

        keyword_chunks = await self.search_chunks(
            company_id=company_id,
            query=query,
            department_id=department_id,
            file_id=file_id,
            limit=limit,
        )
        return keyword_chunks, "keyword_ilike", True

    @staticmethod
    def _safe_limit(limit: int) -> int:
        """Clamp caller-provided limits to a small MVP-safe range."""
        return max(1, min(int(limit), MAX_LIMIT))

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        result = dict(row)
        metadata = result.get("metadata")
        if isinstance(metadata, str):
            result["metadata"] = json.loads(metadata)
        return result
