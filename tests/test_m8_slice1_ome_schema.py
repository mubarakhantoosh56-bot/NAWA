"""M8 Slice 1: OME persistence-foundation schema contract tests.

Proves migrations/014_organizational_memory.sql's three tables
(ome_reasoning_receipts, ome_decision_memories, ome_outcome_memories)
exist with the required FKs, CHECK constraints, and tenant-safe composite
FK behavior - schema-level only. No repository, service, API, retrieval,
or live-reasoning code exists yet (Slice 1 scope); these tests exercise
raw SQL against a real Postgres instance the same way
tests/test_memory_fact_conflict.py does, since a fake pool cannot
faithfully exercise real FK/CHECK constraint enforcement.

Known, accepted exception (see migrations/014_organizational_memory.sql's
own header comment and the M8 OME Provenance Integrity Decision):
ome_decision_memories.situation_id -> operational_situations(id) is a
plain, non-composite FK, because operational_situations (frozen as of
M7) has no UNIQUE(id, company_id) to compose against. That one
relationship is therefore NOT DB-enforced for tenant safety -
test_cross_company_situation_link_is_a_documented_gap proves and records
this fact explicitly rather than silently assuming it away.
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
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
        f"m8-s1-{label}-{uuid4().hex[:10]}", f"M8 Slice 1 Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s1-{label}-{uuid4().hex[:10]}@example.com", f"M8 Slice 1 Test User {label}",
    )
    return str(company_id), str(user_id)


async def _seed_situation(conn: asyncpg.Connection, *, company_id: str) -> str:
    now = datetime.now(timezone.utc)
    situation_id = await conn.fetchval(
        """
        INSERT INTO operational_situations
            (company_id, title, summary, situation_type, severity, status,
             time_window_start, time_window_end, detection_method, source_type)
        VALUES ($1, 'Test situation', 'Test summary', 'anomaly', 'low', 'active', $2, $3, 'rule_based', 'manual_rule')
        RETURNING id
        """,
        company_id, now - timedelta(hours=1), now,
    )
    return str(situation_id)


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


# Each test cleans up its own rows inline, in FK-safe order, immediately
# after its assertion - no shared cleanup helper, so a failed assertion in
# one test can never leave rows that mask another test's result.


# ---------------------------------------------------------------------------
# 1. Migration applies / migration inventory integrity
# ---------------------------------------------------------------------------

def test_migration_014_exists_in_contiguous_sequence() -> None:
    """M8 boundary invariant: migration 014 exists, and the full
    migration sequence remains contiguously numbered with no gaps or
    renumbering. (Historical note: this test was originally named
    test_migration_014_file_exists_and_is_next_after_013 and asserted
    014 was the LAST migration file; that assertion became obsolete
    once Founder-approved M9 Slice 1 added migration 015 - M8's real
    invariant was always that 001-014 remain intact and contiguously
    numbered, not that no future milestone may ever add a migration
    after 014.)"""
    files = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert "014_organizational_memory.sql" in files
    assert files == [f"{i:03d}_{files[i - 1].split('_', 1)[1]}" for i in range(1, len(files) + 1)]


def test_migration_runner_applies_014_and_leaves_001_013_untouched(db_available) -> None:
    """Re-running the real migration runner must report 014 as already
    applied (idempotent) and must NOT raise a checksum-mismatch error for
    001-013 - migrate.py's own validate_applied_migration raises
    RuntimeError precisely when a previously-applied migration's file no
    longer matches its recorded checksum, so a clean run here is direct
    proof 001-013 were not modified by this slice."""
    from scripts.migrate import run_migrations

    _run(run_migrations())  # raises on any checksum mismatch or failure


def test_schema_migrations_row_recorded_for_014(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            row = await pool.fetchrow(
                "SELECT version, filename, checksum FROM schema_migrations WHERE version = '014'"
            )
            return row
        finally:
            await pool.close()

    row = _run(scenario())
    assert row is not None
    assert row["filename"] == "014_organizational_memory.sql"
    expected_checksum = hashlib.sha256(
        (MIGRATIONS_DIR / "014_organizational_memory.sql").read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    assert row["checksum"] == expected_checksum


# ---------------------------------------------------------------------------
# 2. All three tables exist
# ---------------------------------------------------------------------------

def test_all_three_ome_tables_exist(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            rows = await pool.fetch(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = ANY($1)
                """,
                ["ome_reasoning_receipts", "ome_decision_memories", "ome_outcome_memories"],
            )
            return {r["table_name"] for r in rows}
        finally:
            await pool.close()

    found = _run(scenario())
    assert found == {"ome_reasoning_receipts", "ome_decision_memories", "ome_outcome_memories"}


