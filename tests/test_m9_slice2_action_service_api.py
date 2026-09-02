"""M9 Slice 2: Action repository/service/API tests (real Postgres, real
HTTP route via TestClient(app) for the API-layer subset).

Covers the full matrix required by the Slice 2 activation: creation
(unassigned/assigned, initial ledger events), assignee validation
(active/inactive/nonexistent/cross-company membership), status
transitions (full allowed matrix, self-transition and terminal
rejection), assignment mutation (NULL<->user, user<->user, no-op and
terminal rejection), tenancy isolation, atomicity (rejected mutations
write no event), and concurrency semantics (locked-row reads, never a
client-supplied prior state).

Most of the matrix is proven at the ActionService/ActionRepository layer
directly (fast, precise, real Postgres) - a smaller focused subset proves
the HTTP route wiring, auth, and status-code mapping end to end, mirroring
tests/test_m8_slice3b1_human_decision_api.py's pattern.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.core.security import create_token
from app.main import app
from app.ome.errors import (
    ActionNotFound,
    DecisionNotFound,
    InvalidActionTransition,
    InvalidAssignee,
    InvalidMemoryInput,
)
from app.ome.services.action_service import ActionService
from app.services.openai_client import ai_engine

from tests.test_m7_slice1_upload_truth_bridge import (
    _GoldenPermissionAuthService,
    _reset_stale_db_bindings,
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _clean_app_db_binding():
    """Autouse for every test in this module (repository/service-only
    tests included - harmless no-op for them since they never touch
    app.state). Resets any stale app.state.auth_db_pool / ai_engine
    pool binding both before AND after each test.

    `_with_permission` below already resets before each individual
    TestClient call, which is what makes a multi-request test (e.g. the
    golden-path test) work. That leaves one gap: after this test's
    LAST call, app.state.auth_db_pool still references a pool bound to
    THIS test's asyncio.run() event loop, which is about to close. The
    next test anywhere in the suite - in this file or another, e.g.
    tests/test_tenant_isolation.py, which has no reset call of its own
    - would then inherit that now-dead-loop-bound pool and fail with
    'Event loop is closed' / 'another operation is in progress'. The
    teardown reset here closes that gap: it never closes the pool
    itself (unsafe to await across an already-closed loop, per
    _reset_stale_db_bindings's own docstring) - it only discards the
    reference, forcing a fresh pool bound to whichever loop is current
    the next time anything needs one. Fixture teardown runs after the
    test body regardless of pass/fail, so this never masks a real
    assertion failure."""
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


async def _seed_company_and_user(conn, *, label: str) -> tuple[str, str]:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m9-s2-{label}-{uuid4().hex[:10]}", f"M9 Slice 2 Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m9-s2-{label}-{uuid4().hex[:10]}@example.com", f"M9 Slice 2 Test User {label}",
    )
    return str(company_id), str(user_id)


async def _seed_membership(
    conn, *, company_id: str, user_id: str, status: str = "active", department_id: str | None = None
) -> str:
    """Seed a real role + membership row so MembershipRepository.
    get_active_membership can actually find (or correctly not find) it -
    this is the real production table, not a fake."""
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


async def _seed_receipt(conn, *, company_id: str, user_id: str) -> str:
    receipt_id = await conn.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, '[]'::jsonb)
        RETURNING id
        """,
        UUID(company_id), UUID(user_id), '{"ceo_text": "test"}',
    )
    return str(receipt_id)


async def _seed_decision(conn, *, company_id: str, receipt_id: str, user_id: str) -> str:
    decision_id = await conn.fetchval(
        """
        INSERT INTO ome_decision_memories
            (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
        VALUES ($1, $2, 'Test decision', $3, NOW())
        RETURNING id
        """,
        UUID(company_id), UUID(receipt_id), UUID(user_id),
    )
    return str(decision_id)


async def _seed_chain(conn, *, label: str, with_membership: bool = True) -> dict:
    """Seed company + creator user (with an active membership so it can
    also act as a plain valid assignee target when needed) + receipt +
    decision. Returns a dict of string ids."""
    company_id, user_id = await _seed_company_and_user(conn, label=label)
    if with_membership:
        await _seed_membership(conn, company_id=company_id, user_id=user_id)
    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
    return {"company_id": company_id, "user_id": user_id, "receipt_id": receipt_id, "decision_id": decision_id}


async def _cleanup_chain(conn, chain: dict, *extra_user_ids: str) -> None:
    company_id = chain["company_id"]
    await conn.execute("DELETE FROM ome_action_change_events WHERE company_id=$1", UUID(company_id))
    await conn.execute("DELETE FROM ome_actions WHERE company_id=$1", UUID(company_id))
    await conn.execute("DELETE FROM ome_decision_memories WHERE company_id=$1", UUID(company_id))
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE company_id=$1", UUID(company_id))
    await conn.execute("DELETE FROM memberships WHERE company_id=$1", UUID(company_id))
    await conn.execute("DELETE FROM roles WHERE company_id=$1", UUID(company_id))
    await conn.execute("DELETE FROM users WHERE id=$1", UUID(chain["user_id"]))
    for uid in extra_user_ids:
        await conn.execute("DELETE FROM users WHERE id=$1", UUID(uid))
    await conn.execute("DELETE FROM companies WHERE id=$1", UUID(company_id))


