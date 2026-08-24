"""M8 Slice 3C-1: Human Outcome recording API tests (real Postgres, real
HTTP route via TestClient(app)).

Proves: POST /outcomes creates an OutcomeMemory row only from an explicit,
authenticated human call - never from a successful /ai/chat response or a
recorded DecisionMemory alone (items 42-43); the request model fails
closed on ANY undeclared field except observed_at (the one deliberately
client-authorable timestamp); company_id/recorded_by_user_id are always
JWT-derived, never client-supplied; the decision_memory_id company-scoping
is enforced via the existing, unmodified OutcomeMemoryService/repositories;
multiple simultaneously-active outcomes per decision remain allowed
(item 31-33); an outcome may be recorded against a superseded decision
(item 34); and no supersession/GET/list surface is reachable through this
API.
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

from tests.test_m7_slice1_upload_truth_bridge import _GoldenPermissionAuthService, _reset_stale_db_bindings
from tests.test_m8_slice3a_live_reasoning_receipts import _cleanup as _cleanup_slice3a
from tests.test_m8_slice3a_live_reasoning_receipts import _upload_and_chat
from tests.test_m8_slice3b1_human_decision_api import _post_decisions


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
        f"m8-s3c1-{label}-{uuid4().hex[:8]}", f"M8 Slice 3C-1 Test Company {label}",
    )
    user_row = await pool.fetchrow(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s3c1-{label}-{uuid4().hex[:8]}@example.com", f"M8 Slice 3C-1 Test User {label}",
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


async def _seed_decision(pool, *, company_id: str, receipt_id: str, user_id: str) -> str:
    decision_id = await pool.fetchval(
        """
        INSERT INTO ome_decision_memories
            (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
        VALUES ($1, $2, 'Test decision', $3, NOW())
        RETURNING id
        """,
        UUID(company_id), UUID(receipt_id), UUID(user_id),
    )
    return str(decision_id)


async def _supersede_decision(pool, *, company_id: str, old_decision_id: str, receipt_id: str, user_id: str) -> str:
    """Directly marks old_decision_id superseded and inserts a replacement,
    mirroring DecisionMemoryRepository.supersede_with_new_decision's shape
    (raw SQL here - no need to exercise that service for this fixture)."""
    new_decision_id = await pool.fetchval(
        """
        INSERT INTO ome_decision_memories
            (company_id, reasoning_receipt_id, decision_text, decided_by_user_id, decided_at)
        VALUES ($1, $2, 'Replacement decision', $3, NOW())
        RETURNING id
        """,
        UUID(company_id), UUID(receipt_id), UUID(user_id),
    )
    await pool.execute(
        "UPDATE ome_decision_memories SET status = 'superseded', superseded_by = $3 WHERE id = $1 AND company_id = $2",
        UUID(old_decision_id), UUID(company_id), new_decision_id,
    )
    return str(new_decision_id)


async def _cleanup(pool, *, company_id: str, user_id: str) -> None:
    _uuid = UUID
    await pool.execute("DELETE FROM ome_outcome_memories WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM ome_decision_memories WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM ome_reasoning_receipts WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM companies WHERE id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM users WHERE id = $1", _uuid(user_id))


async def _outcome_count(pool, *, company_id: str) -> int:
    return await pool.fetchval(
        "SELECT count(*) FROM ome_outcome_memories WHERE company_id = $1", UUID(company_id)
    )


def _headers(company_id: str, user_id: str) -> dict:
    token = create_token(company_id=company_id, user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def _post_outcomes(client, headers, body, *, permissions=("memory.write",)):
    # TestClient does not keep one persistent event loop alive across
    # separate .post() calls in this environment - a cached
    # app.state.auth_db_pool bound to a now-closed prior test's loop
    # breaks the next request (see
    # test_m7_slice1_upload_truth_bridge.py::_reset_stale_db_bindings's
    # own docstring for the full explanation). Reset immediately before
    # every request so a fresh pool binds to whichever loop is current.
    _reset_stale_db_bindings(app, ai_engine)
    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_GoldenPermissionAuthService(list(permissions))),
    ):
        response = client.post("/outcomes", headers=headers, json=body)
    _reset_stale_db_bindings(app, ai_engine)
    return response


async def _seed_company_receipt_decision(pool, *, label: str) -> tuple[str, str, str, str]:
    company_id, user_id = await _seed_company_user(pool, label=label)
    receipt_id = await _seed_receipt(pool, company_id=company_id, user_id=user_id)
    decision_id = await _seed_decision(pool, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
    return company_id, user_id, receipt_id, decision_id


# ---------------------------------------------------------------------------
# HAPPY PATH (items 1-9)
# ---------------------------------------------------------------------------

def test_happy_path_creates_exactly_one_active_outcome(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="happy")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "  Expansion delivered as planned.  ", "result_state": "positive"},
        )
        assert response.status_code == 201, response.text
        body = response.json()

        async def verify():
            pool = await _make_pool()
            try:
                count = await _outcome_count(pool, company_id=company_id)
                row = await pool.fetchrow(
                    "SELECT * FROM ome_outcome_memories WHERE company_id = $1", UUID(company_id)
                )
                return count, row
            finally:
                await pool.close()

        count, row = asyncio.run(verify())
        assert count == 1, "item 2"
        assert str(row["id"]) == body["id"]
        assert str(row["company_id"]) == company_id, "item 3"
        assert str(row["recorded_by_user_id"]) == user_id, "item 4"
        assert str(row["decision_memory_id"]) == decision_id, "item 5"
        assert row["outcome_summary"] == "Expansion delivered as planned.", "item 6 (trimmed per service semantics)"
        assert row["result_state"] == "positive", "item 7"
        assert row["status"] == "active", "item 8"
        assert row["created_at"] is not None, "item 9"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


async def _run_cleanup(company_id: str, user_id: str) -> None:
    pool = await _make_pool()
    try:
        await _cleanup(pool, company_id=company_id, user_id=user_id)
    finally:
        await pool.close()


# ---------------------------------------------------------------------------
# RESULT STATES (items 10-14)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("result_state", ["positive", "negative", "mixed", "unknown"])
def test_each_allowed_result_state_accepted(db_available, result_state) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label=f"rs-{result_state[:4]}")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": result_state},
        )
        assert response.status_code == 201, response.text
        assert response.json()["result_state"] == result_state
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_invalid_result_state_rejected(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="badresult")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "bogus"},
        )
        assert response.status_code == 422, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


# ---------------------------------------------------------------------------
# TEXT (items 15-17)
# ---------------------------------------------------------------------------

def test_blank_summary_returns_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="blanktext")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "   ", "result_state": "positive"},
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_non_string_summary_returns_422(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="nonstrtext")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": 123, "result_state": "positive"},
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_no_arbitrary_max_length_regression(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="longtext")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        long_text = "y" * 5000
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": long_text, "result_state": "positive"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["outcome_summary"] == long_text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


# ---------------------------------------------------------------------------
# DECISION SECURITY (items 18-21)
# ---------------------------------------------------------------------------

def test_nonexistent_decision_returns_404(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_user(pool, label="nodecision")
        finally:
            await pool.close()

    company_id, user_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": str(uuid4()), "outcome_summary": "x", "result_state": "positive"},
        )
        assert response.status_code == 404, response.text
        assert "another company" not in response.text.lower()

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_cross_company_decision_returns_same_404(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_a, user_a = await _seed_company_user(pool, label="crossa")
            company_b, user_b, receipt_b, decision_b = await _seed_company_receipt_decision(pool, label="crossb")
            return company_a, user_a, company_b, user_b, decision_b
        finally:
            await pool.close()

    company_a, user_a, company_b, user_b, decision_b = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_a, user_a),
            {"decision_memory_id": decision_b, "outcome_summary": "x", "result_state": "positive"},
        )
        assert response.status_code == 404, response.text
        assert "belongs to another company" not in response.text.lower()
        assert "exists" not in response.text.lower()

        async def counts():
            pool = await _make_pool()
            try:
                return (
                    await _outcome_count(pool, company_id=company_a),
                    await _outcome_count(pool, company_id=company_b),
                )
            finally:
                await pool.close()

        count_a, count_b = asyncio.run(counts())
        assert count_a == 0 and count_b == 0
    finally:
        asyncio.run(_run_cleanup(company_a, user_a))
        asyncio.run(_run_cleanup(company_b, user_b))


# ---------------------------------------------------------------------------
# AUTH/PERMISSION (items 22-24)
# ---------------------------------------------------------------------------

def test_user_with_memory_write_succeeds(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="haswrite")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
            permissions=["memory.write"],
        )
        assert response.status_code == 201, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_user_without_memory_write_returns_403(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="nowrite")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
            permissions=["ai.chat"],
        )
        assert response.status_code == 403, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_company_and_user_cannot_be_body_overridden(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id, receipt_id, decision_id = await _seed_company_receipt_decision(pool, label="jwtauth")
            other_company_id, other_user_id = await _seed_company_user(pool, label="jwtother")
            return company_id, user_id, decision_id, other_company_id, other_user_id
        finally:
            await pool.close()

    company_id, user_id, decision_id, other_company_id, other_user_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
        )
        assert response.status_code == 201, response.text

        async def fetch_row():
            pool = await _make_pool()
            try:
                return await pool.fetchrow(
                    "SELECT company_id, recorded_by_user_id FROM ome_outcome_memories WHERE id = $1",
                    UUID(response.json()["id"]),
                )
            finally:
                await pool.close()

        row = asyncio.run(fetch_row())
        assert str(row["company_id"]) == company_id
        assert str(row["company_id"]) != other_company_id
        assert str(row["recorded_by_user_id"]) == user_id
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))
        asyncio.run(_run_cleanup(other_company_id, other_user_id))


# ---------------------------------------------------------------------------
# OBSERVED TIME (items 25-30)
# ---------------------------------------------------------------------------

def test_omitted_observed_at_uses_server_now(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="omitobs")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        before = datetime.now(timezone.utc)
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
        )
        after = datetime.now(timezone.utc)
        assert response.status_code == 201, response.text
        observed_at = datetime.fromisoformat(response.json()["observed_at"].replace("Z", "+00:00"))
        assert before <= observed_at <= after
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_historical_timezone_aware_observed_at_accepted(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="histobs")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        historical = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive", "observed_at": historical},
        )
        assert response.status_code == 201, response.text
        returned = datetime.fromisoformat(response.json()["observed_at"].replace("Z", "+00:00"))
        assert abs((returned - datetime.fromisoformat(historical)).total_seconds()) < 1
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_future_observed_at_returns_422_and_zero_rows(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="futureobs")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive", "observed_at": future},
        )
        assert response.status_code == 422, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_naive_observed_at_returns_422_and_zero_rows(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="naiveobs")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        naive = datetime.now().isoformat()  # no tzinfo
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive", "observed_at": naive},
        )
        assert response.status_code == 422, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_malformed_observed_at_returns_422_and_zero_rows(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="malformobs")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive", "observed_at": "not-a-datetime"},
        )
        assert response.status_code == 422, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_created_at_cannot_be_client_authored(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="createdat")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {
                "decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive",
                "created_at": "2000-01-01T00:00:00Z",
            },
        )
        assert response.status_code == 422, response.text
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


# ---------------------------------------------------------------------------
# MULTIPLE OUTCOMES (items 31-33)
# ---------------------------------------------------------------------------

def test_two_active_outcomes_on_same_decision_both_succeed(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="multi")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        headers = _headers(company_id, user_id)
        first = _post_outcomes(
            client, headers,
            {"decision_memory_id": decision_id, "outcome_summary": "Early partial read: on track.", "result_state": "mixed"},
        )
        second = _post_outcomes(
            client, headers,
            {"decision_memory_id": decision_id, "outcome_summary": "Later fuller read: succeeded.", "result_state": "positive"},
        )
        assert first.status_code == 201, first.text
        assert second.status_code == 201, second.text
        assert first.json()["id"] != second.json()["id"]

        async def verify():
            pool = await _make_pool()
            try:
                rows = await pool.fetch(
                    "SELECT status, superseded_by FROM ome_outcome_memories WHERE company_id = $1", UUID(company_id)
                )
                return rows
            finally:
                await pool.close()

        rows = asyncio.run(verify())
        assert len(rows) == 2, "item 31/32"
        assert all(row["status"] == "active" for row in rows), "item 32"
        assert all(row["superseded_by"] is None for row in rows), "item 33: neither auto-supersedes the other"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


# ---------------------------------------------------------------------------
# SUPERSEDED DECISION (item 34)
# ---------------------------------------------------------------------------

def test_outcome_allowed_on_superseded_decision(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            company_id, user_id, receipt_id, decision_id = await _seed_company_receipt_decision(pool, label="superseded")
            await _supersede_decision(pool, company_id=company_id, old_decision_id=decision_id, receipt_id=receipt_id, user_id=user_id)
            return company_id, user_id, decision_id
        finally:
            await pool.close()

    company_id, user_id, old_decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": old_decision_id, "outcome_summary": "Outcome of the original decision.", "result_state": "negative"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["decision_memory_id"] == old_decision_id
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


# ---------------------------------------------------------------------------
# TRUST BOUNDARY (items 35-39)
# ---------------------------------------------------------------------------

FORBIDDEN_EXTRA_FIELDS = {
    "company_id": lambda: str(uuid4()),
    "recorded_by_user_id": lambda: str(uuid4()),
    "created_by_user_id": lambda: str(uuid4()),
    "decided_by_user_id": lambda: str(uuid4()),
    "user_id": lambda: str(uuid4()),
    "evidence_refs": lambda: [],
    "company_brain_refs": lambda: [],
    "response_snapshot": lambda: {"ceo_text": "x"},
    "status": lambda: "active",
    "created_at": lambda: "2020-01-01T00:00:00Z",
    "superseded_by": lambda: str(uuid4()),
    "supersedes_id": lambda: str(uuid4()),
    "old_outcome_id": lambda: str(uuid4()),
}


@pytest.mark.parametrize("field_name", sorted(FORBIDDEN_EXTRA_FIELDS))
def test_forbidden_extra_field_rejected(db_available, field_name) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label=f"ext-{field_name[:6]}")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        body = {
            "decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive",
            field_name: FORBIDDEN_EXTRA_FIELDS[field_name](),
        }
        response = _post_outcomes(client, _headers(company_id, user_id), body)
        assert response.status_code == 422, response.text  # item 35

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0, "item 36"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_request_model_has_exactly_four_allowed_fields() -> None:
    from app.api.outcomes import OutcomeCreateRequest

    assert set(OutcomeCreateRequest.model_fields) == {
        "decision_memory_id", "outcome_summary", "result_state", "observed_at",
    }  # item 37


def test_request_model_forbids_extras() -> None:
    from app.api.outcomes import OutcomeCreateRequest

    assert OutcomeCreateRequest.model_config.get("extra") == "forbid"


def test_no_evidence_refs_field_on_outcome_model() -> None:
    from app.ome.models import OutcomeMemory
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(OutcomeMemory)}
    assert "evidence_refs" not in field_names  # item 38


def test_response_never_echoes_receipt_or_company_brain_provenance(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="noprov")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id = asyncio.run(seed())
    try:
        client = TestClient(app)
        response = _post_outcomes(
            client, _headers(company_id, user_id),
            {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
        )
        assert response.status_code == 201, response.text
        body_keys = set(response.json().keys())
        assert body_keys == {
            "id", "decision_memory_id", "outcome_summary", "result_state", "status", "observed_at", "created_at",
        }, "item 39: no evidence_refs/provenance echoed"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


# ---------------------------------------------------------------------------
# IMMUTABILITY (items 40-41)
# ---------------------------------------------------------------------------

def test_decision_and_receipt_rows_unchanged_after_outcome_creation(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id, receipt_id, decision_id = await _seed_company_receipt_decision(pool, label="immutable")
            decision_before = await pool.fetchrow("SELECT * FROM ome_decision_memories WHERE id = $1", UUID(decision_id))
            receipt_before = await pool.fetchrow("SELECT * FROM ome_reasoning_receipts WHERE id = $1", UUID(receipt_id))

            client = TestClient(app)
            response = _post_outcomes(
                client, _headers(company_id, user_id),
                {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
            )
            assert response.status_code == 201, response.text

            decision_after = await pool.fetchrow("SELECT * FROM ome_decision_memories WHERE id = $1", UUID(decision_id))
            receipt_after = await pool.fetchrow("SELECT * FROM ome_reasoning_receipts WHERE id = $1", UUID(receipt_id))
            assert dict(decision_before) == dict(decision_after), "item 40"
            assert dict(receipt_before) == dict(receipt_after), "item 41"

            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# AUTOMATION BOUNDARY (items 42-44)
# ---------------------------------------------------------------------------

def test_successful_ai_chat_alone_creates_zero_outcome_rows(tmp_path, monkeypatch) -> None:
    company_id, user_id, file_id, chat_response, fake_client = _upload_and_chat(
        tmp_path=tmp_path, monkeypatch=monkeypatch, mode="cite_truth_and_cb", session_id="m8-s3c1-ai-only",
    )
    try:
        assert chat_response.status_code == 200, chat_response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0, "item 42"
    finally:

        async def cleanup_runner():
            pool = await _make_pool()
            try:
                await _cleanup_slice3a(pool, company_id=company_id, user_id=user_id)
            finally:
                await pool.close()

        asyncio.run(cleanup_runner())


def test_recording_a_decision_alone_creates_zero_outcome_rows(db_available) -> None:
    async def seed():
        pool = await _make_pool()
        try:
            return await _seed_company_receipt_decision(pool, label="decisiononly")
        finally:
            await pool.close()

    company_id, user_id, receipt_id, decision_id_precreated = asyncio.run(seed())
    try:
        _reset_stale_db_bindings(app, ai_engine)
        client = TestClient(app)
        response = _post_decisions(
            client, _headers(company_id, user_id),
            {"reasoning_receipt_id": receipt_id, "decision_text": "A fresh, separate decision."},
        )
        _reset_stale_db_bindings(app, ai_engine)
        assert response.status_code == 201, response.text

        async def count():
            pool = await _make_pool()
            try:
                return await _outcome_count(pool, company_id=company_id)
            finally:
                await pool.close()

        assert asyncio.run(count()) == 0, "item 43"
    finally:
        asyncio.run(_run_cleanup(company_id, user_id))


def test_outcome_creation_does_not_mutate_current_truth(db_available) -> None:
    """item 44: recording an outcome never writes anything into
    memory_events/memory_facts (the closest thing this codebase has to
    'current Truth' ingestion) - the route only ever calls
    OutcomeMemoryService.record_outcome, which only touches
    ome_outcome_memories."""
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id, receipt_id, decision_id = await _seed_company_receipt_decision(pool, label="notruth")
            events_before = await pool.fetchval("SELECT count(*) FROM memory_events WHERE company_id = $1", company_id)
            facts_before = await pool.fetchval("SELECT count(*) FROM memory_facts WHERE company_id = $1", company_id)

            client = TestClient(app)
            response = _post_outcomes(
                client, _headers(company_id, user_id),
                {"decision_memory_id": decision_id, "outcome_summary": "x", "result_state": "positive"},
            )
            assert response.status_code == 201, response.text

            events_after = await pool.fetchval("SELECT count(*) FROM memory_events WHERE company_id = $1", company_id)
            facts_after = await pool.fetchval("SELECT count(*) FROM memory_facts WHERE company_id = $1", company_id)
            assert events_before == events_after == 0
            assert facts_before == facts_after == 0

            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# ROUTE SCOPE (items 45-48)
# ---------------------------------------------------------------------------

def test_no_get_outcome_route() -> None:
    from app.main import app as fastapi_app

    outcome_routes = [(r.path, sorted(r.methods)) for r in fastapi_app.routes if getattr(r, "path", "").startswith("/outcomes")]
    assert outcome_routes == [("/outcomes", ["POST"])]  # items 45/47


def test_no_outcome_supersession_route() -> None:
    """No PUT/PATCH/GET route, and supersede_outcome is never CALLED - the
    substring "supersede_outcome" legitimately appears in the module's own
    explanatory docstring (describing what stays unexposed), so this
    checks actual route surface/service usage, not prose."""
    import pathlib

    text = pathlib.Path("app/api/outcomes.py").read_text(encoding="utf-8")
    assert "outcome_service.supersede_outcome" not in text
    assert "@router.put" not in text and "@router.patch" not in text
    assert "@router.get" not in text  # item 46


def test_no_migration_015() -> None:
    import pathlib

    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert not any(name.startswith("015") for name in migration_files)  # item 48


# ---------------------------------------------------------------------------
# SEMANTICS (items 49-50)
# ---------------------------------------------------------------------------

def test_no_row_vs_explicit_unknown_remain_distinguishable(db_available) -> None:
    """item 49: absence of any OutcomeMemory row means 'nothing recorded
    yet'; a real row with result_state='unknown' means a human explicitly
    asserted the result cannot yet be determined - these must never
    collapse into the same observable state."""
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id, receipt_id, decision_id = await _seed_company_receipt_decision(pool, label="unknownvsnone")

            before_count = await _outcome_count(pool, company_id=company_id)
            assert before_count == 0, "no row recorded yet"

            client = TestClient(app)
            response = _post_outcomes(
                client, _headers(company_id, user_id),
                {"decision_memory_id": decision_id, "outcome_summary": "Result cannot yet be determined.", "result_state": "unknown"},
            )
            assert response.status_code == 201, response.text
            assert response.json()["result_state"] == "unknown"

            after_count = await _outcome_count(pool, company_id=company_id)
            assert after_count == 1, "a real row now exists, distinct from the earlier zero-row state"

            row = await pool.fetchrow("SELECT result_state FROM ome_outcome_memories WHERE company_id = $1", UUID(company_id))
            assert row["result_state"] == "unknown"

            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Final zero-leftover verification for this module (item 50)
# ---------------------------------------------------------------------------

def test_zero_slice3c1_leftovers_marker(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            companies = await pool.fetchval("SELECT count(*) FROM companies WHERE slug LIKE 'm8-s3c1-%'")
            users = await pool.fetchval("SELECT count(*) FROM users WHERE email LIKE 'm8-s3c1-%'")
            outcomes = await pool.fetchval(
                "SELECT count(*) FROM ome_outcome_memories o JOIN companies c ON c.id = o.company_id "
                "WHERE c.slug LIKE 'm8-s3c1-%'"
            )
            decisions = await pool.fetchval(
                "SELECT count(*) FROM ome_decision_memories d JOIN companies c ON c.id = d.company_id "
                "WHERE c.slug LIKE 'm8-s3c1-%'"
            )
            receipts = await pool.fetchval(
                "SELECT count(*) FROM ome_reasoning_receipts r JOIN companies c ON c.id = r.company_id "
                "WHERE c.slug LIKE 'm8-s3c1-%'"
            )
            return companies, users, outcomes, decisions, receipts
        finally:
            await pool.close()

    companies, users, outcomes, decisions, receipts = _run(scenario())
    assert companies == 0
    assert users == 0
    assert outcomes == 0
    assert decisions == 0
    assert receipts == 0
