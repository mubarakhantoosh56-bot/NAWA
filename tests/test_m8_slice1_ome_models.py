"""M8 Slice 1: OME domain model unit tests (no database required).

Proves app/ome/models/* construct from a DB-row-shaped dict, round-trip
through to_dict(), and reject invalid status/result_state values -
mirroring migrations/014_organizational_memory.sql's CHECK constraints at
the Python layer too, so an in-process caller gets the same fail-closed
behavior before ever reaching the database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.ome.models import DecisionMemory, OutcomeMemory, ReasoningReceipt


def test_reasoning_receipt_from_row_and_to_dict_round_trip() -> None:
    receipt_id, company_id, user_id = uuid4(), uuid4(), uuid4()
    now = datetime.now(timezone.utc)
    row = {
        "id": receipt_id,
        "company_id": company_id,
        "created_by_user_id": user_id,
        "session_id": "session-1",
        "created_at": now,
        "response_snapshot": {"ceo_text": "hello"},
        "evidence_refs": [{"type": "file", "id": str(uuid4())}],
    }

    receipt = ReasoningReceipt.from_row(row)

    assert receipt.id == receipt_id
    assert receipt.company_id == company_id
    assert receipt.created_by_user_id == user_id
    assert receipt.session_id == "session-1"
    assert receipt.response_snapshot == {"ceo_text": "hello"}

    payload = receipt.to_dict()
    assert payload["id"] == str(receipt_id)
    assert payload["company_id"] == str(company_id)
    assert payload["created_at"] == now.isoformat()


def test_reasoning_receipt_from_row_accepts_string_ids() -> None:
    """asyncpg returns real UUID objects, but a plain dict (e.g. from a
    JSON fixture) may carry string ids - from_row must accept both."""
    row = {
        "id": str(uuid4()),
        "company_id": str(uuid4()),
        "created_by_user_id": str(uuid4()),
        "session_id": None,
        "created_at": datetime.now(timezone.utc),
        "response_snapshot": {},
        "evidence_refs": [],
    }
    receipt = ReasoningReceipt.from_row(row)
    assert str(receipt.id) == row["id"]


def test_decision_memory_defaults_and_round_trip() -> None:
    decision_id, company_id, receipt_id, user_id = uuid4(), uuid4(), uuid4(), uuid4()
    now = datetime.now(timezone.utc)

    decision = DecisionMemory(
        id=decision_id,
        company_id=company_id,
        reasoning_receipt_id=receipt_id,
        decision_text="Assign veterinary follow-up",
        decided_by_user_id=user_id,
        decided_at=now,
        created_at=now,
    )

    assert decision.status == "active"
    assert decision.situation_id is None
    assert decision.superseded_by is None

    payload = decision.to_dict()
    assert payload["status"] == "active"
    assert payload["situation_id"] is None
    assert payload["decision_text"] == "Assign veterinary follow-up"


def test_decision_memory_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        DecisionMemory(
            id=uuid4(),
            company_id=uuid4(),
            reasoning_receipt_id=uuid4(),
            decision_text="x",
            decided_by_user_id=uuid4(),
            decided_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            status="bogus",
        )


def test_decision_memory_from_row() -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "reasoning_receipt_id": uuid4(),
        "decision_text": "x",
        "decided_by_user_id": uuid4(),
        "decided_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "status": "active",
        "situation_id": None,
        "rationale": None,
        "superseded_by": None,
    }
    decision = DecisionMemory.from_row(row)
    assert decision.id == row["id"]
    assert decision.status == "active"


def test_outcome_memory_rejects_invalid_result_state() -> None:
    with pytest.raises(ValueError):
        OutcomeMemory(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            outcome_summary="x",
            result_state="bogus",
            recorded_by_user_id=uuid4(),
            observed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )


def test_outcome_memory_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        OutcomeMemory(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            outcome_summary="x",
            result_state="unknown",
            recorded_by_user_id=uuid4(),
            observed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            status="bogus",
        )


def test_decision_memory_active_with_superseded_by_rejected() -> None:
    with pytest.raises(ValueError):
        DecisionMemory(
            id=uuid4(),
            company_id=uuid4(),
            reasoning_receipt_id=uuid4(),
            decision_text="x",
            decided_by_user_id=uuid4(),
            decided_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            status="active",
            superseded_by=uuid4(),
        )


def test_decision_memory_superseded_without_superseded_by_rejected() -> None:
    with pytest.raises(ValueError):
        DecisionMemory(
            id=uuid4(),
            company_id=uuid4(),
            reasoning_receipt_id=uuid4(),
            decision_text="x",
            decided_by_user_id=uuid4(),
            decided_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            status="superseded",
        )


def test_decision_memory_superseded_with_superseded_by_succeeds() -> None:
    decision = DecisionMemory(
        id=uuid4(),
        company_id=uuid4(),
        reasoning_receipt_id=uuid4(),
        decision_text="x",
        decided_by_user_id=uuid4(),
        decided_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        status="superseded",
        superseded_by=uuid4(),
    )
    assert decision.status == "superseded"


@pytest.mark.parametrize("field_name", ["id", "company_id", "reasoning_receipt_id", "decided_by_user_id"])
def test_decision_memory_from_row_rejects_none_for_required_fields(field_name: str) -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "reasoning_receipt_id": uuid4(),
        "decision_text": "x",
        "decided_by_user_id": uuid4(),
        "decided_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "status": "active",
    }
    row[field_name] = None
    with pytest.raises(ValueError):
        DecisionMemory.from_row(row)


@pytest.mark.parametrize("field_name", ["id", "company_id", "decision_memory_id", "recorded_by_user_id"])
def test_outcome_memory_from_row_rejects_none_for_required_fields(field_name: str) -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "decision_memory_id": uuid4(),
        "outcome_summary": "x",
        "result_state": "unknown",
        "recorded_by_user_id": uuid4(),
        "observed_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "status": "active",
    }
    row[field_name] = None
    with pytest.raises(ValueError):
        OutcomeMemory.from_row(row)


@pytest.mark.parametrize("field_name", ["id", "company_id", "created_by_user_id"])
def test_reasoning_receipt_from_row_rejects_none_for_required_fields(field_name: str) -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "created_by_user_id": uuid4(),
        "session_id": None,
        "created_at": datetime.now(timezone.utc),
        "response_snapshot": {},
        "evidence_refs": [],
    }
    row[field_name] = None
    with pytest.raises(ValueError):
        ReasoningReceipt.from_row(row)


def test_outcome_memory_active_with_superseded_by_rejected() -> None:
    with pytest.raises(ValueError):
        OutcomeMemory(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            outcome_summary="x",
            result_state="unknown",
            recorded_by_user_id=uuid4(),
            observed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            status="active",
            superseded_by=uuid4(),
        )


def test_outcome_memory_superseded_without_superseded_by_rejected() -> None:
    with pytest.raises(ValueError):
        OutcomeMemory(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            outcome_summary="x",
            result_state="unknown",
            recorded_by_user_id=uuid4(),
            observed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            status="superseded",
        )


def test_outcome_memory_from_row_and_to_dict() -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "decision_memory_id": uuid4(),
        "outcome_summary": "Mortality remained normal",
        "result_state": "positive",
        "recorded_by_user_id": uuid4(),
        "observed_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "status": "active",
        "superseded_by": None,
    }
    outcome = OutcomeMemory.from_row(row)
    assert outcome.result_state == "positive"

    payload = outcome.to_dict()
    assert payload["result_state"] == "positive"
    assert payload["superseded_by"] is None
