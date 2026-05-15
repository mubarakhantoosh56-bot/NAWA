"""Seed the Atlas Home Supplies demo tenant."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import asyncpg

from app.core.config import settings
from app.core.passwords import hash_password
from app.repositories.company_repository import CompanyRepository
from app.repositories.department_repository import DepartmentRepository
from app.services import file_ingestion_service as file_ingestion_module
from app.services.company_bootstrap_service import CompanyBootstrapService
from app.services.department_service import DepartmentService
from app.services.file_ingestion_service import FileIngestionService


BASE_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = BASE_DIR / "demo" / "atlas_home_supplies"
DEMO_FILES_DIR = DEMO_DIR / "files"
DEMO_COMPANY_SLUG = "atlas-home-supplies"
DEMO_COMPANY_NAME = "Atlas Home Supplies"
DEMO_OWNER_EMAIL = "owner@atlas-demo.local"
DEMO_OWNER_NAME = "Atlas Demo Owner"
DEMO_SESSION_ID = "atlas-demo-seed"

logger = logging.getLogger("aimx.demo_seed")


@dataclass(frozen=True)
class DemoDepartment:
    name: str
    slug: str
    department_type: str
    description: str
    filename: str | None = None


DEMO_DEPARTMENTS = (
    DemoDepartment(
        name="CEO",
        slug="ceo",
        department_type="custom",
        description="Company-wide executive AI for cross-department priorities.",
    ),
    DemoDepartment(
        name="Sales",
        slug="sales",
        department_type="sales_ai",
        description="Sales AI for pipeline, outreach, account plans, and conversion.",
        filename="sales_playbook.md",
    ),
    DemoDepartment(
        name="Finance",
        slug="finance",
        department_type="finance_ai",
        description="Finance AI for budgets, margins, pricing, and financial risk.",
        filename="finance_budget.md",
    ),
    DemoDepartment(
        name="Marketing",
        slug="marketing",
        department_type="marketing_ai",
        description="Marketing AI for campaigns, positioning, channels, and KPIs.",
        filename="marketing_campaign.md",
    ),
    DemoDepartment(
        name="Operations",
        slug="operations",
        department_type="operations_ai",
        description="Operations AI for SOPs, delivery constraints, and fulfillment risk.",
        filename="operations_sop.md",
    ),
)

COMPANY_FILES = ("company_profile.md", "growth_goals.md")

DEMO_FACTS = (
    ("company", "company_name", "Atlas Home Supplies", 100),
    ("company", "target_market", "Hotels, restaurants, serviced apartments, and small offices in Jordan", 95),
    ("company", "primary_market", "Amman hospitality and restaurant buyers", 95),
    ("goal", "goal", "Increase monthly B2B revenue by 25 percent within 90 days", 95),
    ("constraint", "marketing_budget", "Monthly marketing budget is capped at 4,000 JOD", 95),
    ("metric", "gross_margin_target", "Standard gross margin target is 28 percent", 95),
    ("constraint", "delivery_constraint", "Same-day delivery is reliable only inside central Amman", 90),
    ("company", "team_size", "42 employees", 90),
)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the AIMX Atlas Home Supplies demo tenant.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Soft-delete the existing demo tenant and seed it again.",
    )
    return parser.parse_args()


async def reset_demo_company(conn: asyncpg.Connection) -> None:
    company = await CompanyRepository(conn).get_by_slug(DEMO_COMPANY_SLUG)
    if company is None:
        return

    company_id = company["id"]
    logger.info("demo_reset_start company_slug=%s", DEMO_COMPANY_SLUG)

    async with conn.transaction():
        await _soft_delete_if_table_exists(
            conn,
            "file_chunk_embeddings",
            "company_id",
            company_id,
        )
        await _soft_delete_if_table_exists(conn, "file_chunks", "company_id", company_id)
        await _soft_delete_if_table_exists(conn, "files", "company_id", company_id)
        await _delete_memory_if_exists(conn, "memory_facts", company_id)
        await _delete_memory_if_exists(conn, "memory_events", company_id)
        await _soft_delete_if_table_exists(conn, "memberships", "company_id", company_id)
        await _soft_delete_if_table_exists(conn, "departments", "company_id", company_id)
        await _soft_delete_if_table_exists(conn, "roles", "company_id", company_id)
        await _soft_delete_if_table_exists(conn, "refresh_tokens", "company_id", company_id)
        await conn.execute(
            """
            UPDATE companies
            SET deleted_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
            """,
            company_id,
        )

    logger.info("demo_reset_complete company_slug=%s", DEMO_COMPANY_SLUG)


async def seed_demo() -> dict[str, object]:
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    password = os.getenv("DEMO_OWNER_PASSWORD", "").strip()
    if not password:
        raise RuntimeError("DEMO_OWNER_PASSWORD is required")

    conn = await asyncpg.connect(dsn=settings.DATABASE_URL, timeout=10)
    try:
        existing = await CompanyRepository(conn).get_by_slug(DEMO_COMPANY_SLUG)
        if existing is not None:
            raise RuntimeError("demo company already exists; rerun with --reset")

        bootstrap = CompanyBootstrapService(conn)
        result = await bootstrap.register_company_owner(
            company_slug=DEMO_COMPANY_SLUG,
            company_name=DEMO_COMPANY_NAME,
            owner_email=DEMO_OWNER_EMAIL,
            owner_full_name=DEMO_OWNER_NAME,
            owner_password_hash=hash_password(password),
            company_plan="demo",
            company_metadata={
                "demo": True,
                "industry": "Retail and light distribution",
                "market": "Jordan",
            },
        )

        company = result["company"]
        user = result["user"]
        await conn.execute(
            """
            UPDATE users
            SET password_hash = $1, updated_at = NOW()
            WHERE id = $2
            """,
            hash_password(password),
            user["id"],
        )
        departments = await _configure_demo_departments(
            conn=conn,
            company_id=company["id"],
            user_id=user["id"],
        )

        await _ensure_demo_memory_tables(conn)
        facts_seeded = await _seed_demo_facts(conn, company_id=company["id"])
        files_seeded = await _seed_demo_files(
            conn=conn,
            company_id=company["id"],
            user_id=user["id"],
            departments=departments,
        )

        logger.info(
            "demo_seed_complete company_slug=%s departments=%s facts=%s files=%s",
            DEMO_COMPANY_SLUG,
            len(departments),
            facts_seeded,
            files_seeded,
        )
        return {
            "company_id": company["id"],
            "user_id": user["id"],
            "departments": departments,
            "facts_seeded": facts_seeded,
            "files_seeded": files_seeded,
        }
    finally:
        await conn.close()


async def _configure_demo_departments(
    conn: asyncpg.Connection,
    company_id: UUID,
    user_id: UUID,
) -> dict[str, dict[str, object]]:
    department_service = DepartmentService(conn)
    department_repo = DepartmentRepository(conn)
    keep_slugs = {department.slug for department in DEMO_DEPARTMENTS}

    for department in await department_repo.list_by_company(company_id):
        slug = str(department["slug"])
        if slug not in keep_slugs:
            await department_repo.soft_delete_department(
                company_id=company_id,
                department_id=department["id"],
                deleted_by_user_id=user_id,
            )

    configured: dict[str, dict[str, object]] = {}
    for department in DEMO_DEPARTMENTS:
        existing = await department_repo.get_by_slug(company_id=company_id, slug=department.slug)
        if existing is None:
            existing = await department_service.create_department(
                company_id=company_id,
                name=department.name,
                department_type=department.department_type,
                description=department.description,
                ai_agent_enabled=True,
                ai_agent_config={"demo": True},
                created_by_user_id=user_id,
            )
        else:
            existing = await department_service.update_department(
                company_id=company_id,
                department_id=existing["id"],
                name=department.name,
                description=department.description,
                department_type=department.department_type,
                ai_agent_enabled=True,
                ai_agent_config={"demo": True},
                updated_by_user_id=user_id,
            ) or existing
        configured[department.slug] = existing

    return configured


async def _seed_demo_facts(conn: asyncpg.Connection, company_id: UUID) -> int:
    if not await _table_exists(conn, "memory_facts"):
        logger.info("demo_memory_facts_skipped reason=table_missing")
        return 0

    count = 0
    for fact_type, fact_key, fact_value, confidence in DEMO_FACTS:
        await conn.execute(
            """
            INSERT INTO public.memory_facts
                (company_id, session_id, fact_type, fact_key, fact_value, confidence)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(company_id),
            DEMO_SESSION_ID,
            fact_type,
            fact_key,
            fact_value,
            confidence,
        )
        count += 1
    return count


