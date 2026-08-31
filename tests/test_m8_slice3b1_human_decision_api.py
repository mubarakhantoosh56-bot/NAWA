"""M8 Slice 3B-1: Human Decision recording API tests (real Postgres, real
HTTP route via TestClient(app)).

Proves: POST /decisions creates a DecisionMemory row only from an explicit,
authenticated human call - never from a successful /ai/chat response alone
(item 44, proven by reusing the already-closed Slice 3A live-chat harness
without modifying that file); the request model fails closed on ANY
undeclared field (Founder Correction 1); company_id/decided_by_user_id are
always JWT-derived, never client-supplied; the reasoning_receipt_id/
situation_id company-scoping is enforced via the existing, unmodified
DecisionMemoryService/repositories; and no supersession/outcome surface is
reachable through this API.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.core.security import create_token
from app.main import app
from app.services.openai_client import ai_engine

from tests.test_m7_slice1_upload_truth_bridge import (
    _GoldenPermissionAuthService,
    _reset_stale_db_bindings,
)
from tests.test_m8_slice3a_live_reasoning_receipts import _cleanup as _cleanup_slice3a
from tests.test_m8_slice3a_live_reasoning_receipts import _upload_and_chat


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=5)


async def _seed_company_user(pool, *, label: str) -> tuple[str, str]:
    company_row = await pool.fetchrow(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m8-s3b1-{label}-{uuid4().hex[:8]}", f"M8 Slice 3B-1 Test Company {label}",
    )
    user_row = await pool.fetchrow(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s3b1-{label}-{uuid4().hex[:8]}@example.com", f"M8 Slice 3B-1 Test User {label}",
    )
    return str(company_row["id"]), str(user_row["id"])


async def _seed_receipt(pool, *, company_id: str, user_id: str) -> str:
    receipt_id = await pool.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, '[]'::jsonb)
        RETURNING id
        """,
        UUID(company_id), UUID(user_id), '{"ceo_text": "test", "reasoning_assessment": {}}',
    )
    return str(receipt_id)


async def _seed_situation(pool, *, company_id: str) -> str:
    now = datetime.now(timezone.utc)
    situation_id = await pool.fetchval(
        """
        INSERT INTO operational_situations
            (company_id, title, summary, situation_type, severity, status,
             time_window_start, time_window_end, detection_method, source_type)
        VALUES ($1, 'Test situation', 'Test summary', 'anomaly', 'low', 'active', $2, $3, 'rule_based', 'manual_rule')
        RETURNING id
        """,
        UUID(company_id), now - timedelta(hours=1), now,
    )
    return str(situation_id)


async def _cleanup(pool, *, company_id: str, user_id: str) -> None:
    _uuid = UUID
    await pool.execute("DELETE FROM ome_decision_memories WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM ome_reasoning_receipts WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM operational_situations WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM companies WHERE id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM users WHERE id = $1", _uuid(user_id))


async def _decision_count(pool, *, company_id: str) -> int:
    return await pool.fetchval(
        "SELECT count(*) FROM ome_decision_memories WHERE company_id = $1", UUID(company_id)
    )


def _headers(company_id: str, user_id: str) -> dict:
    token = create_token(company_id=company_id, user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def _post_decisions(client, headers, body, *, permissions=("memory.write",)):
    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_GoldenPermissionAuthService(list(permissions))),
    ):
        return client.post("/decisions", headers=headers, json=body)


# ---------------------------------------------------------------------------
# HAPPY PATH (items 1-12)
# ---------------------------------------------------------------------------

def test_happy_path_creates_exactly_one_active_decision(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="happy")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "  خفض الإنتاج 10%  ", "rationale": "  "},
        )
        assert response.status_code == 201, response.text
        body = response.json()

        async def verify():
            pool = await _make_pool()
            try:
                count = await _decision_count(pool, company_id=company_id)
                row = await pool.fetchrow(
                    "SELECT * FROM ome_decision_memories WHERE company_id = $1", UUID(company_id)
                )
                return count, row
            finally:
                await pool.close()

        count, row = asyncio.run(verify())
        assert count == 1, "item 2: exactly one row created"
        assert str(row["id"]) == body["id"], "item 12: response id == persisted id"
        assert str(row["company_id"]) == company_id, "item 3: persisted company_id == JWT company"
        assert str(row["decided_by_user_id"]) == user_id, "item 4: persisted decided_by_user_id == JWT user"
        assert str(row["reasoning_receipt_id"]) == receipt_id, "item 5: exact receipt id"
        assert row["decision_text"] == "خفض الإنتاج 10%", "item 6: trimmed per service semantics"
        assert row["rationale"] is None, "items 7/8: blank rationale becomes None"
        assert row["status"] == "active", "item 9"
        assert row["decided_at"] is not None, "item 10: server-generated"
        assert row["created_at"] is not None, "item 11"
        assert body["status"] == "active"
        assert body["rationale"] is None
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