async def _event_count(conn, *, company_id: str, action_id: str) -> int:
    return await conn.fetchval(
        "SELECT count(*) FROM ome_action_change_events WHERE company_id=$1 AND action_id=$2",
        UUID(company_id), UUID(action_id),
    )


# ===========================================================================
# ACTION CREATION
# ===========================================================================


def test_create_unassigned_action(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="create1")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]),
                        acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]),
                        title="Follow up with the vet",
                    )
                    assert action.status == "pending"
                    assert action.assigned_user_id is None
                    assert action.decision_memory_id == UUID(chain["decision_id"])
                    assert action.created_by_user_id == UUID(chain["user_id"])

                    events = await service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert len(events) == 1
                    assert events[0].change_type == "status"
                    assert events[0].from_status is None
                    assert events[0].to_status == "pending"
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_create_assigned_action_writes_initial_assignment_event(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="create2")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]),
                        acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]),
                        title="Ship the fix",
                        assigned_user_id=UUID(chain["user_id"]),
                    )
                    assert action.assigned_user_id == UUID(chain["user_id"])

                    events = await service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert len(events) == 2
                    status_events = [e for e in events if e.change_type == "status"]
                    assignment_events = [e for e in events if e.change_type == "assignment"]
                    assert len(status_events) == 1 and status_events[0].to_status == "pending"
                    assert len(assignment_events) == 1
                    assert assignment_events[0].from_assigned_user_id is None
                    assert assignment_events[0].to_assigned_user_id == UUID(chain["user_id"])
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_create_unassigned_action_creates_no_assignment_event(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="create3")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]),
                        acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]),
                        title="x",
                    )
                    events = await service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert all(e.change_type != "assignment" for e in events)
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_create_action_cross_company_decision_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain_a = await _seed_chain(conn, label="crossa")
                chain_b = await _seed_chain(conn, label="crossb")
                try:
                    service = ActionService(pool)
                    with pytest.raises(DecisionNotFound):
                        await service.create_action(
                            company_id=UUID(chain_b["company_id"]),
                            acting_user_id=UUID(chain_b["user_id"]),
                            decision_memory_id=UUID(chain_a["decision_id"]),
                            title="x",
                        )
                finally:
                    await _cleanup_chain(conn, chain_a)
                    await _cleanup_chain(conn, chain_b)
        finally:
            await pool.close()

    _run(scenario())


def test_create_action_nonexistent_decision_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="nodec")
                try:
                    service = ActionService(pool)
                    with pytest.raises(DecisionNotFound):
                        await service.create_action(
                            company_id=UUID(chain["company_id"]),
                            acting_user_id=UUID(chain["user_id"]),
                            decision_memory_id=uuid4(),
                            title="x",
                        )
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_create_action_blank_title_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="blank")
                try:
                    service = ActionService(pool)
                    with pytest.raises(InvalidMemoryInput):
                        await service.create_action(
                            company_id=UUID(chain["company_id"]),
                            acting_user_id=UUID(chain["user_id"]),
                            decision_memory_id=UUID(chain["decision_id"]),
                            title="   ",
                        )
                    count = await conn.fetchval(
                        "SELECT count(*) FROM ome_actions WHERE company_id=$1", UUID(chain["company_id"])
                    )
                    assert count == 0
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_one_decision_supports_multiple_actions(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="multi")
                try:
                    service = ActionService(pool)
                    a1 = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="first",
                    )
                    a2 = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="second",
                    )
                    actions = await service.list_actions(
                        company_id=UUID(chain["company_id"]), decision_memory_id=UUID(chain["decision_id"]),
                    )
                    assert {a.id for a in actions} == {a1.id, a2.id}
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# ASSIGNEE VALIDATION (create + reassign, shared semantics)
# ===========================================================================


def test_assignee_active_same_company_member_accepted(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asnok")
                assignee_id = str(await conn.fetchval(
                    "INSERT INTO users (email, full_name) VALUES ($1, 'Assignee') RETURNING id",
                    f"assignee-{uuid4().hex[:8]}@example.com",
                ))
                await _seed_membership(conn, company_id=chain["company_id"], user_id=assignee_id)
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                        assigned_user_id=UUID(assignee_id),
                    )
                    assert action.assigned_user_id == UUID(assignee_id)
                finally:
                    await _cleanup_chain(conn, chain, assignee_id)
        finally:
            await pool.close()

    _run(scenario())


