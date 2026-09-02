"""M9 Slice 3 completion pass: company-member source (real Postgres).

Covers the bounded read-only GET /company/members endpoint added to serve
the Action assignee selector (Founder Decision, M9 Slice 3 completion
pass): MembershipRepository.list_active_company_members at the repository
layer, plus a smaller HTTP-layer subset for route wiring, auth, tenancy,
and response-shape, mirroring tests/test_m9_slice2_action_service_api.py's
own pattern.
"""
from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.core.security import create_token
from app.main import app
from app.repositories.membership_repository import MembershipRepository
from app.services.openai_client import ai_engine

from tests.test_m7_slice1_upload_truth_bridge import (
    _GoldenPermissionAuthService,
    _reset_stale_db_bindings,
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _clean_app_db_binding():
    """Same rationale as tests/test_m9_slice2_action_service_api.py's own
    fixture of this name: resets any stale app.state.auth_db_pool binding
    both before and after every test in this module, closing the same
    cross-file event-loop-reuse gap."""
    _reset_stale_db_bindings(app, ai_engine)
    yield
    _reset_stale_db_bindings(app, ai_engine)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=5)


# ---------------------------------------------------------------------------
# Seeding / cleanup helpers
# ---------------------------------------------------------------------------


async def _seed_company(conn, *, label: str) -> str:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m9-s3-{label}-{uuid4().hex[:10]}", f"M9 Slice 3 Test Company {label}",
    )
    return str(company_id)


async def _seed_user(conn, *, label: str, full_name: str | None = None) -> str:
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m9-s3-{label}-{uuid4().hex[:10]}@example.com", full_name or f"M9 Slice 3 Test User {label}",
    )
    return str(user_id)