async def _run_cleanup(company_id: str, user_id: str) -> None:
    pool = await _make_pool()
    try:
        await _cleanup(pool, company_id=company_id, user_id=user_id)
    finally:
        await pool.close()


def test_rationale_stored_when_provided(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="rationale")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x", "rationale": "because Y"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["rationale"] == "because Y", "item 7"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# RECEIPT SECURITY (items 13-15)
# ---------------------------------------------------------------------------

def test_nonexistent_receipt_returns_404(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_user(pool, label="norcpt")
        finally:
            await pool.close()

    company_id, user_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": str(uuid4()), "decision_text": "x"},
        )
        assert response.status_code == 404, response.text
        assert "another company" not in response.text.lower()

        async def count():
            pool = await _make_pool()
            try:
                return await _decision_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_cross_company_receipt_returns_same_404(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_a, user_a = await _seed_company_user(pool, label="crossa")
            company_b, user_b = await _seed_company_user(pool, label="crossb")
            receipt_b = await _seed_receipt(pool, company_id=company_b, user_id=user_b)
            return company_a, user_a, company_b, user_b, receipt_b
        finally:
            await pool.close()

    company_a, user_a, company_b, user_b, receipt_b = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_a, user_a),
            {"reasoning_receipt_id": receipt_b, "decision_text": "x"},
        )
        assert response.status_code == 404, response.text
        assert "belongs to another company" not in response.text.lower()
        assert "exists" not in response.text.lower()

        async def counts():
            pool = await _make_pool()
            try:
                return (
                    await _decision_count(pool, company_id=company_a),
                    await _decision_count(pool, company_id=company_b),
                )
            finally:
                await pool.close()

        count_a, count_b = asyncio.run(counts())
        assert count_a == 0 and count_b == 0
    finally:
        asyncio.run(_run_cleanup(company_a, user_a))
        asyncio.run(_run_cleanup(company_b, user_b))
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# FORBIDDEN CLIENT FIELDS (items 16-26)
# ---------------------------------------------------------------------------

FORBIDDEN_EXTRA_FIELDS = {
    "company_id": str(uuid4()),
    "created_by_user_id": str(uuid4()),
    "decided_by_user_id": str(uuid4()),
    "evidence_refs": [],
    "company_brain_refs": [],
    "response_snapshot": {"ceo_text": "x"},
    "status": "active",
    "created_at": "2020-01-01T00:00:00Z",
    "decided_at": "2020-01-01T00:00:00Z",
    "supersedes_id": str(uuid4()),
    "superseded_by": str(uuid4()),
}


@pytest.mark.parametrize("field_name,field_value", sorted(FORBIDDEN_EXTRA_FIELDS.items()))
def test_forbidden_extra_field_rejected(db_available, field_name, field_value) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label=f"ext-{field_name[:6]}")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        body = {"reasoning_receipt_id": receipt_id, "decision_text": "x", field_name: field_value}
        response = _post_decisions(client, _headers(company_id, user_id), body)
        assert response.status_code == 422, response.text  # items 16-25

        async def count():
            pool = await _make_pool()
            try:
                return await _decision_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0, "item 26: zero rows created"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# SITUATION (items 27-30)
# ---------------------------------------------------------------------------

def test_valid_same_company_situation_succeeds(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="situ")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            situation_id = await _seed_situation(pool, company_id=company_id)
            return company_id, user_id, receipt_id, situation_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id, situation_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x", "situation_id": situation_id},
        )
        assert response.status_code == 201, response.text
        assert response.json()["situation_id"] == situation_id
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_nonexistent_situation_returns_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="nositu")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x", "situation_id": str(uuid4())},
        )
        assert response.status_code == 422, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _decision_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_cross_company_situation_returns_same_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_a, user_a = await _seed_company_user(pool, label="csitua")
            company_b, user_b = await _seed_company_user(pool, label="csitub")
            receipt_a = await _seed_receipt(pool, company_id=company_a, user_id=user_a)
            situation_b = await _seed_situation(pool, company_id=company_b)
            return company_a, user_a, receipt_a, company_b, user_b, situation_b
        finally:
            await pool.close()

    company_a, user_a, receipt_a, company_b, user_b, situation_b = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_a, user_a),
            {"reasoning_receipt_id": receipt_a, "decision_text": "x", "situation_id": situation_b},
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_a, user_a))
        asyncio.run(_run_cleanup(company_b, user_b))
        _reset_stale_db_bindings(app, ai_engine)


