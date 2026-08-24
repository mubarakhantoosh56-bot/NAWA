"""M8 Slice 4A: Organizational Memory Retrieval Foundation tests (real
Postgres).

BACKEND-ONLY, DORMANT, READ-ONLY. Proves: outcome-backed eligibility
(Founder Correction 1), exact-situation vs bounded company-wide retrieval
modes with no similarity claims (Founder Correction 2), durable pointer
preservation with zero receipt-content leakage (Founder Correction 3), no
text truncation (Founder Correction 4), deterministic ordering/tie-breaks,
tenant isolation, superseded-record exclusion, limit validation, and
dormancy (no live /ai/chat wiring).

Required-fix round (Codex pre-commit review): every DB-mutating test now
seeds/cleans up through the `_company_scope`/`_two_company_scope` async
context managers below, whose cleanup runs in a `finally` around `yield` -
so it executes even when an assertion inside the test body raises,
never only on the happy path. This replaces the earlier
seed/assert/cleanup-after-assert pattern in this file.
"""
from __future__ import annotations

import asyncio
import dataclasses
import pathlib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.ome.errors import InvalidMemoryInput
from app.ome.models.organizational_memory_context import (
    OrganizationalMemoryContextItem,
    OrganizationalMemoryOutcomeContext,
)
from app.ome.repositories.decision_memory_repository import (
    MAX_LIST_LIMIT,
    DecisionMemoryRepository,
)
from app.ome.services.organizational_memory_retrieval_service import (
    DEFAULT_LIMIT,
    OrganizationalMemoryRetrievalService,
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=6)


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------

async def _seed_company_and_user(conn: asyncpg.Connection, *, label: str) -> tuple[str, str]:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m8-s4a-{label}-{uuid4().hex[:10]}", f"M8 Slice 4A Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s4a-{label}-{uuid4().hex[:10]}@example.com", f"M8 Slice 4A Test User {label}",
    )
    return str(company_id), str(user_id)


async def _seed_receipt(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    user_id: str,
    response_snapshot: str = '{"ceo_text": "test"}',
) -> str:
    receipt_id = await conn.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, '[]'::jsonb)
        RETURNING id
        """,
        company_id, user_id, response_snapshot,
    )
    return str(receipt_id)


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


async def _seed_decision(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    receipt_id: str,
    user_id: str,
    situation_id: str | None = None,
    decision_text: str = "Test decision",
    rationale: str | None = None,
    decided_at: datetime | None = None,
) -> str:
    decision_id = await conn.fetchval(
        """
        INSERT INTO ome_decision_memories
            (company_id, reasoning_receipt_id, situation_id, decision_text, rationale, decided_by_user_id, decided_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        company_id, receipt_id, situation_id, decision_text, rationale, user_id,
        decided_at or datetime.now(timezone.utc),
    )
    return str(decision_id)


async def _seed_outcome(
    conn: asyncpg.Connection,
    *,
    company_id: str,
    decision_id: str,
    user_id: str,
    result_state: str = "positive",
    outcome_summary: str = "Test outcome",
    observed_at: datetime | None = None,
) -> str:
    outcome_id = await conn.fetchval(
        """
        INSERT INTO ome_outcome_memories
            (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """,
        company_id, decision_id, outcome_summary, result_state, user_id,
        observed_at or datetime.now(timezone.utc),
    )
    return str(outcome_id)


async def _supersede_outcome(conn: asyncpg.Connection, *, old_outcome_id: str, new_outcome_id: str) -> None:
    await conn.execute(
        "UPDATE ome_outcome_memories SET status = 'superseded', superseded_by = $2 WHERE id = $1",
        old_outcome_id, new_outcome_id,
    )


async def _supersede_decision(conn: asyncpg.Connection, *, old_decision_id: str, new_decision_id: str) -> None:
    await conn.execute(
        "UPDATE ome_decision_memories SET status = 'superseded', superseded_by = $2 WHERE id = $1",
        old_decision_id, new_decision_id,
    )


async def _wipe_company(conn: asyncpg.Connection, company_id: str) -> None:
    await conn.execute("DELETE FROM ome_outcome_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_decision_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM operational_situations WHERE company_id=$1", company_id)


