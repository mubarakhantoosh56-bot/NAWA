"""M9 Slice 1: Action persistence-foundation schema contract tests.

Proves migrations/015_decision_execution_foundation.sql's two tables
(ome_actions, ome_action_change_events) exist with the required FKs,
CHECK constraints, and tenant-safe composite FK behavior - schema-level
only. No repository, service, API, or wiring exists yet (Slice 1 scope,
mirroring M8 Slice 1 exactly per the Architecture Contract's own Sec 28
exit condition); these tests exercise raw SQL against a real Postgres
instance the same way tests/test_m8_slice1_ome_schema.py does, since a
fake pool cannot faithfully exercise real FK/CHECK constraint
enforcement.

Known, accepted exception (Architecture Contract Sec 11.2 / 11.3, and
this migration's own header comment): ome_actions.assigned_user_id ->
users(id) is a plain, non-composite FK, because users has no
company_id column and every uniqueness index on memberships is
partial - neither can be used as an FK target. That relationship is
therefore NOT DB-enforced for tenant safety at Slice 1;
same-company active-membership validation is an explicit,
Founder-ratified Slice 2 domain-service responsibility, not a database
constraint. test_assignee_from_another_company_is_not_rejected_by_db
proves and records this fact explicitly rather than silently assuming
it away, mirroring how test_m8_slice1_ome_schema.py's own
test_cross_company_situation_link_is_a_documented_gap treats the
migration 014 situation_id exception.
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import asyncpg
import pytest

from app.core.config import settings

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "migrations"


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=5)


async def _seed_company_and_user(conn: asyncpg.Connection, *, label: str) -> tuple[str, str]:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m9-s1-{label}-{uuid4().hex[:10]}", f"M9 Slice 1 Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m9-s1-{label}-{uuid4().hex[:10]}@example.com", f"M9 Slice 1 Test User {label}",
    )
    return str(company_id), str(user_id)


async def _seed_receipt(conn: asyncpg.Connection, *, company_id: str, user_id: str) -> str:
    receipt_id = await conn.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, $4::jsonb)
        RETURNING id
        """,
        company_id, user_id, '{"ceo_text": "test"}', '[]',
    )
    return str(receipt_id)


async def _seed_decision(
    conn: asyncpg.Connection, *, company_id: str, receipt_id: str, user_id: str
) -> str:
    decision_id = await conn.fetchval(
        """
        INSERT INTO ome_decision_memories
            (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
        VALUES ($1, $2, 'Test decision', $3, NOW())
        RETURNING id
        """,
        company_id, receipt_id, user_id,
    )
    return str(decision_id)


async def _seed_action(
    conn: asyncpg.Connection, *, company_id: str, decision_id: str, user_id: str
) -> str:
    action_id = await conn.fetchval(
        """
        INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id)
        VALUES ($1, $2, 'Test action', $3)
        RETURNING id
        """,
        company_id, decision_id, user_id,
    )
    return str(action_id)


async def _seed_full_chain(conn: asyncpg.Connection, *, label: str) -> tuple[str, str, str, str, str]:
    """Return (company_id, user_id, receipt_id, decision_id, action_id)."""
    company_id, user_id = await _seed_company_and_user(conn, label=label)
    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
    action_id = await _seed_action(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
    return company_id, user_id, receipt_id, decision_id, action_id


async def _cleanup_chain(
    conn: asyncpg.Connection, *, company_id: str, user_id: str, receipt_id: str, decision_id: str, action_id: str
) -> None:
    await conn.execute("DELETE FROM ome_action_change_events WHERE action_id=$1", action_id)
    await conn.execute("DELETE FROM ome_actions WHERE id=$1", action_id)
    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)


# Each test cleans up its own rows inline, in FK-safe order, immediately
# after its assertion - no shared cleanup helper, so a failed assertion
# in one test can never leave rows that mask another test's result.


# ---------------------------------------------------------------------------
# 1. Migration applies / migration inventory integrity
# ---------------------------------------------------------------------------

