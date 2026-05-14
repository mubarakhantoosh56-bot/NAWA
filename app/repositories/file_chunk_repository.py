"""File chunk repository for AIMX RAG foundation data access."""

import json
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class FileChunkRepository:
    """Database access for tenant-scoped file chunk records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_chunks(
        self,
        company_id: UUID,
        file_id: UUID,
        chunks: list[dict[str, object]],
        department_id: UUID | None = None,
    ) -> list[RowDict]:
        """Create file chunks for one tenant and return inserted rows."""
        rows = []
        for chunk in chunks:
            row = await self.db.fetchrow(
                """
                INSERT INTO file_chunks (
                    company_id,
                    file_id,
                    department_id,
                    chunk_index,
                    content,
                    token_count,
                    status,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                RETURNING *
                """,
                company_id,
                file_id,
                department_id,
                chunk["chunk_index"],
                chunk["content"],
                chunk.get("token_count"),
                chunk.get("status", "ready"),
                json.dumps(chunk.get("metadata") or {}),
            )
            rows.append(self._row_to_dict(row))

        return rows

    async def list_chunks_by_file(
        self,
        company_id: UUID,
        file_id: UUID,
    ) -> list[RowDict]:
        """Return active chunks for one tenant file."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM file_chunks
            WHERE company_id = $1
              AND file_id = $2
              AND deleted_at IS NULL
            ORDER BY chunk_index ASC
            """,
            company_id,
            file_id,
        )
        return [self._row_to_dict(row) for row in rows]

    async def count_chunks_by_file(
        self,
        company_id: UUID,
        file_id: UUID,
    ) -> int:
        """Return active chunk count for one tenant file."""
        count = await self.db.fetchval(
            """
            SELECT COUNT(*)
            FROM file_chunks
            WHERE company_id = $1
              AND file_id = $2
              AND deleted_at IS NULL
            """,
            company_id,
            file_id,
        )
        return int(count or 0)

    async def delete_chunks_for_file(
        self,
        company_id: UUID,
        file_id: UUID,
    ) -> int:
        """Soft-delete chunks for one tenant file and return affected count."""
        result = await self.db.execute(
            """
            UPDATE file_chunks
            SET
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE company_id = $1
              AND file_id = $2
              AND deleted_at IS NULL
            """,
            company_id,
            file_id,
        )
        return int(result.split(" ")[1])

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        result = dict(row)
        metadata = result.get("metadata")
        if isinstance(metadata, str):
            result["metadata"] = json.loads(metadata)
        return result