def test_assignee_nonexistent_user_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asnnoexist")
                try:
                    service = ActionService(pool)
                    with pytest.raises(InvalidAssignee):
                        await service.create_action(
                            company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                            decision_memory_id=UUID(chain["decision_id"]), title="x",
                            assigned_user_id=uuid4(),
                        )
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_assignee_inactive_membership_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asninactive")
                assignee_id = str(await conn.fetchval(
                    "INSERT INTO users (email, full_name) VALUES ($1, 'Inactive') RETURNING id",
                    f"inactive-{uuid4().hex[:8]}@example.com",
                ))
                await _seed_membership(conn, company_id=chain["company_id"], user_id=assignee_id, status="suspended")
                try:
                    service = ActionService(pool)
                    with pytest.raises(InvalidAssignee):
                        await service.create_action(
                            company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                            decision_memory_id=UUID(chain["decision_id"]), title="x",
                            assigned_user_id=UUID(assignee_id),
                        )
                finally:
                    await _cleanup_chain(conn, chain, assignee_id)
        finally:
            await pool.close()

    _run(scenario())


def test_assignee_no_membership_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asnnone")
                stray_user_id = str(await conn.fetchval(
                    "INSERT INTO users (email, full_name) VALUES ($1, 'NoMembership') RETURNING id",
                    f"nomember-{uuid4().hex[:8]}@example.com",
                ))
                try:
                    service = ActionService(pool)
                    with pytest.raises(InvalidAssignee):
                        await service.create_action(
                            company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                            decision_memory_id=UUID(chain["decision_id"]), title="x",
                            assigned_user_id=UUID(stray_user_id),
                        )
                finally:
                    await _cleanup_chain(conn, chain, stray_user_id)
        finally:
            await pool.close()

    _run(scenario())


def test_assignee_cross_company_membership_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain_a = await _seed_chain(conn, label="asncrossa")
                chain_b = await _seed_chain(conn, label="asncrossb")
                try:
                    service = ActionService(pool)
                    # chain_b's user has a membership, but only in company B.
                    with pytest.raises(InvalidAssignee):
                        await service.create_action(
                            company_id=UUID(chain_a["company_id"]), acting_user_id=UUID(chain_a["user_id"]),
                            decision_memory_id=UUID(chain_a["decision_id"]), title="x",
                            assigned_user_id=UUID(chain_b["user_id"]),
                        )
                finally:
                    await _cleanup_chain(conn, chain_a)
                    await _cleanup_chain(conn, chain_b)
        finally:
            await pool.close()

    _run(scenario())


def test_assignee_unassigned_is_valid(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asnnull")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x", assigned_user_id=None,
                    )
                    assert action.assigned_user_id is None
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# STATUS TRANSITIONS
# ===========================================================================


@pytest.mark.parametrize(
    "from_status,to_status",
    [
        ("pending", "in_progress"),
        ("pending", "completed"),
        ("pending", "cancelled"),
        ("in_progress", "completed"),
        ("in_progress", "cancelled"),
    ],
)
def test_allowed_status_transitions_succeed(db_available, from_status: str, to_status: str) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label=f"tr{from_status[:2]}{to_status[:2]}")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    if from_status != "pending":
                        action = await service.change_status(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            to_status=from_status, acting_user_id=UUID(chain["user_id"]),
                        )
                    updated = await service.change_status(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        to_status=to_status, acting_user_id=UUID(chain["user_id"]),
                    )
                    assert updated.status == to_status
                    if to_status == "completed":
                        assert updated.completed_at is not None
                        assert updated.cancelled_at is None
                    elif to_status == "cancelled":
                        assert updated.cancelled_at is not None
                        assert updated.completed_at is None
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_self_transition_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="self")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    with pytest.raises(InvalidActionTransition):
                        await service.change_status(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            to_status="pending", acting_user_id=UUID(chain["user_id"]),
                        )
                    count = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    assert count == 1  # only the creation event
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


@pytest.mark.parametrize("terminal_status", ["completed", "cancelled"])
def test_terminal_status_cannot_reopen(db_available, terminal_status: str) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label=f"term{terminal_status[:3]}")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    action = await service.change_status(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        to_status=terminal_status, acting_user_id=UUID(chain["user_id"]),
                    )
                    events_before = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    with pytest.raises(InvalidActionTransition):
                        await service.change_status(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            to_status="in_progress", acting_user_id=UUID(chain["user_id"]),
                        )
                    events_after = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    assert events_after == events_before
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_status_change_cross_company_blocked(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain_a = await _seed_chain(conn, label="statcrossa")
                chain_b = await _seed_chain(conn, label="statcrossb")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain_a["company_id"]), acting_user_id=UUID(chain_a["user_id"]),
                        decision_memory_id=UUID(chain_a["decision_id"]), title="x",
                    )
                    with pytest.raises(ActionNotFound):
                        await service.change_status(
                            company_id=UUID(chain_b["company_id"]), action_id=action.id,
                            to_status="in_progress", acting_user_id=UUID(chain_b["user_id"]),
                        )
                finally:
                    await _cleanup_chain(conn, chain_a)
                    await _cleanup_chain(conn, chain_b)
        finally:
            await pool.close()

    _run(scenario())


