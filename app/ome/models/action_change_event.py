"""ActionChangeEvent: one immutable row of the append-only Action change
ledger.

M9 Slice 1 scope: persistence/domain model only, matching
migrations/015_decision_execution_foundation.sql's
ome_action_change_events table. No repository, service, API, or write
path exists yet.

Exactly two change_type values exist: 'status' and 'assignment'
(Founder-ratified Option B, Architecture Contract Sec 9.4). A single
discriminated ledger, never two separate tables and never a generic
event platform - a row represents EITHER a status transition OR an
assignment change, never both and never neither (Sec 9.5 anti-creep
guard: closed enum, no payload/JSONB/free-text column, ever).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.ome.models.action import ACTION_STATUSES

CHANGE_TYPES = frozenset({"status", "assignment"})


def _required_uuid(value: Any, *, field_name: str) -> UUID:
    """Parse a REQUIRED identifier field. Raises ValueError if None or not
    a valid UUID/UUID-string - a required field silently becoming None
    would be a data-integrity bug, never a valid state to construct."""
    if value is None:
        raise ValueError(f"{field_name} is required and cannot be None")
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _optional_uuid(value: Any) -> UUID | None:
    """Parse a genuinely OPTIONAL identifier field. None stays None."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


@dataclass(frozen=True)
class ActionChangeEvent:
    """One row of ome_action_change_events. Append-only: this model has
    no update/delete semantics - a row is written once and never
    changed (application/repository-enforced; see migrations/
    015_decision_execution_foundation.sql's header comment)."""

    id: UUID
    company_id: UUID
    action_id: UUID
    change_type: str
    changed_by_user_id: UUID
    changed_at: datetime
    from_status: str | None = None
    to_status: str | None = None
    from_assigned_user_id: UUID | None = None
    to_assigned_user_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.change_type not in CHANGE_TYPES:
            raise ValueError(f"Invalid ActionChangeEvent change_type: {self.change_type!r}")

        # Mirrors migrations/015_decision_execution_foundation.sql's
        # chk_ome_action_change_events_shape: a row is EITHER a status
        # event OR an assignment event, never both, never neither -
        # fail closed in Python too, not only at the database boundary.
        if self.change_type == "status":
            if self.to_status is None:
                raise ValueError("A 'status' change event must have to_status set")
            if self.from_assigned_user_id is not None or self.to_assigned_user_id is not None:
                raise ValueError("A 'status' change event cannot carry assignment fields")
            if self.from_status is not None and self.from_status == self.to_status:
                raise ValueError("A 'status' change event cannot be a no-op self-transition")
        else:  # change_type == "assignment"
            if self.from_status is not None or self.to_status is not None:
                raise ValueError("An 'assignment' change event cannot carry status fields")
            if self.from_assigned_user_id == self.to_assigned_user_id:
                raise ValueError(
                    "An 'assignment' change event cannot be a no-op "
                    "(from_assigned_user_id == to_assigned_user_id, including NULL == NULL)"
                )

        if self.to_status is not None and self.to_status not in ACTION_STATUSES:
            raise ValueError(f"Invalid ActionChangeEvent to_status: {self.to_status!r}")
        if self.from_status is not None and self.from_status not in ACTION_STATUSES:
            raise ValueError(f"Invalid ActionChangeEvent from_status: {self.from_status!r}")

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ActionChangeEvent":
        """Construct from a database row (asyncpg Record or plain dict)."""
        return cls(
            id=_required_uuid(row["id"], field_name="id"),
            company_id=_required_uuid(row["company_id"], field_name="company_id"),
            action_id=_required_uuid(row["action_id"], field_name="action_id"),
            change_type=row["change_type"],
            changed_by_user_id=_required_uuid(row["changed_by_user_id"], field_name="changed_by_user_id"),
            changed_at=row["changed_at"],
            from_status=row.get("from_status"),
            to_status=row.get("to_status"),
            from_assigned_user_id=_optional_uuid(row.get("from_assigned_user_id")),
            to_assigned_user_id=_optional_uuid(row.get("to_assigned_user_id")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        payload["id"] = str(self.id)
        payload["company_id"] = str(self.company_id)
        payload["action_id"] = str(self.action_id)
        payload["changed_by_user_id"] = str(self.changed_by_user_id)
        payload["changed_at"] = self.changed_at.isoformat()
        payload["from_assigned_user_id"] = (
            str(self.from_assigned_user_id) if self.from_assigned_user_id else None
        )
        payload["to_assigned_user_id"] = str(self.to_assigned_user_id) if self.to_assigned_user_id else None
        return payload
