"""M9 Slice 1: Action / ActionChangeEvent domain model unit tests (no
database required).

Proves app/ome/models/action.py and app/ome/models/action_change_event.py
construct from a DB-row-shaped dict, round-trip through to_dict(), and
reject invalid status/change_type/shape values - mirroring
migrations/015_decision_execution_foundation.sql's CHECK constraints at
the Python layer too, so an in-process caller gets the same fail-closed
behavior before ever reaching the database. Structure mirrors
tests/test_m8_slice1_ome_models.py exactly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.ome.models import Action, ActionChangeEvent


# ---------------------------------------------------------------------------
# Action - construction, defaults, round-trip
# ---------------------------------------------------------------------------


def test_action_defaults_and_round_trip() -> None:
    action_id, company_id, decision_id, user_id = uuid4(), uuid4(), uuid4(), uuid4()
    now = datetime.now(timezone.utc)

    action = Action(
        id=action_id,
        company_id=company_id,
        decision_memory_id=decision_id,
        title="Follow up with the vet",
        created_by_user_id=user_id,
        created_at=now,
        updated_at=now,
    )

    assert action.status == "pending"
    assert action.instructions is None
    assert action.assigned_user_id is None
    assert action.completed_at is None
    assert action.cancelled_at is None

    payload = action.to_dict()
    assert payload["id"] == str(action_id)
    assert payload["company_id"] == str(company_id)
    assert payload["decision_memory_id"] == str(decision_id)
    assert payload["status"] == "pending"
    assert payload["assigned_user_id"] is None
    assert payload["completed_at"] is None
    assert payload["cancelled_at"] is None


def test_action_from_row() -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "decision_memory_id": uuid4(),
        "title": "Ship the fix",
        "instructions": "Deploy to staging first",
        "created_by_user_id": uuid4(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "status": "pending",
        "assigned_user_id": None,
        "completed_at": None,
        "cancelled_at": None,
    }
    action = Action.from_row(row)
    assert action.id == row["id"]
    assert action.status == "pending"
    assert action.instructions == "Deploy to staging first"


def test_action_from_row_accepts_string_ids() -> None:
    """asyncpg returns real UUID objects, but a plain dict (e.g. from a
    JSON fixture) may carry string ids - from_row must accept both."""
    row = {
        "id": str(uuid4()),
        "company_id": str(uuid4()),
        "decision_memory_id": str(uuid4()),
        "title": "x",
        "instructions": None,
        "created_by_user_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "status": "pending",
        "assigned_user_id": str(uuid4()),
        "completed_at": None,
        "cancelled_at": None,
    }
    action = Action.from_row(row)
    assert str(action.id) == row["id"]
    assert str(action.assigned_user_id) == row["assigned_user_id"]


@pytest.mark.parametrize("field_name", ["id", "company_id", "decision_memory_id", "created_by_user_id"])
def test_action_from_row_rejects_none_for_required_fields(field_name: str) -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "decision_memory_id": uuid4(),
        "title": "x",
        "instructions": None,
        "created_by_user_id": uuid4(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "status": "pending",
    }
    row[field_name] = None
    with pytest.raises(ValueError):
        Action.from_row(row)


# ---------------------------------------------------------------------------
# Action - status enum
# ---------------------------------------------------------------------------


def test_action_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title="x",
            created_by_user_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="bogus",
        )


@pytest.mark.parametrize("status", ["pending", "in_progress", "completed", "cancelled"])
def test_action_accepts_every_mvp_status(status: str) -> None:
    now = datetime.now(timezone.utc)
    kwargs: dict[str, object] = {}
    if status == "completed":
        kwargs["completed_at"] = now
    if status == "cancelled":
        kwargs["cancelled_at"] = now

    action = Action(
        id=uuid4(),
        company_id=uuid4(),
        decision_memory_id=uuid4(),
        title="x",
        created_by_user_id=uuid4(),
        created_at=now,
        updated_at=now,
        status=status,
        **kwargs,
    )
    assert action.status == status


# ---------------------------------------------------------------------------
# Action - title non-blank
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_action_rejects_blank_title(title: str) -> None:
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title=title,
            created_by_user_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Action - terminal timestamp invariants (mirrors the migration's
# chk_ome_actions_completed_at_consistent / chk_ome_actions_cancelled_at_consistent)
# ---------------------------------------------------------------------------


def test_action_completed_without_completed_at_rejected() -> None:
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title="x",
            created_by_user_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="completed",
        )


def test_action_completed_at_set_while_pending_rejected() -> None:
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title="x",
            created_by_user_id=uuid4(),
            created_at=now,
            updated_at=now,
            status="pending",
            completed_at=now,
        )


def test_action_cancelled_without_cancelled_at_rejected() -> None:
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title="x",
            created_by_user_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="cancelled",
        )


def test_action_cancelled_at_set_while_in_progress_rejected() -> None:
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title="x",
            created_by_user_id=uuid4(),
            created_at=now,
            updated_at=now,
            status="in_progress",
            cancelled_at=now,
        )


def test_action_completed_and_cancelled_at_together_rejected() -> None:
    """A completed Action carrying a cancelled_at is not a valid state,
    regardless of which CHECK fires first."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        Action(
            id=uuid4(),
            company_id=uuid4(),
            decision_memory_id=uuid4(),
            title="x",
            created_by_user_id=uuid4(),
            created_at=now,
            updated_at=now,
            status="completed",
            completed_at=now,
            cancelled_at=now,
        )


