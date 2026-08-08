"""Reset the local-dev password for owner@jannat-local.dev.

Usage:
    $env:JANNAT_NEW_PASSWORD="yournewpassword"
    python -m scripts.reset_jannat_password

Does not modify any other data. Safe to run multiple times.
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg

from app.core.config import settings
from app.core.passwords import hash_password

TARGET_EMAIL = "owner@jannat-local.dev"


async def main() -> None:
    password = os.environ.get("JANNAT_NEW_PASSWORD", "").strip()
    if not password:
        print("ERROR: JANNAT_NEW_PASSWORD environment variable is required and must not be empty.")
        sys.exit(1)

    if not settings.DATABASE_URL:
        print("ERROR: DATABASE_URL is not configured.")
        sys.exit(1)

    conn = await asyncpg.connect(dsn=settings.DATABASE_URL, timeout=10)
    try:
        user = await conn.fetchrow(
            "SELECT id, email FROM users WHERE email = $1 AND deleted_at IS NULL",
            TARGET_EMAIL,
        )
        if user is None:
            print(f"ERROR: User '{TARGET_EMAIL}' not found or is deleted. No changes made.")
            sys.exit(1)

        new_hash = hash_password(password)
        await conn.execute(
            "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2",
            new_hash,
            user["id"],
        )

        print(f"Password updated for {TARGET_EMAIL} (id: {user['id']}).")
    finally:
        await conn.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