async def _seed_membership(
    conn, *, company_id: str, user_id: str, status: str = "active", department_id: str | None = None
) -> str:
    role_id = await conn.fetchval(
        """
        INSERT INTO roles (company_id, name, slug, permissions)
        VALUES ($1, 'Test Role', $2, '["memory.write"]'::jsonb)
        RETURNING id
        """,
        UUID(company_id), f"test-role-{uuid4().hex[:8]}",
    )
    membership_id = await conn.fetchval(
        """
        INSERT INTO memberships (company_id, user_id, role_id, department_id, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        UUID(company_id), UUID(user_id), role_id, UUID(department_id) if department_id else None, status,
    )
    return str(membership_id)


async def _cleanup(conn, *, company_ids: list[str], user_ids: list[str]) -> None:
    for company_id in company_ids:
        await conn.execute("DELETE FROM memberships WHERE company_id=$1", UUID(company_id))
        await conn.execute("DELETE FROM roles WHERE company_id=$1", UUID(company_id))
    for user_id in user_ids:
        await conn.execute("DELETE FROM users WHERE id=$1", UUID(user_id))
    for company_id in company_ids:
        await conn.execute("DELETE FROM companies WHERE id=$1", UUID(company_id))


# ===========================================================================
# REPOSITORY LAYER
# ===========================================================================


def test_active_same_company_member_returned(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label="active1")
                user_id = await _seed_user(conn, label="active1", full_name="Amina Yusuf")
                await _seed_membership(conn, company_id=company_id, user_id=user_id, status="active")
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_id))
                    assert len(members) == 1
                    assert members[0]["id"] == UUID(user_id)
                    assert members[0]["full_name"] == "Amina Yusuf"
                finally:
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_id])
        finally:
            await pool.close()

    _run(scenario())


def test_multiple_active_memberships_dedupe_to_one_user(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label="dedupe1")
                user_id = await _seed_user(conn, label="dedupe1")
                dept_id = await conn.fetchval(
                    "INSERT INTO departments (company_id, name, slug, department_type) "
                    "VALUES ($1, 'Ops', $2, 'operations') RETURNING id",
                    UUID(company_id), f"ops-{uuid4().hex[:8]}",
                )
                # Company-wide membership plus a department-scoped one for
                # the SAME user - the documented dual-membership shape.
                await _seed_membership(conn, company_id=company_id, user_id=user_id, status="active")
                await _seed_membership(
                    conn, company_id=company_id, user_id=user_id, status="active", department_id=str(dept_id)
                )
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_id))
                    assert len(members) == 1
                    assert members[0]["id"] == UUID(user_id)
                finally:
                    # Memberships reference the department row (FK) - clear
                    # them before deleting the department, which _cleanup's
                    # own membership delete would otherwise race against.
                    await conn.execute("DELETE FROM memberships WHERE company_id=$1", UUID(company_id))
                    await conn.execute("DELETE FROM departments WHERE id=$1", dept_id)
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_id])
        finally:
            await pool.close()

    _run(scenario())


@pytest.mark.parametrize("excluded_status", ["invited", "suspended", "revoked"])
def test_non_active_membership_statuses_excluded(db_available, excluded_status) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label=f"excl-{excluded_status}")
                user_id = await _seed_user(conn, label=f"excl-{excluded_status}")
                await _seed_membership(conn, company_id=company_id, user_id=user_id, status=excluded_status)
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_id))
                    assert members == []
                finally:
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_id])
        finally:
            await pool.close()

    _run(scenario())


def test_membership_only_in_another_company_excluded(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a = await _seed_company(conn, label="crossA")
                company_b = await _seed_company(conn, label="crossB")
                user_id = await _seed_user(conn, label="cross1")
                await _seed_membership(conn, company_id=company_b, user_id=user_id, status="active")
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_a))
                    assert members == []
                finally:
                    await _cleanup(conn, company_ids=[company_a, company_b], user_ids=[user_id])
        finally:
            await pool.close()

    _run(scenario())


def test_member_of_another_company_cannot_leak_alongside_real_member(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a = await _seed_company(conn, label="leakA")
                company_b = await _seed_company(conn, label="leakB")
                user_a = await _seed_user(conn, label="leak-a")
                user_b = await _seed_user(conn, label="leak-b")
                await _seed_membership(conn, company_id=company_a, user_id=user_a, status="active")
                await _seed_membership(conn, company_id=company_b, user_id=user_b, status="active")
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_a))
                    member_ids = {member["id"] for member in members}
                    assert member_ids == {UUID(user_a)}
                    assert UUID(user_b) not in member_ids
                finally:
                    await _cleanup(conn, company_ids=[company_a, company_b], user_ids=[user_a, user_b])
        finally:
            await pool.close()

    _run(scenario())


def test_list_is_deterministically_ordered(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label="order1")
                user_z = await _seed_user(conn, label="order-z", full_name="Zaid Karim")
                user_a = await _seed_user(conn, label="order-a", full_name="Amal Nasser")
                await _seed_membership(conn, company_id=company_id, user_id=user_z, status="active")
                await _seed_membership(conn, company_id=company_id, user_id=user_a, status="active")
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_id))
                    assert [member["full_name"] for member in members] == ["Amal Nasser", "Zaid Karim"]
                finally:
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_z, user_a])
        finally:
            await pool.close()

    _run(scenario())


def test_response_exposes_only_approved_fields(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label="fields1")
                user_id = await _seed_user(conn, label="fields1")
                await _seed_membership(conn, company_id=company_id, user_id=user_id, status="active")
                try:
                    members = await MembershipRepository(pool).list_active_company_members(UUID(company_id))
                    assert len(members) == 1
                    assert set(members[0].keys()) == {"id", "full_name", "email"}
                finally:
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_id])
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# API LAYER (HTTP wiring, auth, tenancy, response shape)
# ===========================================================================


def _headers(company_id: str, user_id: str) -> dict:
    token = create_token(company_id=company_id, user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def _with_permission(client, method, path, headers, *, permissions=("memory.write",)):
    _reset_stale_db_bindings(app, ai_engine)
    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_GoldenPermissionAuthService(list(permissions))),
    ):
        return getattr(client, method)(path, headers=headers)


def test_api_get_company_members_returns_active_member(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label="api1")
                user_id = await _seed_user(conn, label="api1", full_name="Huda Saleh")
                await _seed_membership(conn, company_id=company_id, user_id=user_id, status="active")
                return company_id, user_id
        finally:
            await pool.close()

    company_id, user_id = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        resp = _with_permission(client, "get", "/company/members", _headers(company_id, user_id))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body) == 1
        assert body[0] == {"id": user_id, "full_name": "Huda Saleh", "email": body[0]["email"]}
        assert set(body[0].keys()) == {"id", "full_name", "email"}
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_id])
            finally:
                await pool.close()

        _run(cleanup())


def test_api_get_company_members_scope_is_token_derived_not_query(db_available) -> None:
    """No company_id can be requested via query string or body - the route
    takes none. Passing one is simply ignored by FastAPI (unused extra
    query param), proving there is no client-controlled scope input at all."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a = await _seed_company(conn, label="scopeA")
                company_b = await _seed_company(conn, label="scopeB")
                user_a = await _seed_user(conn, label="scope-a")
                user_b = await _seed_user(conn, label="scope-b")
                await _seed_membership(conn, company_id=company_a, user_id=user_a, status="active")
                await _seed_membership(conn, company_id=company_b, user_id=user_b, status="active")
                return company_a, user_a, company_b, user_b
        finally:
            await pool.close()

    company_a, user_a, company_b, user_b = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        # Authenticated as company A, but attempts to smuggle company B's id
        # via the query string - must be ignored; result must reflect only
        # the JWT-derived company (A).
        resp = _with_permission(
            client, "get", f"/company/members?company_id={company_b}", _headers(company_a, user_a)
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert {member["id"] for member in body} == {user_a}
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup(conn, company_ids=[company_a, company_b], user_ids=[user_a, user_b])
            finally:
                await pool.close()

        _run(cleanup())


def test_api_get_company_members_requires_permission(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id = await _seed_company(conn, label="perm1")
                user_id = await _seed_user(conn, label="perm1")
                await _seed_membership(conn, company_id=company_id, user_id=user_id, status="active")
                return company_id, user_id
        finally:
            await pool.close()

    company_id, user_id = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        resp = _with_permission(
            client, "get", "/company/members", _headers(company_id, user_id), permissions=("departments.read",)
        )
        assert resp.status_code == 403
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup(conn, company_ids=[company_id], user_ids=[user_id])
            finally:
                await pool.close()

        _run(cleanup())


def test_router_exposes_no_mutation_route() -> None:
    """Read-only law: the company-members router must never grow a
    POST/PATCH/PUT/DELETE route - this endpoint exists to serve a
    selector, not to manage membership."""
    from app.api.company_members import router as company_members_router

    methods = {method for route in company_members_router.routes for method in getattr(route, "methods", set())}
    assert methods == {"GET"}