# ---------------------------------------------------------------------------
# Action - nullable assigned_user_id
# ---------------------------------------------------------------------------


def test_action_assigned_user_id_defaults_to_none() -> None:
    now = datetime.now(timezone.utc)
    action = Action(
        id=uuid4(),
        company_id=uuid4(),
        decision_memory_id=uuid4(),
        title="x",
        created_by_user_id=uuid4(),
        created_at=now,
        updated_at=now,
    )
    assert action.assigned_user_id is None
    assert action.to_dict()["assigned_user_id"] is None


def test_action_assigned_user_id_can_be_set() -> None:
    now = datetime.now(timezone.utc)
    assignee = uuid4()
    action = Action(
        id=uuid4(),
        company_id=uuid4(),
        decision_memory_id=uuid4(),
        title="x",
        created_by_user_id=uuid4(),
        created_at=now,
        updated_at=now,
        assigned_user_id=assignee,
    )
    assert action.assigned_user_id == assignee
    assert action.to_dict()["assigned_user_id"] == str(assignee)


# ---------------------------------------------------------------------------
# ActionChangeEvent - status event shape
# ---------------------------------------------------------------------------


def test_status_event_initial_creation_round_trip() -> None:
    """The creation event: NULL -> pending."""
    event_id, company_id, action_id, user_id = uuid4(), uuid4(), uuid4(), uuid4()
    now = datetime.now(timezone.utc)

    event = ActionChangeEvent(
        id=event_id,
        company_id=company_id,
        action_id=action_id,
        change_type="status",
        changed_by_user_id=user_id,
        changed_at=now,
        from_status=None,
        to_status="pending",
    )

    assert event.from_status is None
    assert event.to_status == "pending"
    assert event.from_assigned_user_id is None
    assert event.to_assigned_user_id is None

    payload = event.to_dict()
    assert payload["change_type"] == "status"
    assert payload["from_status"] is None
    assert payload["to_status"] == "pending"


def test_status_event_genuine_transition_succeeds() -> None:
    now = datetime.now(timezone.utc)
    event = ActionChangeEvent(
        id=uuid4(),
        company_id=uuid4(),
        action_id=uuid4(),
        change_type="status",
        changed_by_user_id=uuid4(),
        changed_at=now,
        from_status="pending",
        to_status="in_progress",
    )
    assert event.from_status == "pending"
    assert event.to_status == "in_progress"


def test_status_event_requires_to_status() -> None:
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="status",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            to_status=None,
        )


def test_status_event_rejects_self_transition() -> None:
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="status",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            from_status="pending",
            to_status="pending",
        )


def test_status_event_rejects_invalid_to_status() -> None:
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="status",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            to_status="bogus",
        )


def test_status_event_rejects_invalid_from_status() -> None:
    """Issue 2 correction: from_status must be constrained to the M9
    status vocabulary too, not just to_status - otherwise a historical
    audit row like 'bogus' -> 'pending' would be representable."""
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="status",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            from_status="bogus",
            to_status="in_progress",
        )


@pytest.mark.parametrize("from_status", ["pending", "in_progress", "completed", "cancelled"])
def test_status_event_accepts_every_valid_from_status(from_status: str) -> None:
    """Positive control: every valid M9 status is accepted as a
    from_status, so long as the event shape is otherwise valid (not a
    self-transition)."""
    to_status = "cancelled" if from_status != "cancelled" else "completed"
    event = ActionChangeEvent(
        id=uuid4(),
        company_id=uuid4(),
        action_id=uuid4(),
        change_type="status",
        changed_by_user_id=uuid4(),
        changed_at=datetime.now(timezone.utc),
        from_status=from_status,
        to_status=to_status,
    )
    assert event.from_status == from_status