def test_migration_015_file_exists_and_is_next_after_014() -> None:
    files = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert files[-1] == "015_decision_execution_foundation.sql"
    assert files == [f"{i:03d}_{files[i - 1].split('_', 1)[1]}" for i in range(1, len(files) + 1)]


def test_migration_runner_applies_015_and_leaves_001_014_untouched(db_available) -> None:
    """Re-running the real migration runner must report 015 as already
    applied (idempotent) and must NOT raise a checksum-mismatch error
    for 001-014 - migrate.py's own validate_applied_migration raises
    RuntimeError precisely when a previously-applied migration's file
    no longer matches its recorded checksum, so a clean run here is
    direct proof 001-014 were not modified by this slice."""
    from scripts.migrate import run_migrations

    _run(run_migrations())  # raises on any checksum mismatch or failure


def test_changed_at_default_is_clock_timestamp_not_now() -> None:
    """DB-independent guard (Issue 3): the migration file itself must
    default changed_at to clock_timestamp(), never NOW()/CURRENT_TIMESTAMP
    - a regression here would silently reintroduce the transaction-start-
    time audit-ordering bug without needing a live database to notice."""
    sql = (MIGRATIONS_DIR / "015_decision_execution_foundation.sql").read_text(encoding="utf-8")
    changed_at_line = next(line for line in sql.splitlines() if "changed_at" in line and "DEFAULT" in line)
    assert "clock_timestamp()" in changed_at_line
    assert "NOW()" not in changed_at_line


def test_schema_migrations_row_recorded_for_015(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            row = await pool.fetchrow(
                "SELECT version, filename, checksum FROM schema_migrations WHERE version = '015'"
            )
            return row
        finally:
            await pool.close()

    row = _run(scenario())
    assert row is not None
    assert row["filename"] == "015_decision_execution_foundation.sql"
    expected_checksum = hashlib.sha256(
        (MIGRATIONS_DIR / "015_decision_execution_foundation.sql").read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    assert row["checksum"] == expected_checksum


# ---------------------------------------------------------------------------
# 2. Both tables exist
# ---------------------------------------------------------------------------

def test_both_action_tables_exist(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            rows = await pool.fetch(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = ANY($1)
                """,
                ["ome_actions", "ome_action_change_events"],
            )
            return {r["table_name"] for r in rows}
        finally:
            await pool.close()

    found = _run(scenario())
    assert found == {"ome_actions", "ome_action_change_events"}


# ---------------------------------------------------------------------------
# 3. Required FKs / NOT NULL attribution
# ---------------------------------------------------------------------------

def test_action_requires_valid_company_fk(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id)
                        VALUES ($1, $2, 'x', $3)
                        """,
                        str(uuid4()), str(uuid4()), str(uuid4()),
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_action_created_by_user_id_cannot_be_null(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="attr")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.NotNullViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id)
                            VALUES ($1, $2, 'x', NULL)
                            """,
                            company_id, decision_id,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_action_requires_existing_decision(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="nodec")
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id)
                            VALUES ($1, $2, 'x', $3)
                            """,
                            company_id, str(uuid4()), user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_change_event_requires_existing_action(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="noaction")
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'status', 'pending', $3)
                            """,
                            company_id, str(uuid4()), user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 4. Cross-company links rejected at DB level (composite FK)
# ---------------------------------------------------------------------------

def test_cross_company_action_to_decision_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="a")
                company_b, user_b = await _seed_company_and_user(conn, label="b")
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id)
                            VALUES ($1, $2, 'x', $3)
                            """,
                            company_b, decision_a, user_b,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_a)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_a)
                    for cid, uid in ((company_a, user_a), (company_b, user_b)):
                        await conn.execute("DELETE FROM users WHERE id=$1", uid)
                        await conn.execute("DELETE FROM companies WHERE id=$1", cid)
        finally:
            await pool.close()

    _run(scenario())