async def _cleanup(conn: asyncpg.Connection, *, company_id: str, user_id: str) -> None:
    # FK-safe order: outcomes -> decisions -> receipts -> situations -> user
    # -> company. Exact-row-scoped only - never a broad DELETE, never
    # touches any other company (including the known historical
    # m7-golden-7af9db72da).
    await _wipe_company(conn, company_id)
    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)


# ---------------------------------------------------------------------------
# Failure-safe test scope (Codex fix 2): cleanup runs in `finally` around
# `yield`, so it executes even when an assertion inside the `async with`
# block raises - not only on the happy path.
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _company_scope(pool: asyncpg.Pool, *, label: str):
    async with pool.acquire() as conn:
        company_id, user_id = await _seed_company_and_user(conn, label=label)
    try:
        yield company_id, user_id
    finally:
        async with pool.acquire() as conn:
            await _cleanup(conn, company_id=company_id, user_id=user_id)


@asynccontextmanager
async def _two_company_scope(pool: asyncpg.Pool, *, label_a: str, label_b: str):
    """Nested company scopes for cross-tenant tests - each company's
    cleanup is independently guaranteed by its own _company_scope, so a
    failure while company B is being set up still cleans up company A."""
    async with _company_scope(pool, label=label_a) as (company_a, user_a):
        async with _company_scope(pool, label=label_b) as (company_b, user_b):
            yield (company_a, user_a), (company_b, user_b)


# ---------------------------------------------------------------------------
# Eligibility (items 1-3)
# ---------------------------------------------------------------------------

def test_empty_company_history_returns_empty_list(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="empty") as (company_id, user_id):
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert result == []
        finally:
            await pool.close()

    _run(scenario())


def test_decision_with_zero_outcomes_excluded(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="zerooutcome") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert result == []
        finally:
            await pool.close()

    _run(scenario())


def test_decision_with_explicit_unknown_outcome_included(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="unknown") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    outcome_id = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        result_state="unknown",
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                assert result[0].decision_memory_id == UUID(decision_id)
                assert len(result[0].outcomes) == 1
                assert result[0].outcomes[0].outcome_memory_id == UUID(outcome_id)
                assert result[0].outcomes[0].result_state == "unknown"
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Aggregate correctness (items 4, 7, 25)
# ---------------------------------------------------------------------------

def test_single_decision_single_outcome_aggregate_correct(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="aggregate") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    situation_id = await _seed_situation(conn, company_id=company_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=situation_id, decision_text="Approve the expansion plan.",
                        rationale="Cash coverage supports it.",
                    )
                    outcome_id = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        result_state="positive", outcome_summary="Expansion delivered a lift.",
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                item = result[0]
                assert item.decision_memory_id == UUID(decision_id)
                assert item.reasoning_receipt_id == UUID(receipt_id)
                assert item.situation_id == UUID(situation_id)
                assert item.decision_text == "Approve the expansion plan."
                assert item.rationale == "Cash coverage supports it."
                assert len(item.outcomes) == 1
                assert item.outcomes[0].outcome_memory_id == UUID(outcome_id)
                assert item.outcomes[0].outcome_summary == "Expansion delivered a lift."
                assert item.outcomes[0].result_state == "positive"
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Tenant isolation (items 5, 6)
# ---------------------------------------------------------------------------

def test_cross_company_isolation(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _two_company_scope(pool, label_a="isoA", label_b="isoB") as (
                (company_a, user_a),
                (company_b, user_b),
            ):
                async with pool.acquire() as conn:
                    receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                    receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                    decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                    decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                    await _seed_outcome(conn, company_id=company_a, decision_id=decision_a, user_id=user_a)
                    await _seed_outcome(conn, company_id=company_b, decision_id=decision_b, user_id=user_b)
                service = OrganizationalMemoryRetrievalService(pool)
                result_a = await service.retrieve(company_id=UUID(company_a))
                result_b = await service.retrieve(company_id=UUID(company_b))
                assert [item.decision_memory_id for item in result_a] == [UUID(decision_a)]
                assert [item.decision_memory_id for item in result_b] == [UUID(decision_b)]
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Multiple outcomes: preservation, chronological ordering, no collapsing
# (items 8, 9, 11)
# ---------------------------------------------------------------------------

def test_multiple_active_outcomes_preserved_and_chronologically_ordered(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="multi") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    now = datetime.now(timezone.utc)
                    t1 = now - timedelta(days=10)
                    t2 = now - timedelta(days=5)
                    # Seed the LATER outcome first so DB insertion order
                    # cannot coincidentally match chronological order - the
                    # service must re-sort, never trust insertion/repository
                    # order.
                    outcome_t2 = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        result_state="positive", outcome_summary="Later: delivered a real lift.", observed_at=t2,
                    )
                    outcome_t1 = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        result_state="mixed", outcome_summary="Earlier: mixed initial signal.", observed_at=t1,
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                outcomes = result[0].outcomes
                # item 11: NOT collapsed to the latest outcome alone.
                assert len(outcomes) == 2
                # item 9: chronological, oldest first - "mixed at T1,
                # positive at T2" progression preserved exactly, never
                # reordered/summarized.
                assert outcomes[0].outcome_memory_id == UUID(outcome_t1)
                assert outcomes[0].result_state == "mixed"
                assert outcomes[1].outcome_memory_id == UUID(outcome_t2)
                assert outcomes[1].result_state == "positive"
        finally:
            await pool.close()

    _run(scenario())