# ---------------------------------------------------------------------------
# 3/13. Required FKs and human attribution cannot be NULL
# ---------------------------------------------------------------------------

def test_receipt_requires_valid_company_and_user_fk(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO ome_reasoning_receipts
                            (company_id, created_by_user_id, response_snapshot)
                        VALUES ($1, $2, '{}'::jsonb)
                        """,
                        str(uuid4()), str(uuid4()),
                    )
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_created_by_user_id_cannot_be_null(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="attr")
                try:
                    with pytest.raises(asyncpg.NotNullViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_reasoning_receipts
                                (company_id, created_by_user_id, response_snapshot)
                            VALUES ($1, NULL, '{}'::jsonb)
                            """,
                            company_id,
                        )
                finally:
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_decided_by_user_id_cannot_be_null(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="attr2")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.NotNullViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
                            VALUES ($1, $2, 'x', NULL, NOW())
                            """,
                            company_id, receipt_id,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 4/5. Decision must reference a valid receipt; outcome a valid decision
# ---------------------------------------------------------------------------

def test_decision_requires_existing_receipt(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="noreceipt")
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
                            VALUES ($1, $2, 'x', $3, NOW())
                            """,
                            company_id, str(uuid4()), user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_requires_existing_decision(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="nodecision")
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_outcome_memories
                                (company_id, decision_memory_id, outcome_summary, result_state,
                                 recorded_by_user_id, observed_at)
                            VALUES ($1, $2, 'x', 'unknown', $3, NOW())
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
# 6/8/9. Cross-company links rejected at DB level (composite FK)
# ---------------------------------------------------------------------------

