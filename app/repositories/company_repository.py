"""Company repository for SaaS foundation data access."""

import json
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class CompanyRepository:
    """Database access for tenant company records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_company(
        self,
        slug: str,
        name: str,
        status: str = "active",
        plan: str = "mvp",
        metadata: dict[str, object] | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a company and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO companies (
                slug,
                name,
                status,
                plan,
                metadata,
                created_by_user_id
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6)
            RETURNING *
            """,
            slug,
            name,
            status,
            plan,
            json.dumps(metadata or {}),
            created_by_user_id,
        )
        return self._row_to_dict(row)

    async def get_by_id(self, company_id: UUID) -> RowDict | None:
        """Return one active company by ID."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM companies
            WHERE id = $1
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
        )
        return self._optional_row_to_dict(row)

    async def get_by_slug(self, slug: str) -> RowDict | None:
        """Return one active company by slug."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM companies
            WHERE slug = $1
              AND deleted_at IS NULL
            LIMIT 1
            """,
            slug,
        )
        return self._optional_row_to_dict(row)

    async def slug_exists(self, slug: str) -> bool:
        """Return whether an active company slug already exists."""
        exists = await self.db.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM companies
                WHERE slug = $1
                  AND deleted_at IS NULL
            )
            """,
            slug,
        )
        return bool(exists)

    async def update_company(
        self,
        company_id: UUID,
        name: str | None = None,
        status: str | None = None,
        plan: str | None = None,
        metadata: dict[str, object] | None = None,
        updated_by_user_id: UUID | None = None,
    ) -> RowDict | None:
        """Update editable company fields and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE companies
            SET
                name = COALESCE($2, name),
                status = COALESCE($3, status),
                plan = COALESCE($4, plan),
                metadata = COALESCE($5::jsonb, metadata),
                updated_by_user_id = $6,
                updated_at = NOW()
            WHERE id = $1
              AND deleted_at IS NULL
            RETURNING *
            """,
            company_id,
            name,
            status,
            plan,
            json.dumps(metadata) if metadata is not None else None,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def soft_delete_company(
        self,
        company_id: UUID,
        deleted_by_user_id: UUID | None = None,
    ) -> bool:
        """Soft-delete a company and return whether a row was updated."""
        result = await self.db.execute(
            """
            UPDATE companies
            SET
                deleted_by_user_id = $2,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
              AND deleted_at IS NULL
            """,
            company_id,
            deleted_by_user_id,
        )
        return result == "UPDATE 1"

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return CompanyRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        result = dict(row)
        metadata = result.get("metadata")
        if isinstance(metadata, str):
            result["metadata"] = json.loads(metadata)
        return result