def test_equal_observed_at_tiebreak_by_outcome_id(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="obstie") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    shared_time = datetime.now(timezone.utc) - timedelta(days=1)
                    outcome_1 = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        observed_at=shared_time,
                    )
                    outcome_2 = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        observed_at=shared_time,
                    )
                expected_order = sorted([outcome_1, outcome_2])
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                actual_order = [str(outcome.outcome_memory_id) for outcome in result[0].outcomes]
                assert actual_order == expected_order
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Superseded records excluded by default (items 12, 13, 14)
# ---------------------------------------------------------------------------

def test_superseded_outcome_excluded_active_only_returned(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="supout") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    old_outcome = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        result_state="negative", observed_at=datetime.now(timezone.utc) - timedelta(days=3),
                    )
                    new_outcome = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        result_state="positive", observed_at=datetime.now(timezone.utc) - timedelta(days=1),
                    )
                    await _supersede_outcome(conn, old_outcome_id=old_outcome, new_outcome_id=new_outcome)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                assert [str(o.outcome_memory_id) for o in result[0].outcomes] == [new_outcome]
        finally:
            await pool.close()

    _run(scenario())


def test_superseded_decision_excluded(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="supdec") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    old_decision = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=old_decision, user_id=user_id)
                    new_decision = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=new_decision, user_id=user_id)
                    await _supersede_decision(conn, old_decision_id=old_decision, new_decision_id=new_decision)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert [str(item.decision_memory_id) for item in result] == [new_decision]
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Situation mode: exact match only, no similarity, no backfill (items 15, 16)
# ---------------------------------------------------------------------------

def test_situation_mode_exact_match_only_never_backfilled(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="situation") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    situation_1 = await _seed_situation(conn, company_id=company_id)
                    situation_2 = await _seed_situation(conn, company_id=company_id)

                    decision_in_s1 = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=situation_1,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_in_s1, user_id=user_id)

                    decision_in_s2 = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=situation_2,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_in_s2, user_id=user_id)

                    decision_no_situation = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id, situation_id=None,
                    )
                    await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_no_situation, user_id=user_id,
                    )

                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id), situation_id=UUID(situation_1))
                # item 15: exact match only.
                assert [str(item.decision_memory_id) for item in result] == [decision_in_s1]
                # item 16: never backfilled with situation_2's or the
                # no-situation decision's history, even though both are
                # outcome-backed.
                returned_ids = {str(item.decision_memory_id) for item in result}
                assert decision_in_s2 not in returned_ids
                assert decision_no_situation not in returned_ids
        finally:
            await pool.close()

    _run(scenario())


def test_situation_mode_returns_empty_when_no_match_even_if_company_wide_has_eligible(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="situationempty") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    # An eligible, outcome-backed decision exists
                    # company-wide...
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    # ...but no decision at all is bound to this exact
                    # situation.
                    empty_situation = await _seed_situation(conn, company_id=company_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id), situation_id=UUID(empty_situation))
                assert result == []
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Fix 1: exact-situation completeness beyond the first repository page
# ---------------------------------------------------------------------------

