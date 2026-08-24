"""M8 Slice 2: OME service tests (real Postgres).

Proves service-level business rules: validation, cross-tenant rejection,
supersession orchestration, and the trust boundary (server-generated
decided_at/observed_at, no client-supplied evidence_refs on decisions).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.ome.errors import DecisionNotFound, InvalidMemoryInput, OutcomeNotFound, ReceiptNotFound
from app.ome.models import DecisionMemory, OutcomeMemory, ReasoningReceipt
from app.ome.repositories.reasoning_receipt_repository import ReasoningReceiptRepository
from app.ome.services.decision_memory_service import DecisionMemoryService
from app.ome.services.outcome_memory_service import OutcomeMemoryService
from app.ome.services.reasoning_receipt_service import ReasoningReceiptService
from app.ome.types import EvidenceRef


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


async def _seed_receipt(conn: asyncpg.Connection, *, company_id: str, user_id: str) -> str:
    receipt_id = await conn.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, '[]'::jsonb)
        RETURNING id
        """,
        company_id, user_id, '{"ceo_text": "test"}',
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


async def _wipe_company(conn: asyncpg.Connection, company_id: str) -> None:
    await conn.execute("DELETE FROM ome_outcome_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_decision_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM operational_situations WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM files WHERE company_id=$1", company_id)


# ---------------------------------------------------------------------------
# Receipt service - evidence validation
# ---------------------------------------------------------------------------

def test_receipt_service_verifies_file_evidence_ref_in_company(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rs1")
                file_id = await _seed_file(conn, company_id=company_id, user_id=user_id)
            service = ReasoningReceiptService(pool)
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                evidence_refs=[EvidenceRef(type="file", id=UUID(file_id))],
            )
            assert isinstance(receipt, ReasoningReceipt)
            assert receipt.evidence_refs == [{"category": "truth", "type": "file", "id": file_id}]
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_service_rejects_file_from_another_company(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="rs2a")
                company_b, user_b = await _seed_company_and_user(conn, label="rs2b")
                file_b = await _seed_file(conn, company_id=company_b, user_id=user_b)
            service = ReasoningReceiptService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_a), created_by_user_id=UUID(user_a), session_id=None,
                    response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                    evidence_refs=[EvidenceRef(type="file", id=UUID(file_b))],
                )
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


def test_receipt_service_rejects_nonexistent_file(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rs3")
            service = ReasoningReceiptService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                    response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                    evidence_refs=[EvidenceRef(type="file", id=uuid4())],
                )
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_service_allows_empty_evidence_refs(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rs4")
            service = ReasoningReceiptService(pool)
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={"ceo_text": "x", "reasoning_assessment": {}}, evidence_refs=[],
            )
            assert receipt.evidence_refs == []
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_evidence_ref_rejects_unsupported_type() -> None:
    with pytest.raises(InvalidMemoryInput):
        EvidenceRef(type="operational_event", id=uuid4())  # type: ignore[arg-type]


def test_receipt_service_rejects_non_dict_response_snapshot(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rs5")
            service = ReasoningReceiptService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                    response_snapshot="not a dict", evidence_refs=[],  # type: ignore[arg-type]
                )
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_service_persists_canonical_snapshot_only(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="rs6")
            service = ReasoningReceiptService(pool)
            repo = ReasoningReceiptRepository(pool)
            raw_snapshot = {
                "ceo_text": "the answer",
                "reasoning_assessment": {"confidence": "high"},
                "prompt": "SECRET SYSTEM PROMPT",
                "decision_context": {"internal": "data"},
                "reasoning_reference_catalog": ["CB#1"],
                "secret_internal_context": "leak me not",
            }
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot=raw_snapshot, evidence_refs=[],
            )
            # The caller's input object must never be mutated by the service.
            assert "prompt" in raw_snapshot

            assert set(receipt.response_snapshot.keys()) == {"ceo_text", "reasoning_assessment"}

            # Prove persistence, not just the in-memory return value: re-fetch
            # the row from the repository/DB.
            fetched = await repo.get_by_id(company_id=UUID(company_id), receipt_id=receipt.id)
            assert fetched is not None
            assert set(fetched.response_snapshot.keys()) == {"ceo_text", "reasoning_assessment"}
            assert fetched.response_snapshot["ceo_text"] == "the answer"
            assert fetched.response_snapshot["reasoning_assessment"] == {"confidence": "high"}
            for leaked_key in (
                "prompt", "decision_context", "reasoning_reference_catalog", "secret_internal_context",
            ):
                assert leaked_key not in fetched.response_snapshot

            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Decision service
# ---------------------------------------------------------------------------