def test_omitted_situation_succeeds(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="omitsitu")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["situation_id"] is None
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# VALIDATION (items 31-34)
# ---------------------------------------------------------------------------

def test_blank_decision_text_returns_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="blanktext")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "   "},
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_non_string_decision_text_returns_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="nonstrtext")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": 123},
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_non_string_rationale_returns_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="nonstrrat")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x", "rationale": 123},
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_no_arbitrary_max_length_regression(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="longtext")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        long_text = "x" * 5000
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": long_text},
        )
        assert response.status_code == 201, response.text
        assert response.json()["decision_text"] == long_text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# AUTH/PERMISSION (items 35-38)
# ---------------------------------------------------------------------------

def test_user_with_memory_write_succeeds(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="haswrite")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x"},
            permissions=["memory.write"],
        )
        assert response.status_code == 201, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_user_without_memory_write_returns_403(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="nowrite")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x"},
            permissions=["ai.chat"],  # explicitly NOT memory.write
        )
        assert response.status_code == 403, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _decision_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        _reset_stale_db_bindings(app, ai_engine)


def test_request_body_cannot_override_jwt_company_or_user(db_available) -> None:
    """items 37/38: even if a client tried to smuggle company_id/user
    identity in, DecisionCreateRequest's extra="forbid" already rejects the
    request outright (see test_forbidden_extra_field_rejected) - this test
    additionally proves the persisted row always reflects the JWT identity,
    never anything derived from the request body."""
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="jwtauth")
            other_company_id, other_user_id = await _seed_company_user(pool, label="jwtother")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            return company_id, user_id, other_company_id, other_user_id, receipt_id
        finally:
            await pool.close()

    company_id, user_id, other_company_id, other_user_id, receipt_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "x"},
        )
        assert response.status_code == 201, response.text

        async def fetch_row():
            pool = await _make_pool()
            try:
                return await pool.fetchrow(
                    "SELECT company_id, decided_by_user_id FROM ome_decision_memories WHERE id = $1",
                    UUID(response.json()["id"]),
                )
            finally:
                await pool.close()

        row = asyncio.run(fetch_row())
        assert str(row["company_id"]) == company_id
        assert str(row["company_id"]) != other_company_id
        assert str(row["decided_by_user_id"]) == user_id
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))

        asyncio.run(_run_cleanup(other_company_id, other_user_id))
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# AUDIT INVARIANTS (items 39-43)
# ---------------------------------------------------------------------------

