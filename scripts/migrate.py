import asyncio
import hashlib
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import asyncpg

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = BASE_DIR / "migrations"
MIGRATION_FILENAME_PATTERN = re.compile(r"^(?P<version>\d{3})_[a-z0-9_]+\.sql$")

logger = logging.getLogger("aimx.migrations")


@dataclass(frozen=True)
class MigrationFile:
    """SQL migration discovered on disk."""

    version: str
    filename: str
    path: Path
    checksum: str
    sql: str


@dataclass(frozen=True)
class AppliedMigration:
    """Migration record loaded from schema_migrations."""

    version: str
    filename: str
    checksum: str
    applied_at: datetime


def configure_logging() -> None:
    """Configure safe console logging for migration execution."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )


def calculate_checksum(sql: str) -> str:
    """Calculate a SHA-256 checksum for a SQL migration body."""

    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def parse_migration_filename(path: Path) -> str:
    """Validate a migration filename and return its version prefix."""

    match = MIGRATION_FILENAME_PATTERN.match(path.name)
    if match is None:
        raise ValueError(
            "Invalid migration filename. Expected format like "
            f"'001_example_name.sql': {path.name}"
        )

    return match.group("version")


def discover_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[MigrationFile]:
    """Read and validate migration files from disk in filename order."""

    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    migration_paths = sorted(migrations_dir.glob("*.sql"), key=lambda item: item.name)
    if not migration_paths:
        logger.info("migration_no_files directory=%s", migrations_dir)
        return []

    seen_versions: set[str] = set()
    migrations: list[MigrationFile] = []

    for path in migration_paths:
        version = parse_migration_filename(path)
        if version in seen_versions:
            raise ValueError(f"Duplicate migration version found: {version}")

        sql = path.read_text(encoding="utf-8")
        checksum = calculate_checksum(sql)
        migrations.append(
            MigrationFile(
                version=version,
                filename=path.name,
                path=path,
                checksum=checksum,
                sql=sql,
            )
        )
        seen_versions.add(version)

    return migrations


async def ensure_schema_migrations(conn: asyncpg.Connection) -> None:
    """Create the schema_migrations tracking table if it does not exist."""

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


async def get_applied_migrations(
    conn: asyncpg.Connection,
) -> dict[str, AppliedMigration]:
    """Load migration records already applied to the database."""

    rows = await conn.fetch(
        """
        SELECT version, filename, checksum, applied_at
        FROM schema_migrations
        ORDER BY version ASC
        """
    )

    return {
        row["version"]: AppliedMigration(
            version=row["version"],
            filename=row["filename"],
            checksum=row["checksum"],
            applied_at=row["applied_at"],
        )
        for row in rows
    }


def validate_applied_migration(
    migration: MigrationFile,
    applied: AppliedMigration | None,
) -> bool:
    """
    Validate applied migration state.

    Returns True when the migration should be skipped.
    """

    if applied is None:
        return False

    if applied.checksum != migration.checksum:
        raise RuntimeError(
            "Checksum mismatch for applied migration "
            f"version={migration.version} filename={migration.filename}"
        )

    logger.info(
        "migration_skip version=%s filename=%s reason=already_applied",
        migration.version,
        migration.filename,
    )
    return True


async def apply_migration(
    conn: asyncpg.Connection,
    migration: MigrationFile,
) -> None:
    """Execute one migration and record it in one transaction."""

    logger.info(
        "migration_start version=%s filename=%s",
        migration.version,
        migration.filename,
    )

    async with conn.transaction():
        await conn.execute(migration.sql)
        await conn.execute(
            """
            INSERT INTO schema_migrations (version, filename, checksum)
            VALUES ($1, $2, $3)
            """,
            migration.version,
            migration.filename,
            migration.checksum,
        )

    logger.info(
        "migration_applied version=%s filename=%s",
        migration.version,
        migration.filename,
    )


async def run_migrations() -> None:
    """Run pending migrations against DATABASE_URL."""

    database_url = settings.DATABASE_URL
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    migrations = discover_migrations()
    if not migrations:
        return

    conn: asyncpg.Connection | None = None
    try:
        conn = await asyncpg.connect(dsn=database_url, timeout=10)
        await ensure_schema_migrations(conn)
        applied_migrations = await get_applied_migrations(conn)

        for migration in migrations:
            applied = applied_migrations.get(migration.version)
            should_skip = validate_applied_migration(migration, applied)
            if should_skip:
                continue

            await apply_migration(conn, migration)

    finally:
        if conn is not None:
            await conn.close()
            logger.info("migration_connection_closed")


async def async_main() -> int:
    """Async CLI entrypoint."""

    configure_logging()

    try:
        await run_migrations()
        logger.info("migration_complete")
        return 0
    except Exception:
        logger.exception("migration_failed")
        return 1


def main() -> None:
    """CLI entrypoint."""

    exit_code = asyncio.run(async_main())
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