def test_decision_service_records_human_decision(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds1")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            service = DecisionMemoryService(pool)
            decision = await service.record_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                reasoning_receipt_id=UUID(receipt_id), decision_text="  Assign follow-up  ",
            )
            assert isinstance(decision, DecisionMemory)
            assert decision.decision_text == "Assign follow-up"
            assert decision.decided_by_user_id == UUID(user_id)
            assert decision.decided_at.tzinfo is not None
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_rejects_blank_text(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds2")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            service = DecisionMemoryService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.record_decision(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    reasoning_receipt_id=UUID(receipt_id), decision_text="   ",
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_blank_rationale_becomes_none(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds3")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            service = DecisionMemoryService(pool)
            decision = await service.record_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                reasoning_receipt_id=UUID(receipt_id), decision_text="x", rationale="   ",
            )
            assert decision.rationale is None
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_rejects_non_string_decision_text(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds3b")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            service = DecisionMemoryService(pool)
            for bad_value in (123, {}):
                with pytest.raises(InvalidMemoryInput):
                    await service.record_decision(
                        company_id=UUID(company_id), acting_user_id=UUID(user_id),
                        reasoning_receipt_id=UUID(receipt_id), decision_text=bad_value,  # type: ignore[arg-type]
                    )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_rejects_non_string_rationale(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds3c")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            service = DecisionMemoryService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.record_decision(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    reasoning_receipt_id=UUID(receipt_id), decision_text="x", rationale=123,  # type: ignore[arg-type]
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_receipt_must_exist_inside_company(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds4")
            service = DecisionMemoryService(pool)
            with pytest.raises(ReceiptNotFound):
                await service.record_decision(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    reasoning_receipt_id=uuid4(), decision_text="x",
                )
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_rejects_cross_company_receipt(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="ds5a")
                company_b, user_b = await _seed_company_and_user(conn, label="ds5b")
                receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
            service = DecisionMemoryService(pool)
            with pytest.raises(ReceiptNotFound):
                await service.record_decision(
                    company_id=UUID(company_a), acting_user_id=UUID(user_a),
                    reasoning_receipt_id=UUID(receipt_b), decision_text="x",
                )
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


def test_decision_service_optional_situation_must_exist_inside_company(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds6")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                situation_id = await _seed_situation(conn, company_id=company_id)
            service = DecisionMemoryService(pool)
            decision = await service.record_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                reasoning_receipt_id=UUID(receipt_id), decision_text="x", situation_id=UUID(situation_id),
            )
            assert decision.situation_id == UUID(situation_id)
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_decision_service_rejects_cross_company_situation(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_a, user_a = await _seed_company_and_user(conn, label="ds7a")
                company_b, user_b = await _seed_company_and_user(conn, label="ds7b")
                receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                situation_b = await _seed_situation(conn, company_id=company_b)
            service = DecisionMemoryService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.record_decision(
                    company_id=UUID(company_a), acting_user_id=UUID(user_a),
                    reasoning_receipt_id=UUID(receipt_a), decision_text="x", situation_id=UUID(situation_b),
                )
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


def test_decision_service_has_no_evidence_refs_parameter() -> None:
    import inspect

    params = inspect.signature(DecisionMemoryService.record_decision).parameters
    assert "evidence_refs" not in params


def test_decision_service_supersede_decision_atomic(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="ds8")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            service = DecisionMemoryService(pool)
            original = await service.record_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                reasoning_receipt_id=UUID(receipt_id), decision_text="ORIGINAL",
            )
            new_dec, old_dec = await service.supersede_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id), old_decision_id=original.id,
                reasoning_receipt_id=UUID(receipt_id), decision_text="CORRECTED",
            )
            assert old_dec.status == "superseded"
            assert old_dec.decision_text == "ORIGINAL"
            assert new_dec.decision_text == "CORRECTED"
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Outcome service
# ---------------------------------------------------------------------------

def test_outcome_service_records_outcome(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os1")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            outcome = await service.record_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                decision_memory_id=UUID(decision_id), outcome_summary="  It worked  ", result_state="positive",
            )
            assert isinstance(outcome, OutcomeMemory)
            assert outcome.outcome_summary == "It worked"
            assert outcome.observed_at.tzinfo is not None
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_decision_must_exist_inside_company(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os2")
            service = OutcomeMemoryService(pool)
            with pytest.raises(DecisionNotFound):
                await service.record_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    decision_memory_id=uuid4(), outcome_summary="x", result_state="unknown",
                )
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_rejects_blank_summary(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os3")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.record_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    decision_memory_id=UUID(decision_id), outcome_summary="   ", result_state="unknown",
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_rejects_non_string_summary(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os3b")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.record_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    decision_memory_id=UUID(decision_id), outcome_summary=123, result_state="unknown",  # type: ignore[arg-type]
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_rejects_invalid_result_state(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os4")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.record_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    decision_memory_id=UUID(decision_id), outcome_summary="x", result_state="bogus",
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_omitted_observed_at_uses_utc_now(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os5")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            before = datetime.now(timezone.utc)
            outcome = await service.record_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                decision_memory_id=UUID(decision_id), outcome_summary="x", result_state="unknown",
            )
            after = datetime.now(timezone.utc)
            assert before <= outcome.observed_at <= after
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_rejects_future_observed_at(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os6")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            future = datetime.now(timezone.utc) + timedelta(days=1)
            with pytest.raises(InvalidMemoryInput):
                await service.record_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    decision_memory_id=UUID(decision_id), outcome_summary="x", result_state="unknown",
                    observed_at=future,
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_rejects_naive_observed_at(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os7")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            naive = datetime.now()  # noqa: DTZ005 - deliberately naive, testing rejection
            with pytest.raises(InvalidMemoryInput):
                await service.record_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id),
                    decision_memory_id=UUID(decision_id), outcome_summary="x", result_state="unknown",
                    observed_at=naive,
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_allows_outcome_on_superseded_decision(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os8")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
            decision_service = DecisionMemoryService(pool)
            outcome_service = OutcomeMemoryService(pool)
            original = await decision_service.record_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                reasoning_receipt_id=UUID(receipt_id), decision_text="original",
            )
            await decision_service.supersede_decision(
                company_id=UUID(company_id), acting_user_id=UUID(user_id), old_decision_id=original.id,
                reasoning_receipt_id=UUID(receipt_id), decision_text="replacement",
            )
            # original is now superseded - recording an outcome against it must still work.
            outcome = await outcome_service.record_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                decision_memory_id=original.id, outcome_summary="outcome of the original", result_state="mixed",
            )
            assert outcome.decision_memory_id == original.id
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_supersede_outcome_atomic(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os9")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            original = await service.record_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                decision_memory_id=UUID(decision_id), outcome_summary="ORIGINAL", result_state="unknown",
            )
            new_out, old_out = await service.supersede_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id), old_outcome_id=original.id,
                outcome_summary="CORRECTED", result_state="positive",
            )
            assert old_out.status == "superseded"
            assert old_out.outcome_summary == "ORIGINAL"
            assert new_out.outcome_summary == "CORRECTED"
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_supersession_stays_on_same_decision(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os9b")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_a = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                decision_b = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)

            outcome_a = await service.record_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                decision_memory_id=UUID(decision_a), outcome_summary="A original", result_state="unknown",
            )
            new_out, old_out = await service.supersede_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id), old_outcome_id=outcome_a.id,
                outcome_summary="A corrected", result_state="positive",
            )
            # The replacement stays on the SAME decision as the outcome it
            # supersedes, even though a different decision (decision_b)
            # exists in the same company.
            assert new_out.decision_memory_id == UUID(decision_a)
            assert old_out.decision_memory_id == UUID(decision_a)

            # A genuinely different decision's outcome is unaffected and
            # still goes through record_outcome(), never supersession.
            outcome_b = await service.record_outcome(
                company_id=UUID(company_id), acting_user_id=UUID(user_id),
                decision_memory_id=UUID(decision_b), outcome_summary="B original", result_state="unknown",
            )
            assert outcome_b.decision_memory_id == UUID(decision_b)

            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_supersede_outcome_has_no_decision_memory_id_parameter() -> None:
    import inspect

    from app.ome.repositories.outcome_memory_repository import OutcomeMemoryRepository

    service_params = inspect.signature(OutcomeMemoryService.supersede_outcome).parameters
    assert "decision_memory_id" not in service_params

    repo_params = inspect.signature(OutcomeMemoryRepository.supersede_with_new_outcome).parameters
    assert "decision_memory_id" not in repo_params


def test_outcome_service_supersede_nonexistent_outcome_raises_not_found(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="os10")
                receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
            service = OutcomeMemoryService(pool)
            with pytest.raises(OutcomeNotFound):
                await service.supersede_outcome(
                    company_id=UUID(company_id), acting_user_id=UUID(user_id), old_outcome_id=uuid4(),
                    outcome_summary="x", result_state="unknown",
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_outcome_service_has_no_evidence_refs_parameter() -> None:
    import inspect

    params = inspect.signature(OutcomeMemoryService.record_outcome).parameters
    assert "evidence_refs" not in params


# ---------------------------------------------------------------------------
# Final zero-leftover verification for this module
# ---------------------------------------------------------------------------

def test_zero_slice2_service_leftovers_marker(db_available) -> None:
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