def test_exactly_one_status_event_per_accepted_transition(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="onevt")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    await service.change_status(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        to_status="in_progress", acting_user_id=UUID(chain["user_id"]),
                    )
                    count = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    assert count == 2  # creation + this one transition
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# ASSIGNMENT MUTATION
# ===========================================================================


def test_reassign_null_to_user(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rasn1")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    updated = await service.change_assignee(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        assigned_user_id=UUID(chain["user_id"]), acting_user_id=UUID(chain["user_id"]),
                    )
                    assert updated.assigned_user_id == UUID(chain["user_id"])
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_reassign_user_a_to_user_b(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rasn2")
                user_b = str(await conn.fetchval(
                    "INSERT INTO users (email, full_name) VALUES ($1, 'UserB') RETURNING id",
                    f"userb-{uuid4().hex[:8]}@example.com",
                ))
                await _seed_membership(conn, company_id=chain["company_id"], user_id=user_b)
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                        assigned_user_id=UUID(chain["user_id"]),
                    )
                    updated = await service.change_assignee(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        assigned_user_id=UUID(user_b), acting_user_id=UUID(chain["user_id"]),
                    )
                    assert updated.assigned_user_id == UUID(user_b)

                    events = await service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    reassignment = [e for e in events if e.change_type == "assignment"][-1]
                    assert reassignment.from_assigned_user_id == UUID(chain["user_id"])
                    assert reassignment.to_assigned_user_id == UUID(user_b)
                finally:
                    await _cleanup_chain(conn, chain, user_b)
        finally:
            await pool.close()

    _run(scenario())


def test_reassign_user_to_null(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rasn3")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                        assigned_user_id=UUID(chain["user_id"]),
                    )
                    updated = await service.change_assignee(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        assigned_user_id=None, acting_user_id=UUID(chain["user_id"]),
                    )
                    assert updated.assigned_user_id is None
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_reassign_same_assignee_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rasnsame")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                        assigned_user_id=UUID(chain["user_id"]),
                    )
                    with pytest.raises(InvalidActionTransition):
                        await service.change_assignee(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            assigned_user_id=UUID(chain["user_id"]), acting_user_id=UUID(chain["user_id"]),
                        )
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_reassign_null_to_null_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rasnnn")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    with pytest.raises(InvalidActionTransition):
                        await service.change_assignee(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            assigned_user_id=None, acting_user_id=UUID(chain["user_id"]),
                        )
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_reassign_terminal_action_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rasnterm")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    action = await service.change_status(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        to_status="cancelled", acting_user_id=UUID(chain["user_id"]),
                    )
                    with pytest.raises(InvalidActionTransition):
                        await service.change_assignee(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            assigned_user_id=UUID(chain["user_id"]), acting_user_id=UUID(chain["user_id"]),
                        )
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_exactly_one_assignment_event_per_accepted_reassignment(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="onereasn")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    await service.change_assignee(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        assigned_user_id=UUID(chain["user_id"]), acting_user_id=UUID(chain["user_id"]),
                    )
                    count = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    assert count == 2  # creation status event + this one assignment event
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_rejected_reassignment_creates_no_event(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rejreasn")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    before = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    with pytest.raises(InvalidActionTransition):
                        await service.change_assignee(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            assigned_user_id=None, acting_user_id=UUID(chain["user_id"]),
                        )
                    after = await _event_count(conn, company_id=chain["company_id"], action_id=str(action.id))
                    assert after == before
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# TENANCY
# ===========================================================================


def test_cross_company_action_read_blocked(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain_a = await _seed_chain(conn, label="readcrossa")
                chain_b = await _seed_chain(conn, label="readcrossb")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain_a["company_id"]), acting_user_id=UUID(chain_a["user_id"]),
                        decision_memory_id=UUID(chain_a["decision_id"]), title="x",
                    )
                    with pytest.raises(ActionNotFound):
                        await service.get_action(company_id=UUID(chain_b["company_id"]), action_id=action.id)
                finally:
                    await _cleanup_chain(conn, chain_a)
                    await _cleanup_chain(conn, chain_b)
        finally:
            await pool.close()

    _run(scenario())


def test_cross_company_assignment_mutation_blocked(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain_a = await _seed_chain(conn, label="mutcrossa")
                chain_b = await _seed_chain(conn, label="mutcrossb")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain_a["company_id"]), acting_user_id=UUID(chain_a["user_id"]),
                        decision_memory_id=UUID(chain_a["decision_id"]), title="x",
                    )
                    with pytest.raises(ActionNotFound):
                        await service.change_assignee(
                            company_id=UUID(chain_b["company_id"]), action_id=action.id,
                            assigned_user_id=UUID(chain_b["user_id"]), acting_user_id=UUID(chain_b["user_id"]),
                        )
                finally:
                    await _cleanup_chain(conn, chain_a)
                    await _cleanup_chain(conn, chain_b)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# ATOMICITY / CONCURRENCY EVIDENCE