async def _seed_demo_files(
    conn: asyncpg.Connection,
    company_id: UUID,
    user_id: UUID,
    departments: dict[str, dict[str, object]],
) -> int:
    file_ingestion_module.store_chunk_embeddings = _skip_demo_embeddings
    service = FileIngestionService(conn)
    count = 0

    for filename in COMPANY_FILES:
        await _ingest_demo_file(
            service=service,
            company_id=company_id,
            user_id=user_id,
            filename=filename,
            department_id=None,
        )
        count += 1

    for department in DEMO_DEPARTMENTS:
        if department.filename is None:
            continue
        await _ingest_demo_file(
            service=service,
            company_id=company_id,
            user_id=user_id,
            filename=department.filename,
            department_id=departments[department.slug]["id"],
        )
        count += 1

    return count


async def _skip_demo_embeddings(**kwargs) -> int:
    return 0


async def _ensure_demo_memory_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.memory_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id TEXT NOT NULL,
            session_id TEXT NULL,
            event_type TEXT NOT NULL DEFAULT 'decision',
            user_message TEXT NULL,
            executive_summary TEXT NULL,
            logic_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            context JSONB NOT NULL DEFAULT '{}'::jsonb,
            tags TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
            idempotency_key TEXT UNIQUE NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.memory_facts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id TEXT NOT NULL,
            session_id TEXT NULL,
            fact_type TEXT NOT NULL DEFAULT 'other',
            fact_key TEXT NOT NULL,
            fact_value TEXT NOT NULL,
            confidence INTEGER NOT NULL DEFAULT 0,
            source_event_id TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT memory_facts_company_key_unique UNIQUE (company_id, fact_key)
        )
        """
    )


async def _ingest_demo_file(
    service: FileIngestionService,
    company_id: UUID,
    user_id: UUID,
    filename: str,
    department_id: UUID | None,
) -> None:
    path = DEMO_FILES_DIR / filename
    result = await service.ingest_file(
        company_id=company_id,
        uploaded_by_user_id=user_id,
        source_path=path,
        filename=filename,
        content_type=_content_type_for(path),
        department_id=department_id,
    )
    file_record = result["file"]
    if file_record.get("status") != "ready":
        raise RuntimeError(f"demo file ingestion failed: {filename}")


def _content_type_for(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "text/markdown"
    if path.suffix.lower() == ".csv":
        return "text/csv"
    if path.suffix.lower() == ".json":
        return "application/json"
    return "text/plain"


async def _table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    return bool(
        await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = $1
            )
            """,
            table_name,
        )
    )


