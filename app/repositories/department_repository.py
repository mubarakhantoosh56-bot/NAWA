"""Department repository for SaaS foundation data access."""

import json
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class DepartmentRepository:
    """Database access for tenant-scoped department records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_department(
        self,
        company_id: UUID,
        name: str,
        slug: str,
        department_type: str,
        description: str | None = None,
        ai_agent_enabled: bool = False,
        ai_agent_config: dict[str, object] | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a tenant-scoped department and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO departments (
                company_id,
                name,
                slug,
                description,
                department_type,
                ai_agent_enabled,
                ai_agent_config,
                created_by_user_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
            RETURNING *
            """,
            company_id,
            name,
            slug,
            description,
            department_type,
            ai_agent_enabled,
            json.dumps(ai_agent_config or {}),
            created_by_user_id,
        )
        return self._row_to_dict(row)

    async def get_by_id(
        self,
        company_id: UUID,
        department_id: UUID,
    ) -> RowDict | None:
        """Return one active department by company and department ID."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM departments
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            department_id,
        )
        return self._optional_row_to_dict(row)

    async def get_by_slug(
        self,
        company_id: UUID,
        slug: str,
    ) -> RowDict | None:
        """Return one active department by company and slug."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM departments
            WHERE company_id = $1
              AND slug = $2
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            slug,
        )
        return self._optional_row_to_dict(row)

    async def list_by_company(self, company_id: UUID) -> list[RowDict]:
        """Return active departments for one tenant."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM departments
            WHERE company_id = $1
              AND deleted_at IS NULL
            ORDER BY name ASC
            """,
            company_id,
        )
        return [self._row_to_dict(row) for row in rows]

    async def slug_exists(self, company_id: UUID, slug: str) -> bool:
        """Return whether an active department slug exists in one tenant."""
        exists = await self.db.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM departments
                WHERE company_id = $1
                  AND slug = $2
                  AND deleted_at IS NULL
            )
            """,
            company_id,
            slug,
        )
        return bool(exists)

    async def update_department(
        self,
        company_id: UUID,
        department_id: UUID,
        name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        department_type: str | None = None,
        ai_agent_enabled: bool | None = None,
        ai_agent_config: dict[str, object] | None = None,
        updated_by_user_id: UUID | None = None,
    ) -> RowDict | None:
        """Update an active tenant department and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE departments
            SET
                name = COALESCE($3, name),
                slug = COALESCE($4, slug),
                description = COALESCE($5, description),
                department_type = COALESCE($6, department_type),
                ai_agent_enabled = COALESCE($7, ai_agent_enabled),
                ai_agent_config = COALESCE($8::jsonb, ai_agent_config),
                updated_by_user_id = $9,
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            RETURNING *
            """,
            company_id,
            department_id,
            name,
            slug,
            description,
            department_type,
            ai_agent_enabled,
            json.dumps(ai_agent_config) if ai_agent_config is not None else None,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def soft_delete_department(
        self,
        company_id: UUID,
        department_id: UUID,
        deleted_by_user_id: UUID,
    ) -> bool:
        """Soft-delete a tenant department and return whether a row was updated."""
        result = await self.db.execute(
            """
            UPDATE departments
            SET
                deleted_by_user_id = $3,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            """,
            company_id,
            department_id,
            deleted_by_user_id,
        )
        return result == "UPDATE 1"

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return DepartmentRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        result = dict(row)
        config = result.get("ai_agent_config")
        if isinstance(config, str):
            result["ai_agent_config"] = json.loads(config)
        return result