def test_exact_situation_paging_reaches_decision_beyond_first_page(db_available) -> None:
    """Regression test for Codex pre-commit finding 1: previously,
    list_by_situation was capped at MAX_LIST_LIMIT (50) rows with no way to
    reach anything beyond that page, so an outcome-backed decision seeded
    OLDER than 50 newer, zero-outcome decisions for the same exact
    situation would never be found - retrieve() would incorrectly return
    [] even though qualifying Organizational Memory existed. This seeds
    exactly MAX_LIST_LIMIT newer zero-outcome decisions (filling page 1
    entirely) plus one older, outcome-backed decision (landing on page 2),
    for the SAME exact situation, and proves both the repository's own
    offset paging and the service's retrieve() reach it."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="page2") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    situation_id = await _seed_situation(conn, company_id=company_id)

                    now = datetime.now(timezone.utc)
                    # MAX_LIST_LIMIT newer decisions, all zero-outcome -
                    # these exactly fill page 1 (offset 0, limit
                    # MAX_LIST_LIMIT) and none are eligible.
                    for i in range(MAX_LIST_LIMIT):
                        await _seed_decision(
                            conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                            situation_id=situation_id, decided_at=now - timedelta(hours=i),
                        )

                    # One OLDER decision, definitively outside page 1 by
                    # decided_at ordering, WITH an active outcome.
                    older_eligible_decision = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=situation_id, decided_at=now - timedelta(days=30),
                    )
                    eligible_outcome = await _seed_outcome(
                        conn, company_id=company_id, decision_id=older_eligible_decision, user_id=user_id,
                    )

                    # An unrelated company-wide (different situation)
                    # outcome-backed decision - must never appear in the
                    # exact-situation result.
                    other_situation = await _seed_situation(conn, company_id=company_id)
                    unrelated_decision = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=other_situation,
                    )
                    await _seed_outcome(
                        conn, company_id=company_id, decision_id=unrelated_decision, user_id=user_id,
                    )

                # Repository-level proof: page 2 (offset=MAX_LIST_LIMIT)
                # genuinely contains the older eligible decision - not just
                # an accidental correct answer at the service layer.
                decision_repo = DecisionMemoryRepository(pool)
                page_1 = await decision_repo.list_by_situation(
                    company_id=UUID(company_id), situation_id=UUID(situation_id),
                    include_superseded=False, limit=MAX_LIST_LIMIT, offset=0,
                )
                assert len(page_1) == MAX_LIST_LIMIT
                assert older_eligible_decision not in {str(d.id) for d in page_1}

                page_2 = await decision_repo.list_by_situation(
                    company_id=UUID(company_id), situation_id=UUID(situation_id),
                    include_superseded=False, limit=MAX_LIST_LIMIT, offset=MAX_LIST_LIMIT,
                )
                assert [str(d.id) for d in page_2] == [older_eligible_decision]

                # Service-level proof: retrieve() is NOT [] and finds the
                # older eligible decision with its outcome preserved.
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(
                    company_id=UUID(company_id), situation_id=UUID(situation_id), limit=5,
                )
                assert result != []
                assert [str(item.decision_memory_id) for item in result] == [older_eligible_decision]
                assert [str(o.outcome_memory_id) for o in result[0].outcomes] == [eligible_outcome]
                # No unrelated company-wide/other-situation decision leaked in.
                assert unrelated_decision not in {str(item.decision_memory_id) for item in result}
        finally:
            await pool.close()

    _run(scenario())


def test_company_wide_mode_does_not_page_underfill_accepted(db_available) -> None:
    """Fix 1D preservation: company-wide mode must NOT gain the
    exact-situation paging behavior. The mirror scenario to the paging
    regression test above - MAX_LIST_LIMIT newer zero-outcome decisions
    plus one older eligible one, all with situation_id=None - must still
    return [] in company-wide mode, since company-wide underfill remains
    explicitly accepted (never paged further)."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="nopage") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    now = datetime.now(timezone.utc)
                    for i in range(MAX_LIST_LIMIT):
                        await _seed_decision(
                            conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                            decided_at=now - timedelta(hours=i),
                        )
                    older_eligible_decision = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decided_at=now - timedelta(days=30),
                    )
                    await _seed_outcome(
                        conn, company_id=company_id, decision_id=older_eligible_decision, user_id=user_id,
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id), limit=5)
                # Underfill accepted: the older eligible decision exists but
                # is outside the single bounded pool this mode ever looks
                # at, so it is correctly NOT found.
                assert result == []
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Company-wide mode (item 17)
# ---------------------------------------------------------------------------