def test_cross_company_change_event_to_action_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a, receipt_a, decision_a, action_a = await _seed_full_chain(conn, label="cea")
                company_b, user_b = await _seed_company_and_user(conn, label="ceb")
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'status', 'pending', $3)
                            """,
                            company_b, action_a, user_b,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_a, user_id=user_a, receipt_id=receipt_a,
                        decision_id=decision_a, action_id=action_a,
                    )
                    await conn.execute("DELETE FROM users WHERE id=$1", user_b)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_b)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 5. assigned_user_id: documented tenant-safety gap (Sec 11.2)
# ---------------------------------------------------------------------------

def test_assignee_from_another_company_is_not_rejected_by_db(db_available) -> None:
    """Documented, Founder-ratified gap (Architecture Contract Sec 11.2 /
    11.3): assigned_user_id is a PLAIN FK to users(id), with no
    composite tenant guard available (users has no company_id; every
    memberships uniqueness index is partial). A cross-company assignee
    is therefore NOT rejected at the database level - only a Slice 2
    domain-service check (MembershipRepository.get_active_membership)
    can catch this. This test proves and records that fact rather than
    silently assuming it away, so nobody mistakes the absence of a
    later regression test for the absence of the gap."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a, receipt_a, decision_a, action_a = await _seed_full_chain(conn, label="assa")
                company_b, user_b = await _seed_company_and_user(conn, label="assb")
                try:
                    updated_id = await conn.fetchval(
                        "UPDATE ome_actions SET assigned_user_id=$1 WHERE id=$2 RETURNING id",
                        user_b, action_a,
                    )
                    assert str(updated_id) == action_a
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_a, user_id=user_a, receipt_id=receipt_a,
                        decision_id=decision_a, action_id=action_a,
                    )
                    await conn.execute("DELETE FROM users WHERE id=$1", user_b)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_b)
        finally:
            await pool.close()

    _run(scenario())


