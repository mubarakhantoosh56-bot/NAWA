"""M8 Slice 2: OME repository tests (real Postgres).

Proves repository-level facts that need real FK/transaction/locking
behavior a fake pool cannot faithfully exercise - same style as
tests/test_m8_slice1_ome_schema.py and tests/test_memory_fact_conflict.py:
real asyncpg pool against DATABASE_URL, db_available skip fixture, each
test seeds and cleans up its own rows inline.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.ome.errors import InvalidSupersession
from app.ome.models import DecisionMemory, OutcomeMemory, ReasoningReceipt
from app.ome.repositories.decision_memory_repository import DecisionMemoryRepository
from app.ome.repositories.outcome_memory_repository import OutcomeMemoryRepository
from app.ome.repositories.reasoning_receipt_repository import ReasoningReceiptRepository


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=6)


async def _seed_company_and_user(conn: asyncpg.Connection, *, label: str) -> tuple[str, str]:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m8-s2-{label}-{uuid4().hex[:10]}", f"M8 Slice 2 Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s2-{label}-{uuid4().hex[:10]}@example.com", f"M8 Slice 2 Test User {label}",
    )
    return str(company_id), str(user_id)


async def _seed_file(conn: asyncpg.Connection, *, company_id: str, user_id: str) -> str:
    filename = f"m8-s2-test-{uuid4().hex[:10]}.xlsx"
    file_id = await conn.fetchval(
        """
        INSERT INTO files (company_id, uploaded_by_user_id, filename, content_type, file_size_bytes, storage_path)
        VALUES ($1, $2, $3, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 100, '/tmp/test.xlsx')
        RETURNING id
        """,
        company_id, user_id, filename,
    )
    return str(file_id)


async def _seed_receipt(
    conn: asyncpg.Connection, *, company_id: str, user_id: str, evidence_refs: str = "[]"
) -> str:
    receipt_id = await conn.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, $4::jsonb)
        RETURNING id
        """,
        company_id, user_id, '{"ceo_text": "test"}', evidence_refs,
    )
    return str(receipt_id)


async def _seed_decision(conn: asyncpg.Connection, *, company_id: str, receipt_id: str, user_id: str) -> str:
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


async def _seed_outcome(conn: asyncpg.Connection, *, company_id: str, decision_id: str, user_id: str) -> str:
    outcome_id = await conn.fetchval(
        """
        INSERT INTO ome_outcome_memories
            (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
        VALUES ($1, $2, 'Test outcome', 'unknown', $3, NOW())
        RETURNING id
        """,
        company_id, decision_id, user_id,
    )
    return str(outcome_id)


async def _wipe_company(conn: asyncpg.Connection, company_id: str) -> None:
    await conn.execute("DELETE FROM ome_outcome_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_decision_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM operational_situations WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM files WHERE company_id=$1", company_id)


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


# ---------------------------------------------------------------------------
# Receipts (1-10, repository-level slice)
# ---------------------------------------------------------------------------