# ===========================================================================


def test_status_mutation_reads_locked_row_not_stale_value(db_available) -> None:
    """Concurrency-semantics evidence: change_status always derives
    from_status from the row actually in the database at lock time, never
    from any client-supplied value (the service API accepts none) - proven
    by transitioning twice in sequence and confirming the SECOND event's
    from_status matches the row's real state after the FIRST transition,
    not the Action's original creation state."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="lockread")
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    await service.change_status(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        to_status="in_progress", acting_user_id=UUID(chain["user_id"]),
                    )
                    await service.change_status(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        to_status="completed", acting_user_id=UUID(chain["user_id"]),
                    )
                    events = await service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    status_events = [e for e in events if e.change_type == "status"]
                    # NULL->pending, pending->in_progress, in_progress->completed
                    assert [(e.from_status, e.to_status) for e in status_events] == [
                        (None, "pending"), ("pending", "in_progress"), ("in_progress", "completed"),
                    ]
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_reassignment_reads_locked_row_not_stale_value(db_available) -> None:
    """Same evidence for assignment: from_assigned_user_id always comes
    from the locked row, proven by two sequential reassignments where the
    second's from_assigned_user_id must equal the first's to_assigned_user_id."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="lockreasn")
                user_b = str(await conn.fetchval(
                    "INSERT INTO users (email, full_name) VALUES ($1, 'B') RETURNING id",
                    f"lockb-{uuid4().hex[:8]}@example.com",
                ))
                await _seed_membership(conn, company_id=chain["company_id"], user_id=user_b)
                try:
                    service = ActionService(pool)
                    action = await service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                        assigned_user_id=UUID(chain["user_id"]),
                    )
                    await service.change_assignee(
                        company_id=UUID(chain["company_id"]), action_id=action.id,
                        assigned_user_id=UUID(user_b), acting_user_id=UUID(chain["user_id"]),
                    )
                    events = await service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assignment_events = [e for e in events if e.change_type == "assignment"]
                    assert assignment_events[0].from_assigned_user_id is None
                    assert assignment_events[0].to_assigned_user_id == UUID(chain["user_id"])
                    assert assignment_events[1].from_assigned_user_id == UUID(chain["user_id"])
                    assert assignment_events[1].to_assigned_user_id == UUID(user_b)
                finally:
                    await _cleanup_chain(conn, chain, user_b)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# FAILURE INJECTION / GENUINE TRANSACTION ROLLBACK
# ===========================================================================
#
# The tests above prove that a REJECTED domain mutation (invalid transition,
# no-op, terminal, bad assignee) writes no row/event - but that is a
# pre-transaction validation path, not proof that the transaction itself
# rolls back correctly if the event INSERT fails for some other reason
# after the current-state row has already been mutated inside the same
# transaction. These three tests prove that with a REAL asyncpg
# transaction and a REAL injected failure - not a mock of the repository
# method, not a validation-rejection path, not a missing-resource path.
#
# The wrapper below passes every call straight through to the real
# connection/pool EXCEPT execute() calls that target
# ome_action_change_events, which it fails on demand. Because
# conn.transaction() and the row INSERT/UPDATE (via fetchrow) are real,
# the surrounding `async with conn.transaction():` block in
# ActionRepository sees a genuine exception mid-transaction and asyncpg
# performs a genuine rollback - exactly the "failure after the row
# mutation, before commit" scenario required.


class _EventInsertFailingConnection:
    """Wraps one real asyncpg connection. execute() raises on any
    statement targeting ome_action_change_events; every other call
    (fetchrow, transaction(), etc.) passes through to the real
    connection unchanged."""

    def __init__(self, real_conn) -> None:
        self._real_conn = real_conn

    async def execute(self, query, *args, **kwargs):
        if "ome_action_change_events" in query:
            raise RuntimeError("injected failure: event insert (test-only)")
        return await self._real_conn.execute(query, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._real_conn, name)


class _AcquireCtx:
    def __init__(self, real_pool) -> None:
        self._real_pool = real_pool
        self._acquire_ctx = None

    async def __aenter__(self):
        self._acquire_ctx = self._real_pool.acquire()
        real_conn = await self._acquire_ctx.__aenter__()
        return _EventInsertFailingConnection(real_conn)

    async def __aexit__(self, *exc_info):
        return await self._acquire_ctx.__aexit__(*exc_info)


class _EventInsertFailingPool:
    """Test-only wrapper around a real asyncpg Pool. Only intercepts the
    connection returned by acquire() (used by the write paths under
    test); every other pool-level call - fetchrow/fetch/fetchval used
    directly by plain reads and by DecisionMemoryRepository (constructed
    internally by ActionService from this same `db`) - passes straight
    through to the real pool unchanged."""

    def __init__(self, real_pool) -> None:
        self._real_pool = real_pool

    def acquire(self):
        return _AcquireCtx(self._real_pool)

    def __getattr__(self, name):
        return getattr(self._real_pool, name)