def test_company_wide_mode_returns_outcome_backed_candidates(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="companywide") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    eligible = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=eligible, user_id=user_id)
                    # An ineligible decision (zero outcomes) coexists but
                    # must never appear.
                    await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert [str(item.decision_memory_id) for item in result] == [eligible]
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Decision ordering and tie-break (items 18, 19)
# ---------------------------------------------------------------------------

def test_decision_ordering_decided_at_desc(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="decorder") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    now = datetime.now(timezone.utc)
                    older = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decided_at=now - timedelta(days=10),
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=older, user_id=user_id)
                    newer = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decided_at=now - timedelta(days=1),
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=newer, user_id=user_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert [str(item.decision_memory_id) for item in result] == [newer, older]
        finally:
            await pool.close()

    _run(scenario())


def test_equal_decided_at_tiebreak_by_decision_id(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="dectie") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    shared_time = datetime.now(timezone.utc) - timedelta(days=2)
                    decision_1 = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decided_at=shared_time,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_1, user_id=user_id)
                    decision_2 = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decided_at=shared_time,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_2, user_id=user_id)
                expected_order = sorted([decision_1, decision_2])
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert [str(item.decision_memory_id) for item in result] == expected_order
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Limit contract (items 20-24, plus required-fix-round hardening 1-2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("requested_limit", [1, 5])
def test_limit_boundaries_respected(db_available, requested_limit) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label=f"limit{requested_limit}") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    now = datetime.now(timezone.utc)
                    for i in range(6):
                        decision_id = await _seed_decision(
                            conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                            decided_at=now - timedelta(days=i),
                        )
                        await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id), limit=requested_limit)
                assert len(result) == requested_limit
        finally:
            await pool.close()

    _run(scenario())


@pytest.mark.parametrize("invalid_limit", [0, -1, 6, 100])
def test_limit_out_of_range_rejected(db_available, invalid_limit) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="badlimit") as (company_id, user_id):
                service = OrganizationalMemoryRetrievalService(pool)
                with pytest.raises(InvalidMemoryInput):
                    await service.retrieve(company_id=UUID(company_id), limit=invalid_limit)
        finally:
            await pool.close()

    _run(scenario())


def test_limit_rejects_non_int(db_available) -> None:
    """Required-fix-round hardening item 1: a string limit ("5") must be
    rejected, never coerced."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="strlimit") as (company_id, user_id):
                service = OrganizationalMemoryRetrievalService(pool)
                with pytest.raises(InvalidMemoryInput):
                    await service.retrieve(company_id=UUID(company_id), limit="5")
        finally:
            await pool.close()

    _run(scenario())


def test_limit_rejects_bool(db_available) -> None:
    """Required-fix-round hardening item 2: `True`/`False` must be
    rejected even though Python's bool is an int subclass and True == 1
    (which would otherwise be in-range)."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="boollimit") as (company_id, user_id):
                service = OrganizationalMemoryRetrievalService(pool)
                with pytest.raises(InvalidMemoryInput):
                    await service.retrieve(company_id=UUID(company_id), limit=True)
                with pytest.raises(InvalidMemoryInput):
                    await service.retrieve(company_id=UUID(company_id), limit=False)
        finally:
            await pool.close()

    _run(scenario())


def test_fewer_than_limit_after_filtering_is_acceptable(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="fewer") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    # Only ONE eligible (outcome-backed) decision, plus
                    # several ineligible (zero-outcome) decisions that must
                    # never pad the result up toward the requested limit.
                    eligible = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=eligible, user_id=user_id)
                    for _ in range(3):
                        await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id), limit=DEFAULT_LIMIT)
                assert len(result) == 1
                assert result[0].decision_memory_id == UUID(eligible)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# No dedup fabrication (item 26)
# ---------------------------------------------------------------------------

def test_decisions_sharing_situation_not_deduplicated(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="sharedsituation") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    situation_id = await _seed_situation(conn, company_id=company_id)
                    decision_1 = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=situation_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_1, user_id=user_id)
                    decision_2 = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        situation_id=situation_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_2, user_id=user_id)
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id), situation_id=UUID(situation_id))
                returned_ids = {str(item.decision_memory_id) for item in result}
                assert returned_ids == {decision_1, decision_2}
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# No text truncation + long-text round-trip (required-fix-round hardening 3)
# ---------------------------------------------------------------------------