def test_receipt_create_returns_domain_model(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rc1")
            repo = ReasoningReceiptRepository(pool)
            receipt = await repo.create(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id="s1",
                response_snapshot={"ceo_text": "hi", "reasoning_assessment": {}},
                evidence_refs=[{"type": "file", "id": str(uuid4())}],
            )
            assert isinstance(receipt, ReasoningReceipt)
            assert receipt.response_snapshot == {"ceo_text": "hi", "reasoning_assessment": {}}
            assert len(receipt.evidence_refs) == 1
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_company_scoped_get_works(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rc2")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            repo = ReasoningReceiptRepository(pool)
            found = await repo.get_by_id(company_id=UUID(company_id), receipt_id=UUID(receipt_id))
            assert found is not None
            assert str(found.id) == receipt_id
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_cross_company_get_does_not_reveal_row(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="rc3a")
                company_b, user_b = await _seed_company_and_user(conn, label="rc3b")
                receipt_id = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
            repo = ReasoningReceiptRepository(pool)
            found = await repo.get_by_id(company_id=UUID(company_b), receipt_id=UUID(receipt_id))
            assert found is None
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_a)
                await _wipe_company(conn, company_b)
                for uid in (user_a, user_b):
                    await conn.execute("DELETE FROM users WHERE id=$1", uid)
                for cid in (company_a, company_b):
                    await conn.execute("DELETE FROM companies WHERE id=$1", cid)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_repository_has_no_update_or_delete_method(db_available) -> None:
    repo = ReasoningReceiptRepository(db=None)
    assert not hasattr(repo, "update")
    assert not hasattr(repo, "delete")


def test_receipt_evidence_refs_preserved_in_order_including_duplicates(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rc5")
            file_a, file_b = str(uuid4()), str(uuid4())
            refs = [{"type": "file", "id": file_a}, {"type": "file", "id": file_b}, {"type": "file", "id": file_a}]
            repo = ReasoningReceiptRepository(pool)
            receipt = await repo.create(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={"ceo_text": "x", "reasoning_assessment": {}}, evidence_refs=refs,
            )
            assert receipt.evidence_refs == refs
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Decisions - repository-level
# ---------------------------------------------------------------------------

def test_decision_create_and_get_return_domain_models(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc1")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            repo = DecisionMemoryRepository(pool)
            created = await repo.create(
                company_id=UUID(company_id), reasoning_receipt_id=UUID(receipt_id), situation_id=None,
                decision_text="Assign follow-up", rationale=None, decided_by_user_id=UUID(user_id),
                decided_at=datetime.now(timezone.utc),
            )
            assert isinstance(created, DecisionMemory)
            fetched = await repo.get_by_id(company_id=UUID(company_id), decision_id=created.id)
            assert isinstance(fetched, DecisionMemory)
            assert fetched.id == created.id
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_cross_company_get_returns_none(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="dc2a")
                company_b, user_b = await _seed_company_and_user(conn, label="dc2b")
                receipt_id = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                decision_id = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_id, user_id=user_a)
            repo = DecisionMemoryRepository(pool)
            found = await repo.get_by_id(company_id=UUID(company_b), decision_id=UUID(decision_id))
            assert found is None
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_a)
                await _wipe_company(conn, company_b)
                for uid in (user_a, user_b):
                    await conn.execute("DELETE FROM users WHERE id=$1", uid)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_a)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_b)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_list_recent_ordering_and_limit(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc3")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                ids = []
                for i in range(5):
                    did = await conn.fetchval(
                        """
                        INSERT INTO ome_decision_memories
                            (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
                        VALUES ($1, $2, $3, $4, $5) RETURNING id
                        """,
                        company_id, receipt_id, f"decision {i}", user_id,
                        datetime.now(timezone.utc) + timedelta(seconds=i),
                    )
                    ids.append(str(did))
            repo = DecisionMemoryRepository(pool)
            listed = await repo.list_recent(company_id=UUID(company_id), limit=3)
            assert len(listed) == 3
            assert [str(d.id) for d in listed] == list(reversed(ids))[:3]
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_list_recent_hides_superseded_by_default(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc4")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                old_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            repo = DecisionMemoryRepository(pool)
            new_dec, old_dec = await repo.supersede_with_new_decision(
                company_id=UUID(company_id), old_decision_id=UUID(old_id), reasoning_receipt_id=UUID(receipt_id),
                situation_id=None, decision_text="replacement", rationale=None,
                decided_by_user_id=UUID(user_id), decided_at=datetime.now(timezone.utc),
            )
            hidden = await repo.list_recent(company_id=UUID(company_id), include_superseded=False)
            assert {str(d.id) for d in hidden} == {str(new_dec.id)}
            full = await repo.list_recent(company_id=UUID(company_id), include_superseded=True)
            assert {str(d.id) for d in full} == {str(new_dec.id), str(old_dec.id)}
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_supersession_atomic_old_content_preserved(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc5")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                old_id = await conn.fetchval(
                    """
                    INSERT INTO ome_decision_memories
                        (company_id, reasoning_receipt_id, decision_text, rationale, decided_by_user_id, decided_at)
                    VALUES ($1, $2, 'ORIGINAL TEXT', 'ORIGINAL RATIONALE', $3, NOW())
                    RETURNING id
                    """,
                    company_id, receipt_id, user_id,
                )
            repo = DecisionMemoryRepository(pool)
            new_dec, old_dec = await repo.supersede_with_new_decision(
                company_id=UUID(company_id), old_decision_id=UUID(str(old_id)), reasoning_receipt_id=UUID(receipt_id),
                situation_id=None, decision_text="corrected", rationale="corrected rationale",
                decided_by_user_id=UUID(user_id), decided_at=datetime.now(timezone.utc),
            )
            assert old_dec.status == "superseded"
            assert old_dec.superseded_by == new_dec.id
            assert old_dec.decision_text == "ORIGINAL TEXT"
            assert old_dec.rationale == "ORIGINAL RATIONALE"
            assert new_dec.status == "active"
            assert new_dec.decision_text == "corrected"
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_already_superseded_cannot_be_superseded_again(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc6")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                old_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            repo = DecisionMemoryRepository(pool)
            new_dec, _old = await repo.supersede_with_new_decision(
                company_id=UUID(company_id), old_decision_id=UUID(old_id), reasoning_receipt_id=UUID(receipt_id),
                situation_id=None, decision_text="first replacement", rationale=None,
                decided_by_user_id=UUID(user_id), decided_at=datetime.now(timezone.utc),
            )
            with pytest.raises(InvalidSupersession):
                await repo.supersede_with_new_decision(
                    company_id=UUID(company_id), old_decision_id=UUID(old_id), reasoning_receipt_id=UUID(receipt_id),
                    situation_id=None, decision_text="second attempt", rationale=None,
                    decided_by_user_id=UUID(user_id), decided_at=datetime.now(timezone.utc),
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_concurrent_double_supersession_has_exactly_one_winner(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc7")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                old_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            repo = DecisionMemoryRepository(pool)

            async def attempt(text: str) -> str:
                try:
                    await repo.supersede_with_new_decision(
                        company_id=UUID(company_id), old_decision_id=UUID(old_id), reasoning_receipt_id=UUID(receipt_id),
                        situation_id=None, decision_text=text, rationale=None,
                        decided_by_user_id=UUID(user_id), decided_at=datetime.now(timezone.utc),
                    )
                    return "ok"
                except InvalidSupersession:
                    return "failed"

            results = await asyncio.gather(attempt("attempt-A"), attempt("attempt-B"))
            assert sorted(results) == ["failed", "ok"]

            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT status FROM ome_decision_memories WHERE company_id=$1", company_id
                )
                statuses = sorted(r["status"] for r in rows)
                # exactly 2 rows total: the original (now superseded) + exactly
                # one winner's replacement (active) - no orphan from the loser.
                assert statuses == ["active", "superseded"]
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Outcomes - repository-level
# ---------------------------------------------------------------------------

def test_outcome_create_and_get_return_domain_models(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="oc1")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            repo = OutcomeMemoryRepository(pool)
            created = await repo.create(
                company_id=UUID(company_id), decision_memory_id=UUID(decision_id), outcome_summary="worked",
                result_state="positive", recorded_by_user_id=UUID(user_id), observed_at=datetime.now(timezone.utc),
            )
            assert isinstance(created, OutcomeMemory)
            fetched = await repo.get_by_id(company_id=UUID(company_id), outcome_id=created.id)
            assert isinstance(fetched, OutcomeMemory)
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_list_by_decision_hides_superseded_by_default(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="oc2")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                old_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
            repo = OutcomeMemoryRepository(pool)
            new_out, old_out = await repo.supersede_with_new_outcome(
                company_id=UUID(company_id), old_outcome_id=UUID(old_outcome),
                outcome_summary="corrected", result_state="positive",
                recorded_by_user_id=UUID(user_id), observed_at=datetime.now(timezone.utc),
            )
            hidden = await repo.list_by_decision(company_id=UUID(company_id), decision_memory_id=UUID(decision_id))
            assert {str(o.id) for o in hidden} == {str(new_out.id)}
            full = await repo.list_by_decision(
                company_id=UUID(company_id), decision_memory_id=UUID(decision_id), include_superseded=True
            )
            assert {str(o.id) for o in full} == {str(new_out.id), str(old_out.id)}
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_supersede_derives_decision_id_from_locked_old_row(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="oc2b")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_a = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                decision_b = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                old_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_a, user_id=user_id)
            repo = OutcomeMemoryRepository(pool)
            new_out, old_out = await repo.supersede_with_new_outcome(
                company_id=UUID(company_id), old_outcome_id=UUID(old_outcome),
                outcome_summary="corrected", result_state="positive",
                recorded_by_user_id=UUID(user_id), observed_at=datetime.now(timezone.utc),
            )
            # decision_memory_id is derived from the locked old row, never a
            # caller input - it must never drift to decision_b even though
            # decision_b exists in the same company.
            assert new_out.decision_memory_id == UUID(decision_a)
            assert old_out.decision_memory_id == UUID(decision_a)
            assert new_out.decision_memory_id != UUID(decision_b)
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_concurrent_double_supersession_has_exactly_one_winner(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="oc3")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                old_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
            repo = OutcomeMemoryRepository(pool)

            async def attempt(summary: str) -> str:
                try:
                    await repo.supersede_with_new_outcome(
                        company_id=UUID(company_id), old_outcome_id=UUID(old_outcome),
                        outcome_summary=summary, result_state="positive",
                        recorded_by_user_id=UUID(user_id), observed_at=datetime.now(timezone.utc),
                    )
                    return "ok"
                except InvalidSupersession:
                    return "failed"

            results = await asyncio.gather(attempt("A"), attempt("B"))
            assert sorted(results) == ["failed", "ok"]

            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT status FROM ome_outcome_memories WHERE company_id=$1", company_id
                )
                statuses = sorted(r["status"] for r in rows)
                assert statuses == ["active", "superseded"]
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Tenant hygiene (42-45)
# ---------------------------------------------------------------------------

def test_every_repository_lookup_is_company_scoped(db_available) -> None:
    """Structural check: every get_by_id/list_* method on all three
    repositories requires company_id as a keyword-only parameter."""
    import inspect

    for repo_cls in (ReasoningReceiptRepository, DecisionMemoryRepository, OutcomeMemoryRepository):
        for name, method in inspect.getmembers(repo_cls, predicate=inspect.isfunction):
            if name.startswith("_") or name == "__init__":
                continue
            params = inspect.signature(method).parameters
            assert "company_id" in params, f"{repo_cls.__name__}.{name} is missing company_id"


def test_wrong_company_ids_behave_as_not_found(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="hy1a")
                company_b, user_b = await _seed_company_and_user(conn, label="hy1b")
                receipt_id = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                decision_id = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_id, user_id=user_a)
                outcome_id = await _seed_outcome(conn, company_id=company_a, decision_id=decision_id, user_id=user_a)

            receipt_repo = ReasoningReceiptRepository(pool)
            decision_repo = DecisionMemoryRepository(pool)
            outcome_repo = OutcomeMemoryRepository(pool)

            assert await receipt_repo.get_by_id(company_id=UUID(company_b), receipt_id=UUID(receipt_id)) is None
            assert await decision_repo.get_by_id(company_id=UUID(company_b), decision_id=UUID(decision_id)) is None
            assert await outcome_repo.get_by_id(company_id=UUID(company_b), outcome_id=UUID(outcome_id)) is None
            assert await decision_repo.list_by_receipt(company_id=UUID(company_b), reasoning_receipt_id=UUID(receipt_id)) == []

            async with pool.acquire() as conn:
                await _wipe_company(conn, company_a)
                await _wipe_company(conn, company_b)
                for uid in (user_a, user_b):
                    await conn.execute("DELETE FROM users WHERE id=$1", uid)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_a)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_b)
        finally:
            await pool.close()

    _run(scenario())


def test_zero_slice2_leftovers_marker(db_available) -> None:
    """Sanity marker: no row matching this file's 'm8-s2-%' test prefix
    should exist before or after this module's own tests ran cleanly."""

    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                companies = await conn.fetchval("SELECT count(*) FROM companies WHERE slug LIKE 'm8-s2-%'")
                users = await conn.fetchval("SELECT count(*) FROM users WHERE email LIKE 'm8-s2-%'")
                files = await conn.fetchval("SELECT count(*) FROM files WHERE filename LIKE 'm8-s2-%'")
                return companies, users, files
        finally:
            await pool.close()

    companies, users, files = _run(scenario())
    assert companies == 0
    assert users == 0
    assert files == 0
