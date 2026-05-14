"""Keyword-only PostgreSQL retrieval service for MVP RAG."""

import json
from uuid import UUID

import asyncpg

RowDict = dict[str, object]

DEFAULT_LIMIT = 10
MAX_LIMIT = 100


class RetrievalService:
    """Retrieve tenant-scoped file chunks with simple PostgreSQL keyword search."""

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