def test_long_human_authored_text_round_trips_untruncated(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="longtext") as (company_id, user_id):
                long_decision_text = "Decision rationale detail. " * 300  # ~8,100 chars
                long_rationale = "Supporting evidence and context. " * 300  # ~10,200 chars
                long_outcome_summary = "Observed operational result narrative. " * 300  # ~12,000 chars
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decision_text=long_decision_text, rationale=long_rationale,
                    )
                    await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        outcome_summary=long_outcome_summary,
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                item = result[0]
                assert item.decision_text == long_decision_text
                assert len(item.decision_text) == len(long_decision_text)
                assert item.rationale == long_rationale
                assert len(item.rationale) == len(long_rationale)
                assert item.outcomes[0].outcome_summary == long_outcome_summary
                assert len(item.outcomes[0].outcome_summary) == len(long_outcome_summary)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# No age cutoff (required-fix-round hardening 4)
# ---------------------------------------------------------------------------

def test_old_decision_and_outcome_remain_eligible_no_age_cutoff(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="oldmemory") as (company_id, user_id):
                very_old = datetime.now(timezone.utc) - timedelta(days=365 * 5)
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                        decided_at=very_old,
                    )
                    outcome_id = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                        observed_at=very_old,
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                assert result[0].decision_memory_id == UUID(decision_id)
                assert result[0].decided_at == very_old
                assert result[0].outcomes[0].outcome_memory_id == UUID(outcome_id)
                assert result[0].outcomes[0].observed_at == very_old
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Recursive-memory guard: structural proof (items 29, 31, 32, 33)
# ---------------------------------------------------------------------------

def test_context_dataclasses_have_no_forbidden_fields() -> None:
    """Structural proof: the returned shapes carry only durable ids and
    HUMAN-authored OME text - no receipt content, no Truth/Company Brain
    field, no scoring/similarity/confidence field, no policy label."""
    item_fields = {f.name for f in dataclasses.fields(OrganizationalMemoryContextItem)}
    assert item_fields == {
        "decision_memory_id",
        "reasoning_receipt_id",
        "situation_id",
        "decision_text",
        "rationale",
        "decided_at",
        "outcomes",
    }

    outcome_fields = {f.name for f in dataclasses.fields(OrganizationalMemoryOutcomeContext)}
    assert outcome_fields == {"outcome_memory_id", "outcome_summary", "result_state", "observed_at"}


def test_retrieval_service_never_imports_reasoning_receipt_repository() -> None:
    """Checks actual import/instantiation usage, not prose - the module's
    own docstring legitimately mentions ReasoningReceiptRepository/Service
    by name (explaining what is deliberately NOT used), so this asserts the
    real import statement and the real instantiation call are both
    absent, never a bare substring match against the whole file."""
    text = pathlib.Path("app/ome/services/organizational_memory_retrieval_service.py").read_text(encoding="utf-8")
    assert "from app.ome.repositories.reasoning_receipt_repository import" not in text
    assert "from app.ome.services.reasoning_receipt_service import" not in text
    assert "ReasoningReceiptRepository(" not in text
    assert "ReasoningReceiptService(" not in text


def test_service_never_imports_truth_company_brain_or_prompt_builders() -> None:
    """Structural proof (Step 15): the retrieval service imports nothing
    from Truth, Company Brain, memory facts, explainability, or decision
    context / prompt-building modules."""
    text = pathlib.Path("app/ome/services/organizational_memory_retrieval_service.py").read_text(encoding="utf-8")
    for forbidden_import in [
        "app.services.operational_truth_context",
        "app.services.company_brain_context",
        "app.services.memory",
        "app.services.explainability",
        "app.services.decision_context",
        "app.services.openai_client",
    ]:
        assert forbidden_import not in text