def test_creation_rollback_on_event_insert_failure(db_available) -> None:
    """Failure injected during the mandatory NULL->pending event insert,
    after the Action row insert. Proves neither row survives - the
    Action insert must not be committed independently of its creation
    event (Architecture Contract Sec 24: "An Action without its creation
    event must be impossible")."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rbcreate")
                try:
                    failing_repo_service = ActionService(_EventInsertFailingPool(pool))
                    with pytest.raises(RuntimeError, match="injected failure"):
                        await failing_repo_service.create_action(
                            company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                            decision_memory_id=UUID(chain["decision_id"]), title="should not persist",
                        )
                    action_count = await conn.fetchval(
                        "SELECT count(*) FROM ome_actions WHERE company_id=$1", UUID(chain["company_id"])
                    )
                    event_count = await conn.fetchval(
                        "SELECT count(*) FROM ome_action_change_events WHERE company_id=$1", UUID(chain["company_id"])
                    )
                    assert action_count == 0
                    assert event_count == 0
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_status_mutation_rollback_on_event_insert_failure(db_available) -> None:
    """Failure injected during the status change-event insert, AFTER the
    Action row's status/timestamps have already been updated inside the
    same transaction. Proves the row update itself is rolled back, not
    just the event."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rbstatus")
                try:
                    real_service = ActionService(pool)
                    action = await real_service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    original_updated_at = action.updated_at

                    failing_repo_service = ActionService(_EventInsertFailingPool(pool))
                    with pytest.raises(RuntimeError, match="injected failure"):
                        await failing_repo_service.change_status(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            to_status="completed", acting_user_id=UUID(chain["user_id"]),
                        )

                    reloaded = await real_service.action_repo.get_by_id(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert reloaded is not None
                    assert reloaded.status == "pending"
                    assert reloaded.completed_at is None
                    assert reloaded.cancelled_at is None
                    assert reloaded.updated_at == original_updated_at

                    events = await real_service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert len(events) == 1  # only the original creation event
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


def test_assignment_mutation_rollback_on_event_insert_failure(db_available) -> None:
    """Failure injected during the assignment change-event insert, AFTER
    the Action row's assigned_user_id has already been updated inside
    the same transaction. Proves the row update itself is rolled back,
    not just the event."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="rbassign")
                try:
                    real_service = ActionService(pool)
                    action = await real_service.create_action(
                        company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                        decision_memory_id=UUID(chain["decision_id"]), title="x",
                    )
                    assert action.assigned_user_id is None

                    failing_repo_service = ActionService(_EventInsertFailingPool(pool))
                    with pytest.raises(RuntimeError, match="injected failure"):
                        await failing_repo_service.change_assignee(
                            company_id=UUID(chain["company_id"]), action_id=action.id,
                            assigned_user_id=UUID(chain["user_id"]), acting_user_id=UUID(chain["user_id"]),
                        )

                    reloaded = await real_service.action_repo.get_by_id(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert reloaded is not None
                    assert reloaded.assigned_user_id is None

                    events = await real_service.action_repo.list_change_events(
                        company_id=UUID(chain["company_id"]), action_id=action.id
                    )
                    assert len(events) == 1  # only the original creation event
                    assert all(e.change_type != "assignment" for e in events)
                finally:
                    await _cleanup_chain(conn, chain)
        finally:
            await pool.close()

    _run(scenario())


# ===========================================================================
# API LAYER (HTTP wiring, auth, status-code mapping)
# ===========================================================================


def _headers(company_id: str, user_id: str) -> dict:
    token = create_token(company_id=company_id, user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def _with_permission(client, method, path, headers, *, json=None, permissions=("memory.write",)):
    # Reset before EVERY call, not just once per test: TestClient does not
    # keep one persistent event loop alive across separate calls in this
    # environment (see _reset_stale_db_bindings's own docstring), and a
    # golden-path test chains several sequential requests on one client.
    _reset_stale_db_bindings(app, ai_engine)
    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_GoldenPermissionAuthService(list(permissions))),
    ):
        if json is None:
            return getattr(client, method)(path, headers=headers)
        return getattr(client, method)(path, headers=headers, json=json)


def test_api_post_actions_creates_action(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                return await _seed_chain(conn, label="api1")
        finally:
            await pool.close()

    chain = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        resp = _with_permission(
            client, "post", "/actions", _headers(chain["company_id"], chain["user_id"]),
            json={"decision_memory_id": chain["decision_id"], "title": "Do the thing"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "pending"
        assert body["assigned_user_id"] is None
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_post_actions_rejects_extra_field(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                return await _seed_chain(conn, label="api2")
        finally:
            await pool.close()

    chain = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        resp = _with_permission(
            client, "post", "/actions", _headers(chain["company_id"], chain["user_id"]),
            json={"decision_memory_id": chain["decision_id"], "title": "x", "company_id": str(uuid4())},
        )
        assert resp.status_code == 422
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_full_golden_path(db_available) -> None:
    """POST -> GET list -> GET detail (with history) -> PATCH status ->
    PATCH assignee, all through real HTTP routes."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                return await _seed_chain(conn, label="golden")
        finally:
            await pool.close()

    chain = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        headers = _headers(chain["company_id"], chain["user_id"])

        create_resp = _with_permission(
            client, "post", "/actions", headers,
            json={"decision_memory_id": chain["decision_id"], "title": "Golden path action"},
        )
        assert create_resp.status_code == 201, create_resp.text
        action_id = create_resp.json()["id"]

        list_resp = _with_permission(
            client, "get", f"/actions?decision_memory_id={chain['decision_id']}", headers,
        )
        assert list_resp.status_code == 200
        assert any(a["id"] == action_id for a in list_resp.json())

        detail_resp = _with_permission(client, "get", f"/actions/{action_id}", headers)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail["events"]) == 1
        assert detail["events"][0]["to_status"] == "pending"

        status_resp = _with_permission(
            client, "patch", f"/actions/{action_id}/status", headers, json={"status": "in_progress"},
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "in_progress"

        assignee_resp = _with_permission(
            client, "patch", f"/actions/{action_id}/assignee", headers,
            json={"assigned_user_id": chain["user_id"]},
        )
        assert assignee_resp.status_code == 200
        assert assignee_resp.json()["assigned_user_id"] == chain["user_id"]

        terminal_resp = _with_permission(
            client, "patch", f"/actions/{action_id}/status", headers, json={"status": "completed"},
        )
        assert terminal_resp.status_code == 200

        reopen_resp = _with_permission(
            client, "patch", f"/actions/{action_id}/status", headers, json={"status": "in_progress"},
        )
        assert reopen_resp.status_code == 409

        terminal_reassign_resp = _with_permission(
            client, "patch", f"/actions/{action_id}/assignee", headers, json={"assigned_user_id": None},
        )
        assert terminal_reassign_resp.status_code == 409
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_get_action_cross_company_returns_404(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain_a = await _seed_chain(conn, label="apicrossa")
                chain_b = await _seed_chain(conn, label="apicrossb")
                service = ActionService(pool)
                action = await service.create_action(
                    company_id=UUID(chain_a["company_id"]), acting_user_id=UUID(chain_a["user_id"]),
                    decision_memory_id=UUID(chain_a["decision_id"]), title="x",
                )
                return chain_a, chain_b, str(action.id)
        finally:
            await pool.close()

    chain_a, chain_b, action_id = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        resp = _with_permission(
            client, "get", f"/actions/{action_id}", _headers(chain_b["company_id"], chain_b["user_id"]),
        )
        assert resp.status_code == 404
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain_a)
                    await _cleanup_chain(conn, chain_b)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_missing_permission_returns_403(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                return await _seed_chain(conn, label="api403")
        finally:
            await pool.close()

    chain = _run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        resp = _with_permission(
            client, "post", "/actions", _headers(chain["company_id"], chain["user_id"]),
            json={"decision_memory_id": chain["decision_id"], "title": "x"},
            permissions=(),
        )
        assert resp.status_code == 403
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


# ===========================================================================
# BLOCKER 1 — assigned_user_id REQUIRED (nullable, but no default)
# ===========================================================================


def test_api_patch_assignee_empty_body_rejected(db_available) -> None:
    """{} must be 422 - assigned_user_id is REQUIRED (nullable, not
    defaulted); an omitted field must never be silently treated as
    'unassign'."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asnreq1")
                service = ActionService(pool)
                action = await service.create_action(
                    company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                    decision_memory_id=UUID(chain["decision_id"]), title="x",
                    assigned_user_id=UUID(chain["user_id"]),
                )
                return chain, str(action.id)
        finally:
            await pool.close()

    chain, action_id = _run(seed())
    try:
        client = TestClient(app)
        resp = _with_permission(
            client, "patch", f"/actions/{action_id}/assignee", _headers(chain["company_id"], chain["user_id"]),
            json={},
        )
        assert resp.status_code == 422

        async def verify_unmutated():
            pool = await _make_pool()
            try:
                service = ActionService(pool)
                action = await service.action_repo.get_by_id(
                    company_id=UUID(chain["company_id"]), action_id=UUID(action_id)
                )
                assert action.assigned_user_id == UUID(chain["user_id"])
                events = await service.action_repo.list_change_events(
                    company_id=UUID(chain["company_id"]), action_id=UUID(action_id)
                )
                assert all(e.change_type != "assignment" or e.to_assigned_user_id == UUID(chain["user_id"])
                           for e in events)
                assert len(events) == 2  # creation status event + creation assignment event only
            finally:
                await pool.close()

        _run(verify_unmutated())
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_patch_assignee_explicit_null_still_unassigns(db_available) -> None:
    """{"assigned_user_id": null} must remain a valid, successful
    unassign request - proving the fix distinguishes 'omitted' from
    'explicit null' rather than rejecting null outright."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="asnreq2")
                service = ActionService(pool)
                action = await service.create_action(
                    company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                    decision_memory_id=UUID(chain["decision_id"]), title="x",
                    assigned_user_id=UUID(chain["user_id"]),
                )
                return chain, str(action.id)
        finally:
            await pool.close()

    chain, action_id = _run(seed())
    try:
        client = TestClient(app)
        resp = _with_permission(
            client, "patch", f"/actions/{action_id}/assignee", _headers(chain["company_id"], chain["user_id"]),
            json={"assigned_user_id": None},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["assigned_user_id"] is None
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


# ===========================================================================
# BLOCKER 3 — server-derived field injection rejected (extra="forbid")
# ===========================================================================


@pytest.mark.parametrize(
    "forbidden_field,forbidden_value",
    [
        ("company_id", lambda: str(uuid4())),
        ("created_by_user_id", lambda: str(uuid4())),
        ("status", lambda: "completed"),
    ],
)
def test_api_create_action_rejects_server_derived_field_injection(
    db_available, forbidden_field: str, forbidden_value
) -> None:
    """POST /actions must reject any attempt to client-supply a
    server-owned field - company_id, created_by_user_id, or an initial
    status override - with 422, and must create no row."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                return await _seed_chain(conn, label=f"inj{forbidden_field[:4]}")
        finally:
            await pool.close()

    chain = _run(seed())
    try:
        client = TestClient(app)
        body = {"decision_memory_id": chain["decision_id"], "title": "x", forbidden_field: forbidden_value()}
        resp = _with_permission(
            client, "post", "/actions", _headers(chain["company_id"], chain["user_id"]), json=body,
        )
        assert resp.status_code == 422, resp.text

        async def verify_no_row():
            pool = await _make_pool()
            try:
                count = await pool.fetchval(
                    "SELECT count(*) FROM ome_actions WHERE company_id=$1", UUID(chain["company_id"])
                )
                assert count == 0
            finally:
                await pool.close()

        _run(verify_no_row())
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_patch_status_rejects_changed_by_user_id_injection(db_available) -> None:
    """PATCH /actions/{id}/status must reject a client-supplied
    changed_by_user_id with 422 and must not mutate the Action or write
    an event - the acting identity is always server-derived from
    AuthContext."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="injstat")
                service = ActionService(pool)
                action = await service.create_action(
                    company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                    decision_memory_id=UUID(chain["decision_id"]), title="x",
                )
                return chain, str(action.id)
        finally:
            await pool.close()

    chain, action_id = _run(seed())
    try:
        client = TestClient(app)
        resp = _with_permission(
            client, "patch", f"/actions/{action_id}/status", _headers(chain["company_id"], chain["user_id"]),
            json={"status": "in_progress", "changed_by_user_id": str(uuid4())},
        )
        assert resp.status_code == 422

        async def verify_unmutated():
            pool = await _make_pool()
            try:
                service = ActionService(pool)
                action = await service.action_repo.get_by_id(
                    company_id=UUID(chain["company_id"]), action_id=UUID(action_id)
                )
                assert action.status == "pending"
                events = await service.action_repo.list_change_events(
                    company_id=UUID(chain["company_id"]), action_id=UUID(action_id)
                )
                assert len(events) == 1  # only the creation event
            finally:
                await pool.close()

        _run(verify_unmutated())
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())


def test_api_patch_assignee_rejects_changed_by_user_id_injection(db_available) -> None:
    """PATCH /actions/{id}/assignee must reject a client-supplied
    changed_by_user_id with 422 and must not mutate the Action or write
    an event."""

    async def seed():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                chain = await _seed_chain(conn, label="injasn")
                service = ActionService(pool)
                action = await service.create_action(
                    company_id=UUID(chain["company_id"]), acting_user_id=UUID(chain["user_id"]),
                    decision_memory_id=UUID(chain["decision_id"]), title="x",
                )
                return chain, str(action.id)
        finally:
            await pool.close()

    chain, action_id = _run(seed())
    try:
        client = TestClient(app)
        resp = _with_permission(
            client, "patch", f"/actions/{action_id}/assignee", _headers(chain["company_id"], chain["user_id"]),
            json={"assigned_user_id": chain["user_id"], "changed_by_user_id": str(uuid4())},
        )
        assert resp.status_code == 422

        async def verify_unmutated():
            pool = await _make_pool()
            try:
                service = ActionService(pool)
                action = await service.action_repo.get_by_id(
                    company_id=UUID(chain["company_id"]), action_id=UUID(action_id)
                )
                assert action.assigned_user_id is None
                events = await service.action_repo.list_change_events(
                    company_id=UUID(chain["company_id"]), action_id=UUID(action_id)
                )
                assert len(events) == 1  # only the creation event
            finally:
                await pool.close()

        _run(verify_unmutated())
    finally:
        async def cleanup():
            pool = await _make_pool()
            try:
                async with pool.acquire() as conn:
                    await _cleanup_chain(conn, chain)
            finally:
                await pool.close()

        _run(cleanup())
