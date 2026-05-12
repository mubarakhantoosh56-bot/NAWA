"""Role repository for SaaS foundation data access."""

import json
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class RoleRepository:
    """Database access for system and company-scoped role records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def get_system_role_by_slug(self, slug: str) -> RowDict | None:
        """Return one active system role template by slug."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM roles
            WHERE company_id IS NULL
              AND is_system_role = TRUE
              AND slug = $1
              AND deleted_at IS NULL
            LIMIT 1
            """,
            slug,
        )
        return self._optional_row_to_dict(row)

    async def list_system_roles(self) -> list[RowDict]:
        """Return all active system role templates."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM roles
            WHERE company_id IS NULL
              AND is_system_role = TRUE
              AND deleted_at IS NULL
            ORDER BY name ASC
            """
        )
        return [self._row_to_dict(row) for row in rows]

    async def create_company_role(
        self,
        company_id: UUID,
        name: str,
        slug: str,
        description: str | None = None,
        permissions: list[str] | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a tenant-scoped role and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO roles (
                company_id,
                name,
                slug,
                description,
                permissions,
                is_system_role,
                created_by_user_id
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, FALSE, $6)
            RETURNING *
            """,
            company_id,
            name,
            slug,
            description,
            json.dumps(permissions or []),
            created_by_user_id,
        )
        return self._row_to_dict(row)

    async def get_company_role_by_id(
        self,
        company_id: UUID,
        role_id: UUID,
    ) -> RowDict | None:
        """Return one active tenant role by company and role ID."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM roles
            WHERE company_id = $1
              AND id = $2
              AND is_system_role = FALSE
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            role_id,
        )
        return self._optional_row_to_dict(row)

    async def get_company_role_by_slug(
        self,
        company_id: UUID,
        slug: str,
    ) -> RowDict | None:
        """Return one active tenant role by company and slug."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM roles
            WHERE company_id = $1
              AND slug = $2
              AND is_system_role = FALSE
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            slug,
        )
        return self._optional_row_to_dict(row)

    async def list_company_roles(self, company_id: UUID) -> list[RowDict]:
        """Return active tenant roles for one company."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM roles
            WHERE company_id = $1
              AND is_system_role = FALSE
              AND deleted_at IS NULL
            ORDER BY name ASC
            """,
            company_id,
        )
        return [self._row_to_dict(row) for row in rows]

    async def update_company_role(
        self,
        company_id: UUID,
        role_id: UUID,
        name: str | None = None,
        description: str | None = None,
        permissions: list[str] | None = None,
        updated_by_user_id: UUID | None = None,
    ) -> RowDict | None:
        """Update an active tenant role and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE roles
            SET
                name = COALESCE($3, name),
                description = COALESCE($4, description),
                permissions = COALESCE($5::jsonb, permissions),
                updated_by_user_id = $6,
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND is_system_role = FALSE
              AND deleted_at IS NULL
            RETURNING *
            """,
            company_id,
            role_id,
            name,
            description,
            json.dumps(permissions) if permissions is not None else None,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def soft_delete_company_role(
        self,
        company_id: UUID,
        role_id: UUID,
        deleted_by_user_id: UUID,
    ) -> bool:
        """Soft-delete a tenant role and return whether a row was updated."""
        result = await self.db.execute(
            """
            UPDATE roles
            SET
                deleted_by_user_id = $3,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND is_system_role = FALSE
              AND deleted_at IS NULL
            """,
            company_id,
            role_id,
            deleted_by_user_id,
        )
        return result == "UPDATE 1"

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return RoleRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        result = dict(row)
        permissions = result.get("permissions")
        if isinstance(permissions, str):
            result["permissions"] = json.loads(permissions)
        return result