async def _soft_delete_if_table_exists(
    conn: asyncpg.Connection,
    table_name: str,
    company_column: str,
    company_id: UUID,
) -> None:
    if not await _table_exists(conn, table_name):
        return
    await conn.execute(
        f"""
        UPDATE {table_name}
        SET deleted_at = NOW(), updated_at = NOW()
        WHERE {company_column} = $1 AND deleted_at IS NULL
        """,
        company_id,
    )


async def _delete_memory_if_exists(
    conn: asyncpg.Connection,
    table_name: str,
    company_id: UUID,
) -> None:
    if not await _table_exists(conn, table_name):
        return
    await conn.execute(
        f"""
        DELETE FROM public.{table_name}
        WHERE company_id = $1
        """,
        str(company_id),
    )


async def async_main() -> int:
    configure_logging()
    args = parse_args()
    conn: asyncpg.Connection | None = None

    try:
        if args.reset:
            if not settings.DATABASE_URL:
                raise RuntimeError("DATABASE_URL is not configured")
            conn = await asyncpg.connect(dsn=settings.DATABASE_URL, timeout=10)
            await reset_demo_company(conn)
            await conn.close()
            conn = None

        await seed_demo()
        return 0
    except Exception:
        logger.exception("demo_seed_failed")
        return 1
    finally:
        if conn is not None:
            await conn.close()


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