def test_cross_company_decision_to_receipt_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="a")
                company_b, user_b = await _seed_company_and_user(conn, label="b")
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
                            VALUES ($1, $2, 'x', $3, NOW())
                            """,
                            company_b, receipt_a, user_b,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_a)
                    for cid, uid in ((company_a, user_a), (company_b, user_b)):
                        await conn.execute("DELETE FROM users WHERE id=$1", uid)
                        await conn.execute("DELETE FROM companies WHERE id=$1", cid)
        finally:
            await pool.close()

    _run(scenario())


def test_cross_company_outcome_to_decision_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="a2")
                company_b, user_b = await _seed_company_and_user(conn, label="b2")
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_outcome_memories
                                (company_id, decision_memory_id, outcome_summary, result_state,
                                 recorded_by_user_id, observed_at)
                            VALUES ($1, $2, 'x', 'unknown', $3, NOW())
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


def test_cross_company_decision_supersession_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="a3")
                company_b, user_b = await _seed_company_and_user(conn, label="b3")
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            "UPDATE ome_decision_memories SET superseded_by=$1, status='superseded' WHERE id=$2",
                            decision_b, decision_a,
                        )
                finally:
                    for did in (decision_a, decision_b):
                        await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", did)
                    for rid in (receipt_a, receipt_b):
                        await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", rid)
                    for cid, uid in ((company_a, user_a), (company_b, user_b)):
                        await conn.execute("DELETE FROM users WHERE id=$1", uid)
                        await conn.execute("DELETE FROM companies WHERE id=$1", cid)
        finally:
            await pool.close()

    _run(scenario())


def test_cross_company_outcome_supersession_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="a4")
                company_b, user_b = await _seed_company_and_user(conn, label="b4")
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                outcome_a = await conn.fetchval(
                    """
                    INSERT INTO ome_outcome_memories
                        (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
                    VALUES ($1, $2, 'x', 'unknown', $3, NOW()) RETURNING id
                    """,
                    company_a, decision_a, user_a,
                )
                outcome_b = await conn.fetchval(
                    """
                    INSERT INTO ome_outcome_memories
                        (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
                    VALUES ($1, $2, 'x', 'unknown', $3, NOW()) RETURNING id
                    """,
                    company_b, decision_b, user_b,
                )
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            "UPDATE ome_outcome_memories SET superseded_by=$1, status='superseded' WHERE id=$2",
                            outcome_b, outcome_a,
                        )
                finally:
                    for oid in (outcome_a, outcome_b):
                        await conn.execute("DELETE FROM ome_outcome_memories WHERE id=$1", oid)
                    for did in (decision_a, decision_b):
                        await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", did)
                    for rid in (receipt_a, receipt_b):
                        await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", rid)
                    for cid, uid in ((company_a, user_a), (company_b, user_b)):
                        await conn.execute("DELETE FROM users WHERE id=$1", uid)
                        await conn.execute("DELETE FROM companies WHERE id=$1", cid)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 7. Decision -> situation IS tenant-safe (Codex-required fix)
# ---------------------------------------------------------------------------

def test_cross_company_decision_to_situation_is_rejected(db_available) -> None:
    """Codex-required fix: operational_situations now carries
    UNIQUE(id, company_id) (added by this migration, additive-only - see
    the migration's header comment), and
    fk_ome_decision_memories_situation_same_company FKs against that
    composite key. A decision referencing another company's situation
    must now be rejected at the database level, closing the gap the
    previous version of this test merely documented."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="sita")
                company_b, user_b = await _seed_company_and_user(conn, label="sitb")
                situation_b = await _seed_situation(conn, company_id=company_b)
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, situation_id, decision_text, decided_by_user_id, decided_at)
                            VALUES ($1, $2, $3, 'x', $4, NOW())
                            """,
                            company_a, receipt_a, situation_b, user_a,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_a)
                    await conn.execute("DELETE FROM operational_situations WHERE id=$1", situation_b)
                    for cid, uid in ((company_a, user_a), (company_b, user_b)):
                        await conn.execute("DELETE FROM users WHERE id=$1", uid)
                        await conn.execute("DELETE FROM companies WHERE id=$1", cid)
        finally:
            await pool.close()

    _run(scenario())


def test_same_company_decision_to_situation_succeeds(db_available) -> None:
    """Positive control for the fix above: a same-company situation_id
    must still be usable."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="sitok")
                situation_id = await _seed_situation(conn, company_id=company_id)
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                try:
                    decision_id = await conn.fetchval(
                        """
                        INSERT INTO ome_decision_memories
                            (company_id, reasoning_receipt_id, situation_id, decision_text, decided_by_user_id, decided_at)
                        VALUES ($1, $2, $3, 'x', $4, NOW())
                        RETURNING id
                        """,
                        company_id, receipt_id, situation_id, user_id,
                    )
                    assert decision_id is not None
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE company_id=$1", company_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM operational_situations WHERE id=$1", situation_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Supersession status/superseded_by consistency invariant (Codex-required)
# ---------------------------------------------------------------------------

def test_decision_active_with_superseded_by_set_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dinv1")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_1 = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at,
                                 status, superseded_by)
                            VALUES ($1, $2, 'x', $3, NOW(), 'active', $4)
                            """,
                            company_id, receipt_id, user_id, decision_1,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_1)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_superseded_with_superseded_by_null_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dinv2")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at, status)
                            VALUES ($1, $2, 'x', $3, NOW(), 'superseded')
                            """,
                            company_id, receipt_id, user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_supersession_round_trip_succeeds(db_available) -> None:
    """Positive control: a consistent active->superseded transition, with
    superseded_by correctly set, must succeed."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dinvok")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                old_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                new_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    await conn.execute(
                        "UPDATE ome_decision_memories SET status='superseded', superseded_by=$1 WHERE id=$2",
                        new_decision, old_decision,
                    )
                    row = await conn.fetchrow(
                        "SELECT status, superseded_by FROM ome_decision_memories WHERE id=$1", old_decision
                    )
                    assert row["status"] == "superseded"
                    assert str(row["superseded_by"]) == new_decision
                finally:
                    for did in (old_decision, new_decision):
                        await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", did)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_active_with_superseded_by_set_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="oinv1")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                outcome_1 = await conn.fetchval(
                    """
                    INSERT INTO ome_outcome_memories
                        (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
                    VALUES ($1, $2, 'x', 'unknown', $3, NOW()) RETURNING id
                    """,
                    company_id, decision_id, user_id,
                )
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_outcome_memories
                                (company_id, decision_memory_id, outcome_summary, result_state,
                                 recorded_by_user_id, observed_at, status, superseded_by)
                            VALUES ($1, $2, 'x', 'unknown', $3, NOW(), 'active', $4)
                            """,
                            company_id, decision_id, user_id, outcome_1,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_outcome_memories WHERE id=$1", outcome_1)
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_superseded_with_superseded_by_null_is_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="oinv2")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_outcome_memories
                                (company_id, decision_memory_id, outcome_summary, result_state,
                                 recorded_by_user_id, observed_at, status)
                            VALUES ($1, $2, 'x', 'unknown', $3, NOW(), 'superseded')
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
# Supersession delete-action fix (Codex-required): a row still referenced
# as another row's superseded_by must not be deletable.
# ---------------------------------------------------------------------------

def test_referenced_decision_cannot_be_deleted(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="nodel")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                old_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                new_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                await conn.execute(
                    "UPDATE ome_decision_memories SET status='superseded', superseded_by=$1 WHERE id=$2",
                    new_decision, old_decision,
                )
                try:
                    with pytest.raises(asyncpg.ForeignKeyViolationError):
                        await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", new_decision)
                finally:
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", old_decision)
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", new_decision)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# 10/11. Invalid status / result_state rejected
# ---------------------------------------------------------------------------

def test_invalid_decision_status_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="stat")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_decision_memories
                                (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at, status)
                            VALUES ($1, $2, 'x', $3, NOW(), 'bogus')
                            """,
                            company_id, receipt_id, user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_invalid_outcome_result_state_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="res")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_outcome_memories
                                (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
                            VALUES ($1, $2, 'x', 'bogus', $3, NOW())
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


def test_invalid_outcome_status_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ostat")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_outcome_memories
                                (company_id, decision_memory_id, outcome_summary, result_state,
                                 recorded_by_user_id, observed_at, status)
                            VALUES ($1, $2, 'x', 'unknown', $3, NOW(), 'bogus')
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
# 12. evidence_refs must be a JSON array
# ---------------------------------------------------------------------------

def test_receipt_evidence_refs_must_be_json_array(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="arr")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_reasoning_receipts
                                (company_id, created_by_user_id, response_snapshot, evidence_refs)
                            VALUES ($1, $2, '{}'::jsonb, '{"not": "an array"}'::jsonb)
                            """,
                            company_id, user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_response_snapshot_must_be_json_object(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="obj")
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            """
                            INSERT INTO ome_reasoning_receipts
                                (company_id, created_by_user_id, response_snapshot)
                            VALUES ($1, $2, '[1, 2, 3]'::jsonb)
                            """,
                            company_id, user_id,
                        )
                finally:
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Bonus: no self-supersession
# ---------------------------------------------------------------------------