def test_receipt_row_unchanged_after_decision_creation(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id = await _seed_company_user(pool, label="rcptimm")
            receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
            before = await pool.fetchrow("SELECT * FROM ome_reasoning_receipts WHERE id = $1", UUID(receipt_id))

            client = TestClient(app)
            _reset_stale_db_bindings(app, ai_engine)
            response = _post_decisions(
                client, _headers(company_id, user_id),
                {"reasoning_receipt_id": receipt_id, "decision_text": "x"},
            )
            assert response.status_code == 201, response.text

            after = await pool.fetchrow("SELECT * FROM ome_reasoning_receipts WHERE id = $1", UUID(receipt_id))
            assert dict(before) == dict(after), "item 39: receipt row byte-for-byte unchanged"

            assert after["evidence_refs"] == before["evidence_refs"], "item 40: no evidence_refs duplicated onto receipt"

            outcomes = await pool.fetchval(
                "SELECT count(*) FROM ome_outcome_memories WHERE company_id = $1", UUID(company_id)
            )
            assert outcomes == 0, "item 41: no OutcomeMemory row created"

            superseded = await pool.fetchval(
                "SELECT count(*) FROM ome_decision_memories WHERE company_id = $1 AND status = 'superseded'",
                UUID(company_id),
            )
            assert superseded == 0, "item 42: no supersession created"

            count = await _decision_count(pool, company_id=company_id)
            assert count == 1, "item 43: exactly one active decision"

            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            await pool.close()
            _reset_stale_db_bindings(app, ai_engine)

    _run(scenario())


# ---------------------------------------------------------------------------
# AI != HUMAN DECISION (item 44) - reuses the closed Slice 3A harness
# ---------------------------------------------------------------------------

def test_successful_ai_chat_alone_creates_zero_decision_rows(tmp_path, monkeypatch) -> None:
    company_id, user_id, file_id, chat_response, fake_client = _upload_and_chat(
        tmp_path=tmp_path, monkeypatch=monkeypatch, mode="cite_truth_and_cb", session_id="m8-s3b1-ai-only",
    )
    try:
        assert chat_response.status_code == 200, chat_response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _decision_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0, "item 44: a successful /ai/chat response alone never creates a decision"
    finally:

        async def cleanup_runner():
            pool = await _make_pool()
            try:
                # This harness seeds a full Dairtna company/department/file
                # (m8-s3a- namespace, not m8-s3b1-) - reuse the Slice 3A
                # module's own matching cleanup, not this file's leaner one.
                await _cleanup_slice3a(pool, company_id=company_id, user_id=user_id)
            finally:
                await pool.close()

        asyncio.run(cleanup_runner())
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# STRUCTURAL / SCOPE (items 45-50)
# ---------------------------------------------------------------------------

def test_request_model_has_exactly_four_allowed_fields() -> None:
    from app.api.decisions import DecisionCreateRequest

    assert set(DecisionCreateRequest.model_fields) == {
        "reasoning_receipt_id", "decision_text", "rationale", "situation_id",
    }


def test_request_model_forbids_extras() -> None:
    from app.api.decisions import DecisionCreateRequest

    assert DecisionCreateRequest.model_config.get("extra") == "forbid"


def test_no_endpoint_field_accepts_status_created_at_user_company_provenance() -> None:
    """The response model legitimately has some of these as OUTPUT fields
    (status/created_at); the REQUEST model (DecisionCreateRequest) must
    not accept any of them as input. Checked via model_fields directly -
    not source-text grepping, which would also match explanatory prose in
    the class's own docstring."""
    from app.api.decisions import DecisionCreateRequest

    forbidden = {
        "company_id", "decided_by_user_id", "created_by_user_id", "status",
        "created_at", "evidence_refs", "company_brain_refs", "response_snapshot",
        "supersedes_id", "superseded_by",
    }
    assert forbidden.isdisjoint(DecisionCreateRequest.model_fields.keys())


def test_no_record_outcome_endpoint_exists() -> None:
    import pathlib

    text = pathlib.Path("app/api/decisions.py").read_text(encoding="utf-8")
    assert "record_outcome" not in text
    assert "OutcomeMemoryService" not in text


def test_no_supersession_endpoint_exists() -> None:
    """No PUT/PATCH route, and supersede_decision is never called - the
    substring "supersede" legitimately appears in explanatory docstrings
    (describing what the request model forbids), so this checks actual
    route surface, not prose."""
    import pathlib

    text = pathlib.Path("app/api/decisions.py").read_text(encoding="utf-8")
    assert "supersede_decision" not in text
    assert "@router.put" not in text and "@router.patch" not in text


def test_migration_014_still_present() -> None:
    """M8 boundary invariant: 014_organizational_memory.sql remains the
    M8 OME foundation migration, present and unrenamed. (Historical
    note: this test was originally named test_no_migration_015 and
    asserted no migration 015 existed. That assertion became obsolete
    once Founder-approved M9 Slice 1 added migration 015 - M8's real
    invariant was always about migration 014 staying intact, not about
    permanently forbidding future milestones from adding migrations.)"""
    import pathlib

    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert "014_organizational_memory.sql" in migration_files


# ---------------------------------------------------------------------------
# Final zero-leftover verification for this module
# ---------------------------------------------------------------------------

def test_zero_slice3b1_leftovers_marker(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            companies = await pool.fetchval("SELECT count(*) FROM companies WHERE slug LIKE 'm8-s3b1-%'")
            users = await pool.fetchval("SELECT count(*) FROM users WHERE email LIKE 'm8-s3b1-%'")
            decisions = await pool.fetchval(
                "SELECT count(*) FROM ome_decision_memories d JOIN companies c ON c.id = d.company_id "
                "WHERE c.slug LIKE 'm8-s3b1-%'"
            )
            return companies, users, decisions
        finally:
            await pool.close()

    companies, users, decisions = _run(scenario())
    assert companies == 0
    assert users == 0
    assert decisions == 0
