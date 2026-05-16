"""Refresh token repository for NAWA auth runtime."""

from datetime import datetime
from uuid import UUID

import asyncpg

RowDict = dict[str, object]


class RefreshTokenRepository:
    """Database access for tenant-scoped refresh token records."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_refresh_token(
        self,
        company_id: UUID,
        user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RowDict:
        """Store a hashed refresh token and return the inserted row."""
        row = await self.db.fetchrow(
            """
            INSERT INTO refresh_tokens (
                company_id,
                user_id,
                token_hash,
                family_id,
                expires_at,
                ip_address,
                user_agent
            )
            VALUES ($1, $2, $3, $4, $5, $6::inet, $7)
            RETURNING *
            """,
            company_id,
            user_id,
            token_hash,
            family_id,
            expires_at,
            ip_address,
            user_agent,
        )
        return self._row_to_dict(row)

    async def get_active_by_hash(self, token_hash: str) -> RowDict | None:
        """Return one active refresh token row by stored token hash."""
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM refresh_tokens
            WHERE token_hash = $1
              AND revoked_at IS NULL
              AND deleted_at IS NULL
              AND expires_at > NOW()
            LIMIT 1
            """,
            token_hash,
        )
        return self._optional_row_to_dict(row)

    async def revoke_token(
        self,
        token_id: UUID,
        replaced_by_token_id: UUID | None = None,
    ) -> bool:
        """Revoke one refresh token and return whether a row was updated."""
        result = await self.db.execute(
            """
            UPDATE refresh_tokens
            SET
                revoked_at = NOW(),
                replaced_by_token_id = $2,
                updated_at = NOW()
            WHERE id = $1
              AND revoked_at IS NULL
              AND deleted_at IS NULL
            """,
            token_id,
            replaced_by_token_id,
        )
        return result == "UPDATE 1"

    async def revoke_family(
        self,
        company_id: UUID,
        user_id: UUID,
        family_id: UUID,
    ) -> int:
        """Revoke all active refresh tokens in one tenant-scoped token family."""
        result = await self.db.execute(
            """
            UPDATE refresh_tokens
            SET
                revoked_at = NOW(),
                updated_at = NOW()
            WHERE company_id = $1
              AND user_id = $2
              AND family_id = $3
              AND revoked_at IS NULL
              AND deleted_at IS NULL
            """,
            company_id,
            user_id,
            family_id,
        )
        return int(result.split(" ")[1])

    @staticmethod
    def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
        if row is None:
            return None
        return RefreshTokenRepository._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: asyncpg.Record) -> RowDict:
        return dict(row)