def test_decision_cannot_supersede_itself(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="self")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                try:
                    with pytest.raises(asyncpg.CheckViolationError):
                        await conn.execute(
                            "UPDATE ome_decision_memories SET superseded_by=$1 WHERE id=$1",
                            decision_id,
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
# Happy path: the full receipt -> decision -> outcome chain persists
# ---------------------------------------------------------------------------

def test_full_receipt_decision_outcome_chain_persists(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="happy")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                outcome_id = await conn.fetchval(
                    """
                    INSERT INTO ome_outcome_memories
                        (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
                    VALUES ($1, $2, 'It worked', 'positive', $3, NOW())
                    RETURNING id
                    """,
                    company_id, decision_id, user_id,
                )
                row = await conn.fetchrow(
                    """
                    SELECT o.id AS outcome_id, d.id AS decision_id, r.id AS receipt_id
                    FROM ome_outcome_memories o
                    JOIN ome_decision_memories d ON d.id = o.decision_memory_id
                    JOIN ome_reasoning_receipts r ON r.id = d.reasoning_receipt_id
                    WHERE o.id = $1
                    """,
                    outcome_id,
                )
                try:
                    assert row is not None
                    assert str(row["outcome_id"]) == str(outcome_id)
                    assert str(row["decision_id"]) == str(decision_id)
                    assert str(row["receipt_id"]) == str(receipt_id)
                finally:
                    await conn.execute("DELETE FROM ome_outcome_memories WHERE id=$1", outcome_id)
                    await conn.execute("DELETE FROM ome_decision_memories WHERE id=$1", decision_id)
                    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE id=$1", receipt_id)
                    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())
