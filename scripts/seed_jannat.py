"""Seed the Jannat Al-Firdaws operational tenant for NAWA staging.

Idempotent: each resource is checked before creation.
Safe to re-run against an existing database.

Usage:
    DEMO_OWNER_PASSWORD=yourpassword python scripts/seed_jannat.py

Required environment variables:
    DATABASE_URL         — PostgreSQL connection string (direct, not pooler)
    DEMO_OWNER_PASSWORD  — Password for owner@jannat-local.dev
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from uuid import UUID

import asyncpg

from app.core.config import settings
from app.core.passwords import hash_password
from app.repositories.company_repository import CompanyRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.company_bootstrap_service import CompanyBootstrapService
from app.services.department_service import DepartmentService


COMPANY_SLUG = "jannat-al-firdaws"
COMPANY_NAME = "Jannat Al-Firdaws"
OWNER_EMAIL = "owner@jannat-local.dev"
OWNER_FULL_NAME = "Jannat Owner"

JANNAT_DIVISIONS: list[tuple[str, str, str]] = [
    (
        "Executive Management",
        "custom",
        "Company-wide executive intelligence for cross-division priorities and decisions.",
    ),
    (
        "Dairtna Poultry",
        "production_ai",
        "Poultry operations: halls, feed, egg production, veterinary, warehouse, and sales.",
    ),
    (
        "Caesar Beverage",
        "production_ai",
        "Beverage operations: production, distribution, and quality.",
    ),
    (
        "Shared Corporate Services",
        "custom",
        "HR, finance, and procurement services shared across all Jannat divisions.",
    ),
]

COMPANY_INTELLIGENCE_PROFILE: dict[str, object] = {
    "company_name": "Jannat Al-Firdaws",
    "industry": "Agri-food production and beverage operations",
    "business_type": "Multi-division enterprise",
    "country_market": "Jordan / Middle East",
    "company_size": "Multi-division: Dairtna Poultry, Caesar Beverage, Shared Corporate Services",
    "departments_enabled": [
        "Executive Management",
        "Dairtna Poultry",
        "Caesar Beverage",
        "Shared Corporate Services",
    ],
    "primary_goals": (
        "Operational intelligence across poultry and beverage divisions, "
        "grounded in daily field reality before ERP."
    ),
    "current_operational_challenges": (
        "Feed cost pressure, hall mortality rates, production cycle tracking, "
        "and cross-division cash management."
    ),
    "growth_priorities": (
        "Native AI grounding before ERP. Phase 1: Dairtna Poultry operational interpreter."
    ),
    "preferred_response_language": "ar",
    "is_active": True,
}


def _configure_logging() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")


def _ok(message: str) -> None:
    print(f"  ok    {message}")


def _skip(message: str) -> None:
    print(f"  skip  {message}")


def _fail(message: str) -> None:
    print(f"  FAIL  {message}", file=sys.stderr)


async def _ensure_jannat_divisions(
    conn: asyncpg.Connection,
    company_id: UUID,
    created_by_user_id: UUID,
) -> None:
    department_repo = DepartmentRepository(conn)
    department_service = DepartmentService(conn)

    print("\nDivisions:")
    for name, department_type, description in JANNAT_DIVISIONS:
        slug = DepartmentService.normalize_slug(name)
        existing = await department_repo.get_by_slug(company_id=company_id, slug=slug)
        if existing is not None:
            _skip(f"{name} (slug={slug})")
            continue
        await department_service.create_department(
            company_id=company_id,
            name=name,
            department_type=department_type,
            description=description,
            ai_agent_enabled=True,
            ai_agent_config={"jannat": True},
            created_by_user_id=created_by_user_id,
        )
        _ok(f"{name} created (slug={slug})")


async def _ensure_intelligence_profile(
    conn: asyncpg.Connection,
    company_id: UUID,
    updated_by_user_id: UUID,
) -> None:
    company_repo = CompanyRepository(conn)
    existing_profile = await company_repo.get_intelligence_profile(company_id)
    if existing_profile.get("is_active"):
        _skip("intelligence profile (already active)")
        return
    await company_repo.update_intelligence_profile(
        company_id=company_id,
        profile=COMPANY_INTELLIGENCE_PROFILE,
        updated_by_user_id=updated_by_user_id,
    )
    _ok("intelligence profile set")


async def seed_jannat(password: str) -> None:
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    conn = await asyncpg.connect(dsn=settings.DATABASE_URL, timeout=15)
    try:
        password_hash = hash_password(password)
        company_repo = CompanyRepository(conn)
        user_repo = UserRepository(conn)
        membership_repo = MembershipRepository(conn)
        role_repo = RoleRepository(conn)

        print("\nCompany:")
        existing_company = await company_repo.get_by_slug(COMPANY_SLUG)

        if existing_company is None:
            bootstrap = CompanyBootstrapService(conn)
            result = await bootstrap.register_company_owner(
                company_slug=COMPANY_SLUG,
                company_name=COMPANY_NAME,
                owner_email=OWNER_EMAIL,
                owner_full_name=OWNER_FULL_NAME,
                owner_password_hash=password_hash,
                company_plan="staging",
                company_metadata={},
            )
            company = result["company"]
            user_id: UUID = result["user"]["id"]  # type: ignore[assignment]
            _ok(f"Jannat Al-Firdaws created (id={company['id']})")
            _ok(f"owner user created ({OWNER_EMAIL})")
            _ok("owner membership created")
        else:
            company = existing_company
            _skip(f"Jannat Al-Firdaws already exists (id={company['id']})")

            print("\nOwner:")
            existing_user = await user_repo.get_by_email(OWNER_EMAIL)
            if existing_user is None:
                created_user = await user_repo.create_user(
                    email=OWNER_EMAIL,
                    full_name=OWNER_FULL_NAME,
                    password_hash=password_hash,
                )
                user_id = created_user["id"]  # type: ignore[assignment]
                _ok(f"owner user created ({OWNER_EMAIL})")
            else:
                user_id = existing_user["id"]  # type: ignore[assignment]
                await user_repo.update_user(
                    user_id=user_id,
                    password_hash=password_hash,
                    updated_by_user_id=user_id,
                )
                _skip(f"{OWNER_EMAIL} (password synced to DEMO_OWNER_PASSWORD)")

            print("\nMembership:")
            existing_membership = await membership_repo.get_active_membership(
                company_id=company["id"],  # type: ignore[arg-type]
                user_id=user_id,
            )
            if existing_membership is None:
                owner_role = await role_repo.get_system_role_by_slug("owner")
                if owner_role is None:
                    raise RuntimeError(
                        "owner system role not found — run migrations before seeding"
                    )
                await membership_repo.create_membership(
                    company_id=company["id"],  # type: ignore[arg-type]
                    user_id=user_id,
                    role_id=owner_role["id"],  # type: ignore[arg-type]
                    status="active",
                    accepted_at=datetime.now(timezone.utc),
                    created_by_user_id=user_id,
                )
                _ok("owner membership created")
            else:
                _skip("owner membership (already exists)")

        await _ensure_jannat_divisions(
            conn=conn,
            company_id=company["id"],  # type: ignore[arg-type]
            created_by_user_id=user_id,
        )

        print("\nIntelligence profile:")
        await _ensure_intelligence_profile(
            conn=conn,
            company_id=company["id"],  # type: ignore[arg-type]
            updated_by_user_id=user_id,
        )

        print(f"\nJannat Al-Firdaws staging tenant ready.")
        print(f"  company_id  {company['id']}")
        print(f"  owner       {OWNER_EMAIL}")
        print(f"  login slug  {COMPANY_SLUG}")

    finally:
        await conn.close()


async def _async_main() -> int:
    _configure_logging()

    password = os.getenv("DEMO_OWNER_PASSWORD", "").strip()
    if not password:
        _fail("DEMO_OWNER_PASSWORD is required")
        _fail("Usage: DEMO_OWNER_PASSWORD=yourpassword python scripts/seed_jannat.py")
        return 1

    try:
        await seed_jannat(password)
        return 0
    except Exception as exc:
        _fail(f"seed failed: {exc}")
        return 1


def main() -> None:
    raise SystemExit(asyncio.run(_async_main()))


if __name__ == "__main__":
    main()
