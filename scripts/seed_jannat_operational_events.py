"""Seed Jannat Al-Firdaws operational reference events."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import asyncpg

from app.core.config import settings


logger = logging.getLogger("nawa.jannat_operational_seed")
JANNAAT_COMPANY_NAME = "Jannat Al-Firdaws"
JANNAAT_COMPANY_SLUGS = ("jannat-al-firdaws", "jannat-alfirdaws")
SEED_SOURCE = "jannat_operational_reference"


@dataclass(frozen=True)
class ReferenceEvent:
    title: str
    category: str
    priority: str
    event_type: str
    summary: str
    days_ago: int
    hours_offset: int
    department_slugs: tuple[str, ...]
    payload: dict[str, object]


REFERENCE_EVENTS = (
    ReferenceEvent(
        title="Production Delay",
        category="production_delay",
        priority="high",
        event_type="operational.dairtna.production_delay",
        summary="Reference seed: poultry production cycle reported a delayed handoff.",
        days_ago=1,
        hours_offset=2,
        department_slugs=("production", "dairtna-poultry"),
        payload={"division": "Dairtna Poultry", "signal": "production_delay"},
    ),
    ReferenceEvent(
        title="Feed Shortage",
        category="feed_shortage",
        priority="high",
        event_type="operational.dairtna.feed_shortage",
        summary="Reference seed: feed availability pressure reported for poultry operations.",
        days_ago=1,
        hours_offset=4,
        department_slugs=("procurement", "warehouse", "dairtna-poultry"),
        payload={"division": "Dairtna Poultry", "signal": "feed_shortage"},
    ),
    ReferenceEvent(
        title="High Mortality",
        category="mortality",
        priority="critical",
        event_type="operational.dairtna.mortality",
        summary="Reference seed: elevated poultry mortality signal for review.",
        days_ago=2,
        hours_offset=1,
        department_slugs=("veterinary", "production", "dairtna-poultry"),
        payload={"division": "Dairtna Poultry", "signal": "mortality"},
    ),
    ReferenceEvent(
        title="Employee Absence",
        category="employee_absence",
        priority="watch",
        event_type="operational.shared.hr_absence",
        summary="Reference seed: staffing absence pressure affecting operating coverage.",
        days_ago=5,
        hours_offset=3,
        department_slugs=("hr", "shared-corporate"),
        payload={"division": "Shared Corporate Departments", "signal": "employee_absence"},
    ),
    ReferenceEvent(
        title="Medicine Delay",
        category="medicine_delay",
        priority="high",
        event_type="operational.dairtna.medicine_delay",
        summary="Reference seed: veterinary medicine procurement delay reported.",
        days_ago=2,
        hours_offset=5,
        department_slugs=("veterinary", "procurement", "dairtna-poultry"),
        payload={"division": "Dairtna Poultry", "signal": "medicine_delay"},
    ),
    ReferenceEvent(
        title="Low Egg Production",
        category="production_delay",
        priority="high",
        event_type="operational.dairtna.production_delay",
        summary="Reference seed: egg production below operating expectation.",
        days_ago=1,
        hours_offset=6,
        department_slugs=("production", "dairtna-poultry"),
        payload={"division": "Dairtna Poultry", "signal": "low_egg_production"},
    ),
    ReferenceEvent(
        title="Distribution Delay",
        category="distribution_delay",
        priority="high",
        event_type="operational.caesar.distribution_delay",
        summary="Reference seed: beverage distribution dispatch delay reported.",
        days_ago=8,
        hours_offset=2,
        department_slugs=("distribution", "sales", "caesar-beverage"),
        payload={"division": "Caesar Beverage", "signal": "distribution_delay"},
    ),
    ReferenceEvent(
        title="Customer Complaint",
        category="customer_complaint",
        priority="watch",
        event_type="operational.caesar.customer_complaint",
        summary="Reference seed: customer complaint connected to fulfillment timing.",
        days_ago=9,
        hours_offset=4,
        department_slugs=("sales", "customer-service", "caesar-beverage"),
        payload={"division": "Caesar Beverage", "signal": "customer_complaint"},
    ),
)


def configure_logging() -> None:
    """Configure safe console logging for seed execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for Jannat reference event seeding."""
    parser = argparse.ArgumentParser(
        description="Seed realistic Jannat Al-Firdaws operational reference events.",
    )
    parser.add_argument(
        "--company-id",
        help="Existing Jannat company UUID. Overrides lookup by env, slug, or name.",
    )
    return parser.parse_args()


async def seed_reference_events(company_id_arg: str | None = None) -> dict[str, object]:
    """Seed Jannat reference operational events for an existing company."""
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    conn = await asyncpg.connect(dsn=settings.DATABASE_URL, timeout=10)
    try:
        company = await _resolve_company(conn, company_id_arg)
        if company is None:
            raise RuntimeError(
                "Jannat Al-Firdaws company not found. Provide --company-id or "
                "JANNAT_COMPANY_ID for an existing company."
            )

        company_id = company["id"]
        user_id = await _resolve_seed_user_id(conn, company_id)
        departments = await _load_departments(conn, company_id)
        seeded = 0
        skipped = 0

        for event in REFERENCE_EVENTS:
            source_ref = f"{SEED_SOURCE}:{event.event_type}:{event.title.lower().replace(' ', '-')}"
            if await _event_exists(conn, company_id, source_ref):
                skipped += 1
                continue

            event_timestamp = datetime.now(timezone.utc) - timedelta(
                days=event.days_ago,
                hours=event.hours_offset,
            )
            department_id = _resolve_department_id(departments, event.department_slugs)
            await conn.execute(
                """
                INSERT INTO operational_events (
                    company_id,
                    department_id,
                    created_by_user_id,
                    event_type,
                    category,
                    priority,
                    title,
                    summary,
                    event_timestamp,
                    source_type,
                    source_ref,
                    payload,
                    metadata
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, 'reference_seed', $10, $11::jsonb, $12::jsonb
                )
                """,
                company_id,
                department_id,
                user_id,
                event.event_type,
                event.category,
                event.priority,
                event.title,
                event.summary,
                event_timestamp,
                source_ref,
                json.dumps(event.payload),
                json.dumps(
                    {
                        "reference_seed": True,
                        "seed_source": SEED_SOURCE,
                        "verified_historical_data": False,
                    }
                ),
            )
            seeded += 1

        logger.info(
            "jannat_reference_seed_complete company_id=%s seeded=%s skipped=%s",
            company_id,
            seeded,
            skipped,
        )
        return {"company_id": company_id, "seeded": seeded, "skipped": skipped}
    finally:
        await conn.close()


async def _resolve_company(
    conn: asyncpg.Connection,
    company_id_arg: str | None,
) -> asyncpg.Record | None:
    company_id_value = (company_id_arg or os.getenv("JANNAT_COMPANY_ID", "")).strip()
    if company_id_value:
        return await conn.fetchrow(
            """
            SELECT *
            FROM companies
            WHERE id = $1
              AND deleted_at IS NULL
            LIMIT 1
            """,
            UUID(company_id_value),
        )

    row = await conn.fetchrow(
        """
        SELECT *
        FROM companies
        WHERE slug = ANY($1::text[])
          AND deleted_at IS NULL
        ORDER BY created_at ASC
        LIMIT 1
        """,
        list(JANNAAT_COMPANY_SLUGS),
    )
    if row is not None:
        return row

    return await conn.fetchrow(
        """
        SELECT *
        FROM companies
        WHERE LOWER(name) = LOWER($1)
          AND deleted_at IS NULL
        ORDER BY created_at ASC
        LIMIT 1
        """,
        JANNAAT_COMPANY_NAME,
    )


async def _resolve_seed_user_id(conn: asyncpg.Connection, company_id: UUID) -> UUID:
    user_id = await conn.fetchval(
        """
        SELECT user_id
        FROM memberships
        WHERE company_id = $1
          AND status = 'active'
          AND deleted_at IS NULL
        ORDER BY created_at ASC
        LIMIT 1
        """,
        company_id,
    )
    if user_id is None:
        raise RuntimeError(
            "No active user membership found for the Jannat company; "
            "cannot seed operational_events.created_by_user_id."
        )
    return user_id


async def _load_departments(
    conn: asyncpg.Connection,
    company_id: UUID,
) -> dict[str, UUID]:
    rows = await conn.fetch(
        """
        SELECT id, slug, name
        FROM departments
        WHERE company_id = $1
          AND deleted_at IS NULL
        """,
        company_id,
    )
    departments: dict[str, UUID] = {}
    for row in rows:
        departments[_normalize_lookup(row["slug"])] = row["id"]
        departments[_normalize_lookup(row["name"])] = row["id"]
    return departments


async def _event_exists(
    conn: asyncpg.Connection,
    company_id: UUID,
    source_ref: str,
) -> bool:
    return bool(
        await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM operational_events
                WHERE company_id = $1
                  AND source_ref = $2
                  AND deleted_at IS NULL
            )
            """,
            company_id,
            source_ref,
        )
    )


def _resolve_department_id(
    departments: dict[str, UUID],
    candidates: tuple[str, ...],
) -> UUID | None:
    for candidate in candidates:
        department_id = departments.get(_normalize_lookup(candidate))
        if department_id is not None:
            return department_id
    return None


def _normalize_lookup(value: object) -> str:
    normalized = str(value or "").replace("_", " ").replace("-", " ").lower()
    return " ".join(normalized.split())


async def async_main() -> int:
    """Async CLI entrypoint."""
    configure_logging()
    args = parse_args()
    try:
        await seed_reference_events(args.company_id)
        return 0
    except Exception:
        logger.exception("jannat_reference_seed_failed")
        return 1


def main() -> None:
    """CLI entrypoint."""
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