def test_provenance_pointers_preserved_without_receipt_content(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            distinctive_snapshot = '{"ceo_text": "DISTINCTIVE-AI-TEXT-MUST-NEVER-LEAK-4A"}'
            async with _company_scope(pool, label="provenance") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(
                        conn, company_id=company_id, user_id=user_id, response_snapshot=distinctive_snapshot,
                    )
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    outcome_id = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_id, user_id=user_id,
                    )
                service = OrganizationalMemoryRetrievalService(pool)
                result = await service.retrieve(company_id=UUID(company_id))
                assert len(result) == 1
                item = result[0]
                # Pointers preserved (items 27, 28).
                assert item.decision_memory_id == UUID(decision_id)
                assert item.reasoning_receipt_id == UUID(receipt_id)
                assert item.outcomes[0].outcome_memory_id == UUID(outcome_id)
                # No receipt content leaked anywhere in the returned object
                # (items 18/19/20/29/30 combined proof).
                serialized = repr(item)
                assert "DISTINCTIVE-AI-TEXT-MUST-NEVER-LEAK-4A" not in serialized
                assert "response_snapshot" not in serialized
                assert "evidence_refs" not in serialized
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# No mutation / no side effects (items 34-37, strengthened per required-fix
# round: exact row snapshot, not just a row-count comparison)
# ---------------------------------------------------------------------------

async def _snapshot_rows(conn: asyncpg.Connection, *, company_id: str) -> tuple[list[dict], list[dict]]:
    decision_rows = [
        dict(row)
        for row in await conn.fetch(
            "SELECT * FROM ome_decision_memories WHERE company_id=$1 ORDER BY id", company_id,
        )
    ]
    outcome_rows = [
        dict(row)
        for row in await conn.fetch(
            "SELECT * FROM ome_outcome_memories WHERE company_id=$1 ORDER BY id", company_id,
        )
    ]
    return decision_rows, outcome_rows


def test_retrieve_performs_no_mutation(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="nomutation") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(
                        conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id,
                    )
                    await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    decisions_before, outcomes_before = await _snapshot_rows(conn, company_id=company_id)

                service = OrganizationalMemoryRetrievalService(pool)
                await service.retrieve(company_id=UUID(company_id))
                await service.retrieve(company_id=UUID(company_id), situation_id=None, limit=1)

                async with pool.acquire() as conn:
                    decisions_after, outcomes_after = await _snapshot_rows(conn, company_id=company_id)

                # Exact row snapshot equality (every column, not just row
                # count) - proves no UPDATE mutated a value in place either.
                assert decisions_after == decisions_before
                assert outcomes_after == outcomes_before
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Dormancy (item 38)
# ---------------------------------------------------------------------------

def test_dormancy_not_referenced_from_live_chat_pipeline() -> None:
    """Checks actual import/instantiation usage in the three live-reasoning
    files, not a bare substring across the whole codebase (which would
    false-positive against this test file's own imports)."""
    live_pipeline_files = [
        "app/api/chat.py",
        "app/services/openai_client.py",
        "app/services/decision_context.py",
    ]
    for path in live_pipeline_files:
        text = pathlib.Path(path).read_text(encoding="utf-8")
        assert "organizational_memory_retrieval_service" not in text
        assert "OrganizationalMemoryRetrievalService" not in text


# ---------------------------------------------------------------------------
# Migration safety (items 39, 40)
# ---------------------------------------------------------------------------

def test_migrations_still_001_through_014() -> None:
    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert not any(name.startswith("015") for name in migration_files)
    assert any(name.startswith("014") for name in migration_files)


def test_migration_014_checksum_unchanged() -> None:
    import hashlib

    digest = hashlib.sha256(
        pathlib.Path("migrations/014_organizational_memory.sql").read_bytes()
    ).hexdigest()
    assert digest == "8e30a9b8bb7c73f226ac8bf8eb1a751ddb311c82404c5f635fd995c46a378710"


# ---------------------------------------------------------------------------
# Namespace cleanliness snapshot (items 41, 42) - SUPPLEMENTARY, defense in
# depth only. Every individual DB-mutating test above is independently
# failure-safe via _company_scope/_two_company_scope (cleanup runs in a
# `finally` around `yield`, executing even when an assertion fails) - this
# test does not rely on, and its validity does not depend on, pytest
# collection/execution order. It exists only to catch a leftover from a
# scenario outside this file's own control (e.g. a killed process
# mid-test), never as this file's own cleanup mechanism.
# ---------------------------------------------------------------------------

def test_m8_s4a_namespace_cleanliness_snapshot(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT slug FROM companies WHERE slug LIKE 'm8-s4a-%'")
            assert rows == [], f"leftover m8-s4a-* companies: {[r['slug'] for r in rows]}"
        finally:
            await pool.close()

    _run(scenario())
