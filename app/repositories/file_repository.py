"""File repository for AIMX RAG foundation data access."""

import json
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class FileRepository:
    """Database access for tenant-scoped uploaded file records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_file(
        self,
        company_id: UUID,
        uploaded_by_user_id: UUID,
        filename: str,
        content_type: str,
        file_size_bytes: int,
        storage_path: str,
        department_id: UUID | None = None,
        status: str = "uploaded",
        metadata: dict[str, object] | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a tenant-scoped file record and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO files (
                company_id,
                department_id,
                uploaded_by_user_id,
                filename,
                content_type,
                file_size_bytes,
                storage_path,
                status,
                metadata,
                created_by_user_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
            RETURNING *
            """,
            company_id,
            department_id,
            uploaded_by_user_id,
            filename,
            content_type,
            file_size_bytes,
            storage_path,
            status,
            json.dumps(metadata or {}),
            created_by_user_id,
        )
        return self._row_to_dict(row)

    async def get_file_by_id(
        self,
        company_id: UUID,
        file_id: UUID,
    ) -> RowDict | None:
        """Return one active file by company and file ID."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM files
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            file_id,
        )
        return self._optional_row_to_dict(row)

    async def list_files(
        self,
        company_id: UUID,
        department_id: UUID | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RowDict]:
        """Return active files for one tenant, optionally filtered."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM files
            WHERE company_id = $1
              AND ($2::uuid IS NULL OR department_id = $2)
              AND ($3::text IS NULL OR status = $3)
              AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $4 OFFSET $5
            """,
            company_id,
            department_id,
            status,
            limit,
            offset,
        )
        return [self._row_to_dict(row) for row in rows]

    async def update_file_status(
        self,
        company_id: UUID,
        file_id: UUID,
        status: str,
        metadata: dict[str, object] | None = None,
        updated_by_user_id: UUID | None = None,
    ) -> RowDict | None:
        """Update a file status for one tenant and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE files
            SET
                status = $3,
                metadata = COALESCE($4::jsonb, metadata),
                updated_by_user_id = $5,
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            RETURNING *
            """,
            company_id,
            file_id,
            status,
            json.dumps(metadata) if metadata is not None else None,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def soft_delete_file(
        self,
        company_id: UUID,
        file_id: UUID,
        deleted_by_user_id: UUID,
    ) -> bool:
        """Soft-delete a file for one tenant and return whether it changed."""
        result = await self.db.execute(
            """
            UPDATE files
            SET
                status = 'deleted',
                deleted_by_user_id = $3,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            """,
            company_id,
            file_id,
            deleted_by_user_id,
        )
        return result == "UPDATE 1"

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return FileRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        result = dict(row)
        metadata = result.get("metadata")
        if isinstance(metadata, str):
            result["metadata"] = json.loads(metadata)
        return result