def test_status_event_cannot_carry_assignment_fields() -> None:
    """Discriminator violation: a status event must not also look like
    an assignment event."""
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="status",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            to_status="in_progress",
            to_assigned_user_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# ActionChangeEvent - assignment event shape
# ---------------------------------------------------------------------------


def test_assignment_event_initial_when_created_assigned() -> None:
    """The initial assignment event when an Action is created with an
    assignee: NULL -> assigned_user_id."""
    assignee = uuid4()
    event = ActionChangeEvent(
        id=uuid4(),
        company_id=uuid4(),
        action_id=uuid4(),
        change_type="assignment",
        changed_by_user_id=uuid4(),
        changed_at=datetime.now(timezone.utc),
        from_assigned_user_id=None,
        to_assigned_user_id=assignee,
    )
    assert event.from_assigned_user_id is None
    assert event.to_assigned_user_id == assignee


def test_assignment_event_reassignment_user_to_user_succeeds() -> None:
    ahmed, mohammed = uuid4(), uuid4()
    event = ActionChangeEvent(
        id=uuid4(),
        company_id=uuid4(),
        action_id=uuid4(),
        change_type="assignment",
        changed_by_user_id=uuid4(),
        changed_at=datetime.now(timezone.utc),
        from_assigned_user_id=ahmed,
        to_assigned_user_id=mohammed,
    )
    assert event.from_assigned_user_id == ahmed
    assert event.to_assigned_user_id == mohammed


def test_assignment_event_clear_to_none_succeeds() -> None:
    assignee = uuid4()
    event = ActionChangeEvent(
        id=uuid4(),
        company_id=uuid4(),
        action_id=uuid4(),
        change_type="assignment",
        changed_by_user_id=uuid4(),
        changed_at=datetime.now(timezone.utc),
        from_assigned_user_id=assignee,
        to_assigned_user_id=None,
    )
    assert event.from_assigned_user_id == assignee
    assert event.to_assigned_user_id is None


def test_assignment_event_rejects_fake_null_to_null() -> None:
    """No fake NULL -> NULL assignment event when an Action is created
    unassigned - there is nothing to record."""
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="assignment",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            from_assigned_user_id=None,
            to_assigned_user_id=None,
        )


def test_assignment_event_rejects_same_user_no_op() -> None:
    same_user = uuid4()
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="assignment",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            from_assigned_user_id=same_user,
            to_assigned_user_id=same_user,
        )


def test_assignment_event_cannot_carry_status_fields() -> None:
    """Discriminator violation: an assignment event must not also look
    like a status event."""
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="assignment",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
            from_assigned_user_id=None,
            to_assigned_user_id=uuid4(),
            to_status="pending",
        )


# ---------------------------------------------------------------------------
# ActionChangeEvent - change_type discriminator
# ---------------------------------------------------------------------------


def test_change_event_rejects_invalid_change_type() -> None:
    with pytest.raises(ValueError):
        ActionChangeEvent(
            id=uuid4(),
            company_id=uuid4(),
            action_id=uuid4(),
            change_type="bogus",
            changed_by_user_id=uuid4(),
            changed_at=datetime.now(timezone.utc),
        )


def test_change_event_from_row_status() -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "action_id": uuid4(),
        "change_type": "status",
        "changed_by_user_id": uuid4(),
        "changed_at": datetime.now(timezone.utc),
        "from_status": None,
        "to_status": "pending",
        "from_assigned_user_id": None,
        "to_assigned_user_id": None,
    }
    event = ActionChangeEvent.from_row(row)
    assert event.change_type == "status"
    assert event.to_status == "pending"


def test_change_event_from_row_assignment() -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "action_id": uuid4(),
        "change_type": "assignment",
        "changed_by_user_id": uuid4(),
        "changed_at": datetime.now(timezone.utc),
        "from_status": None,
        "to_status": None,
        "from_assigned_user_id": None,
        "to_assigned_user_id": str(uuid4()),
    }
    event = ActionChangeEvent.from_row(row)
    assert event.change_type == "assignment"
    assert event.from_assigned_user_id is None
    assert event.to_assigned_user_id is not None


@pytest.mark.parametrize("field_name", ["id", "company_id", "action_id", "changed_by_user_id"])
def test_change_event_from_row_rejects_none_for_required_fields(field_name: str) -> None:
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "action_id": uuid4(),
        "change_type": "status",
        "changed_by_user_id": uuid4(),
        "changed_at": datetime.now(timezone.utc),
        "from_status": None,
        "to_status": "pending",
    }
    row[field_name] = None
    with pytest.raises(ValueError):
        ActionChangeEvent.from_row(row)
