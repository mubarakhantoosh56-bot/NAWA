"""User repository for SaaS foundation data access."""

from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class UserRepository:
    """Database access for global user records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_user(
        self,
        email: str,
        full_name: str,
        status: str = "active",
        password_hash: str | None = None,
        auth_provider: str = "local",
        external_subject: str | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a user and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO users (
                email,
                full_name,
                status,
                password_hash,
                auth_provider,
                external_subject,
                created_by_user_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            email,
            full_name,
            status,
            password_hash,
            auth_provider,
            external_subject,
            created_by_user_id,
        )
        return self._row_to_dict(row)

    async def get_by_id(self, user_id: UUID) -> RowDict | None:
        """Return one active user by ID."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM users
            WHERE id = $1
              AND deleted_at IS NULL
            LIMIT 1
            """,
            user_id,
        )
        return self._optional_row_to_dict(row)

    async def get_by_email(self, email: str) -> RowDict | None:
        """Return one active user by email."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM users
            WHERE email = $1
              AND deleted_at IS NULL
            LIMIT 1
            """,
            email,
        )
        return self._optional_row_to_dict(row)

    async def email_exists(self, email: str) -> bool:
        """Return whether an active user email already exists."""
        exists = await self.db.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM users
                WHERE email = $1
                  AND deleted_at IS NULL
            )
            """,
            email,
        )
        return bool(exists)

    async def update_user(
        self,
        user_id: UUID,
        full_name: str | None = None,
        status: str | None = None,
        password_hash: str | None = None,
        auth_provider: str | None = None,
        external_subject: str | None = None,
        updated_by_user_id: UUID | None = None,
    ) -> RowDict | None:
        """Update editable user fields and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE users
            SET
                full_name = COALESCE($2, full_name),
                status = COALESCE($3, status),
                password_hash = COALESCE($4, password_hash),
                auth_provider = COALESCE($5, auth_provider),
                external_subject = COALESCE($6, external_subject),
                updated_by_user_id = $7,
                updated_at = NOW()
            WHERE id = $1
              AND deleted_at IS NULL
            RETURNING *
            """,
            user_id,
            full_name,
            status,
            password_hash,
            auth_provider,
            external_subject,
            updated_by_user_id,
        )
        return self._optional_row_to_dict(row)

    async def record_login(self, user_id: UUID) -> RowDict | None:
        """Record a user's last login time and return the updated row."""
        row = await self.db.fetchrow(
            """
            UPDATE users
            SET
                last_login_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
              AND deleted_at IS NULL
            RETURNING *
            """,
            user_id,
        )
        return self._optional_row_to_dict(row)

    async def soft_delete_user(
        self,
        user_id: UUID,
        deleted_by_user_id: UUID | None = None,
    ) -> bool:
        """Soft-delete a user and return whether a row was updated."""
        result = await self.db.execute(
            """
            UPDATE users
            SET
                deleted_by_user_id = $2,
                deleted_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
              AND deleted_at IS NULL
            """,
            user_id,
            deleted_by_user_id,
        )
        return result == "UPDATE 1"

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return UserRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        return dict(row)
