"""Membership repository for SaaS foundation data access."""

from datetime import datetime
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class MembershipRepository:
    """Database access for tenant-scoped membership records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_membership(
        self,
        company_id: UUID,
        user_id: UUID,
        role_id: UUID,
        department_id: UUID | None = None,
        status: str = "active",
        invited_by_user_id: UUID | None = None,
        invited_at: datetime | None = None,
        accepted_at: datetime | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a tenant-scoped membership and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO memberships (
                company_id,
                user_id,
                role_id,
                department_id,
                status,
                invited_by_user_id,
                invited_at,
                accepted_at,
                created_by_user_id
            )
            SELECT
                $1,
                $2,
                roles.id,
                $4,
                $5,
                $6,
                $7,
                $8,
                $9
            FROM roles
            WHERE roles.id = $3
              AND roles.deleted_at IS NULL
              AND (
                  roles.company_id = $1
                  OR (
                      roles.company_id IS NULL
                      AND roles.is_system_role = TRUE
                  )
              )
            RETURNING *
            """,
            company_id,
            user_id,
            role_id,
            department_id,
            status,
            invited_by_user_id,
            invited_at,
            accepted_at,
            created_by_user_id,
        )
        if row is None:
            raise ValueError("role_id is not valid for company membership")
        return self._row_to_dict(row)

    async def get_by_id(
        self,
        company_id: UUID,
        membership_id: UUID,
    ) -> RowDict | None:
        """Return one active membership by company and membership ID."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM memberships
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            membership_id,
        )
        return self._optional_row_to_dict(row)

    async def get_by_user_and_company(
        self,
        company_id: UUID,
        user_id: UUID,
    ) -> RowDict | None:
        """Return a user's company-level active membership in one tenant."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM memberships
            WHERE company_id = $1
              AND user_id = $2
              AND department_id IS NULL
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            user_id,
        )
        return self._optional_row_to_dict(row)

    async def get_active_membership(
        self,
        company_id: UUID,
        user_id: UUID,
    ) -> RowDict | None:
        """Return a user's active tenant membership for authorization checks."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM memberships
            WHERE company_id = $1
              AND user_id = $2
              AND status = 'active'
              AND deleted_at IS NULL
            ORDER BY department_id NULLS FIRST, created_at DESC
            LIMIT 1
            """,
            company_id,
            user_id,
        )
        return self._optional_row_to_dict(row)

    async def get_by_user_and_department(
        self,
        company_id: UUID,
        user_id: UUID,
        department_id: UUID,
    ) -> RowDict | None:
        """Return a user's department-level active membership in one tenant."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM memberships
            WHERE company_id = $1
              AND user_id = $2
              AND department_id = $3
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            user_id,
            department_id,
        )
        return self._optional_row_to_dict(row)

    async def list_by_company(
        self,
        company_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RowDict]:
        """Return active memberships for one tenant."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM memberships
            WHERE company_id = $1
              AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            company_id,
            limit,
            offset,
        )
        return [self._row_to_dict(row) for row in rows]

    async def list_active_company_members(
        self,
        company_id: UUID,
    ) -> list[RowDict]:
        """Return one row per distinct user with at least one ACTIVE,
        non-deleted membership in this company (M9 Slice 3 - Action
        assignee selector source, Founder-approved completion pass).

        Company scope must always come from the caller's JWT-derived
        AuthContext, never from client input. Deduplicates a user holding
        more than one active membership (e.g. company-wide plus a
        department-scoped row) to exactly one result row. Ordered for a
        selector: by display name, then email, then id."""
        rows = await self.db.fetch(
            """
            SELECT DISTINCT ON (users.id)
                users.id,
                users.full_name,
                users.email
            FROM memberships
            JOIN users ON users.id = memberships.user_id
            WHERE memberships.company_id = $1
              AND memberships.status = 'active'
              AND memberships.deleted_at IS NULL
              AND users.deleted_at IS NULL
            ORDER BY users.id, users.full_name, users.email
            """,
            company_id,
        )
        members = [self._row_to_dict(row) for row in rows]
        members.sort(key=lambda member: (str(member["full_name"]), str(member["email"]), str(member["id"])))
        return members

    async def list_auth_memberships_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
    ) -> list[RowDict]:
        """Auth/bootstrap only. Do not use for tenant-scoped API responses."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM memberships
            WHERE user_id = $1
              AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return [self._row_to_dict(row) for row in rows]

    async def update_membership_role(
        self,
        company_id: UUID,
        membership_id: UUID,
        role_id: UUID,
        updated_by_user_id: UUID,
    ) -> RowDict | None:
        """Update a tenant membership role and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE memberships
            SET
                role_id = $3,
                updated_by_user_id = $4,
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            RETURNING *
            """,
            company_id,
            membership_id,
            role_id,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def update_membership_status(
        self,
        company_id: UUID,
        membership_id: UUID,
        status: str,
        updated_by_user_id: UUID,
    ) -> RowDict | None:
        """Update a tenant membership status and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE memberships
            SET
                status = $3,
                updated_by_user_id = $4,
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            RETURNING *
            """,
            company_id,
            membership_id,
            status,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def soft_delete_membership(
        self,
        company_id: UUID,
        membership_id: UUID,
        deleted_by_user_id: UUID,
    ) -> bool:
        """Soft-delete a tenant membership and return whether a row was updated."""
        result = await self.db.execute(
            """
            UPDATE memberships
            SET
                deleted_by_user_id = $3,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE company_id = $1
              AND id = $2
              AND deleted_at IS NULL
            """,
            company_id,
            membership_id,
            deleted_by_user_id,
        )
        return result == "UPDATE 1"

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return MembershipRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        return dict(row)