def test_action_requires_existing_assigned_user(db_available) -> None:
    """The database DOES prove the assigned user exists (plain FK),
    even though it cannot prove same-company membership."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="exist")
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            "UPDATE ome_actions SET assigned_user_id=$1 WHERE id=$2",
                            str(uuid4()), action_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 6. Status enum / title non-blank
# ---------------------------------------------------------------------------

def test_invalid_action_status_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, _ = await _seed_full_chain(conn, label="stat")
                await conn.execute("DELETE FROM ome_actions WHERE company_id=$1", company_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id, status)
                            VALUES ($1, $2, 'x', $3, 'bogus')
                            """,
                            company_id, decision_id, user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_blank_action_title_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, _ = await _seed_full_chain(conn, label="blank")
                await conn.execute("DELETE FROM ome_actions WHERE company_id=$1", company_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_actions (company_id, decision_memory_id, title, created_by_user_id)
                            VALUES ($1, $2, '   ', $3)
                            """,
                            company_id, decision_id, user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 7. Terminal timestamp CHECK consistency
# ---------------------------------------------------------------------------

def test_completed_action_requires_completed_at(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="c1")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            "UPDATE ome_actions SET status='completed' WHERE id=$1", action_id
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_pending_action_with_completed_at_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="c2")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            "UPDATE ome_actions SET completed_at=NOW() WHERE id=$1", action_id
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_cancelled_action_requires_cancelled_at(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="c3")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            "UPDATE ome_actions SET status='cancelled' WHERE id=$1", action_id
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_completed_action_with_completed_at_succeeds(db_available) -> None:
    """Positive control: a consistent completed transition succeeds."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="ok1")
                try:
                    row = await conn.fetchrow(
                        "UPDATE ome_actions SET status='completed', completed_at=NOW() WHERE id=$1 RETURNING status",
                        action_id,
                    )
                    assert row["status"] == "completed"
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 8. ome_action_change_events discriminated shape CHECK
# ---------------------------------------------------------------------------

def test_status_event_with_assignment_fields_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="mix1")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, to_status, to_assigned_user_id, changed_by_user_id)
                            VALUES ($1, $2, 'status', 'in_progress', $3, $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_assignment_event_with_status_fields_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="mix2")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, to_status, to_assigned_user_id, changed_by_user_id)
                            VALUES ($1, $2, 'assignment', 'pending', $3, $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_status_event_missing_to_status_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="miss1")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, changed_by_user_id)
                            VALUES ($1, $2, 'status', $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_fake_null_to_null_assignment_event_rejected(db_available) -> None:
    """Do NOT create a fake NULL -> NULL assignment event when an Action
    is created unassigned."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="fakeasn")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, changed_by_user_id)
                            VALUES ($1, $2, 'assignment', $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_invalid_change_type_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="ctype")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'bogus', 'pending', $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_invalid_from_status_rejected(db_available) -> None:
    """Issue 2 correction: from_status must be constrained to the M9
    status vocabulary at the database boundary too, not just to_status."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="badfrom")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'status', 'bogus', 'in_progress', $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


@pytest.mark.parametrize("from_status", ["pending", "in_progress", "completed", "cancelled"])
def test_valid_from_status_succeeds(db_available, from_status: str) -> None:
    """Positive control: every valid M9 status succeeds as from_status,
    so long as the event shape is otherwise valid."""
    to_status = "cancelled" if from_status != "cancelled" else "completed"

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(
                    conn, label=f"okfrom{from_status[:3]}"
                )
                try:
                    event_id = await conn.fetchval(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                        VALUES ($1, $2, 'status', $3, $4, $5)
                        RETURNING id
                        """,
                        company_id, action_id, from_status, to_status, user_id,
                    )
                    assert event_id is not None
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_self_transition_status_event_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="selft")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'status', 'pending', 'pending', $3)
                            """,
                            company_id, action_id, user_id,
                        )
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 9. Happy path: initial status event + genuine transition + assignment
# ---------------------------------------------------------------------------

def test_initial_status_event_persistence_path(db_available) -> None:
    """NULL -> pending, written for a freshly created Action."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="init1")
                try:
                    event_id = await conn.fetchval(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                        VALUES ($1, $2, 'status', NULL, 'pending', $3)
                        RETURNING id
                        """,
                        company_id, action_id, user_id,
                    )
                    assert event_id is not None
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_initial_assignment_event_persistence_path_when_assigned(db_available) -> None:
    """NULL -> assigned_user_id, for an Action created with an assignee."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="init2")
                try:
                    await conn.execute(
                        "UPDATE ome_actions SET assigned_user_id=$1 WHERE id=$2", user_id, action_id
                    )
                    event_id = await conn.fetchval(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_assigned_user_id, to_assigned_user_id, changed_by_user_id)
                        VALUES ($1, $2, 'assignment', NULL, $3, $3)
                        RETURNING id
                        """,
                        company_id, action_id, user_id,
                    )
                    assert event_id is not None
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_full_status_and_assignment_ledger_chronological_read(db_available) -> None:
    """The unified timeline read: status and assignment events for one
    Action, both readable from one table.

    Ordering note (Issue 6, refined after independent re-review):
    `ORDER BY changed_at ASC, id ASC` here is a DETERMINISTIC DISPLAY
    order only (a stable read for pagination/rendering, matching the
    tie-break style already used by
    DecisionMemoryRepository.list_by_situation). It is NOT a claim that
    `id` proves causal order - UUIDs (gen_random_uuid(), v4) carry no
    temporal information and must never be read as a sequence.

    changed_at (clock_timestamp()) is NOT a strict monotonic causal
    sequence either - it avoids the specific NOW()-based transaction-
    start inversion risk this correction pass identified, and it
    improves audit-time fidelity, but the underlying wall clock can
    still tie at practical resolution or step backward. The three
    events below read back in insertion order below because they are
    three sequential, non-concurrent statement executions on one
    connection - a natural consequence of real elapsed time between
    ordinary statements, not a claim about how concurrent, row-locked
    transactions would serialize. The authoritative evidence for what
    happened, in what prior state, is the ledger's persisted
    from-state/to-state values themselves, not changed_at.
    """

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="chrono")
                try:
                    await conn.execute(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                        VALUES ($1, $2, 'status', NULL, 'pending', $3)
                        """,
                        company_id, action_id, user_id,
                    )
                    await conn.execute(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                        VALUES ($1, $2, 'status', 'pending', 'in_progress', $3)
                        """,
                        company_id, action_id, user_id,
                    )
                    await conn.execute(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_assigned_user_id, to_assigned_user_id, changed_by_user_id)
                        VALUES ($1, $2, 'assignment', NULL, $3, $3)
                        """,
                        company_id, action_id, user_id,
                    )
                    rows = await conn.fetch(
                        """
                        SELECT change_type, from_status, to_status, to_assigned_user_id
                        FROM ome_action_change_events
                        WHERE company_id = $1 AND action_id = $2
                        ORDER BY changed_at ASC, id ASC
                        """,
                        company_id, action_id,
                    )
                    assert [r["change_type"] for r in rows] == ["status", "status", "assignment"]
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_changed_at_uses_statement_time_not_transaction_start(db_available) -> None:
    """Demonstrates the specific PostgreSQL function-semantics
    difference this correction relies on: within ONE transaction, two
    INSERTs separated by a real delay (pg_sleep) show that
    clock_timestamp() is evaluated at each statement's execution time,
    not frozen at transaction BEGIN like NOW()/CURRENT_TIMESTAMP would
    be. With NOW(), both rows would share the exact same frozen
    transaction-start timestamp regardless of the delay between them -
    this test would fail against that implementation, which is exactly
    the inversion risk this correction removes.

    This is NOT a concurrency test and proves NO claim about how two
    separate, lock-racing transactions would order relative to each
    other, nor a claim of strict monotonicity in general (a backward
    system-clock step or a same-resolution tie remain possible outside
    this controlled, single-transaction, real-delay scenario). It
    proves only the function-evaluation-time difference itself."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="clockts")
                try:
                    async with conn.transaction():
                        first_id = await conn.fetchval(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'status', NULL, 'pending', $3)
                            RETURNING id
                            """,
                            company_id, action_id, user_id,
                        )
                        await conn.execute("SELECT pg_sleep(0.05)")
                        second_id = await conn.fetchval(
                            """
                            INSERT INTO ome_action_change_events
                                (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                            VALUES ($1, $2, 'status', 'pending', 'in_progress', $3)
                            RETURNING id
                            """,
                            company_id, action_id, user_id,
                        )

                    first_ts = await conn.fetchval(
                        "SELECT changed_at FROM ome_action_change_events WHERE id = $1", first_id
                    )
                    second_ts = await conn.fetchval(
                        "SELECT changed_at FROM ome_action_change_events WHERE id = $1", second_id
                    )
                    assert second_ts > first_ts
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_full_decision_action_chain_persists(db_available) -> None:
    """Happy path: the full receipt -> decision -> action chain persists
    and is queryable through a JOIN, matching the M8 precedent's own
    full-chain test."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id, receipt_id, decision_id, action_id = await _seed_full_chain(conn, label="happy")
                try:
                    row = await conn.fetchrow(
                        """
                        SELECT a.id AS action_id, d.id AS decision_id, r.id AS receipt_id
                        FROM ome_actions a
                        JOIN ome_decision_memories d ON d.id = a.decision_memory_id
                        JOIN ome_reasoning_receipts r ON r.id = d.reasoning_receipt_id
                        WHERE a.id = $1
                        """,
                        action_id,
                    )
                    assert row is not None
                    assert str(row["action_id"]) == action_id
                    assert str(row["decision_id"]) == decision_id
                    assert str(row["receipt_id"]) == receipt_id
                finally:
                    await _cleanup_chain(
                        conn, company_id=company_id, user_id=user_id, receipt_id=receipt_id,
                        decision_id=decision_id, action_id=action_id,
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_one_decision_supports_multiple_actions(db_available) -> None:
    """DecisionMemory 1 -> N Action (Architecture Contract Sec 6)."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="multi")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                action_1 = await _seed_action(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                action_2 = await _seed_action(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                try:
                    rows = await conn.fetch(
                        "SELECT id FROM ome_actions WHERE decision_memory_id = $1 ORDER BY created_at", decision_id
                    )
                    assert {str(r["id"]) for r in rows} == {action_1, action_2}
                finally:
                    await conn.execute("DELETE FROM ome_actions WHERE decision_memory_id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())
