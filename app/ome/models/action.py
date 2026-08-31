"""Action: one human-governed unit of execution work, always anchored to
a DecisionMemory.

M9 Slice 1 scope: persistence/domain model only, matching
migrations/015_decision_execution_foundation.sql's ome_actions table.
No repository, service, API, or write path exists yet - mirrors M8
Slice 1 exactly (see NAWA_M9_DECISION_EXECUTION_FOUNDATION_ARCHITECTURE_
CONTRACT_v1.md Sec 28, M9 Slice 1).

Execution state (this model) and Outcome state (OutcomeMemory) are
deliberately different vocabularies in different tables (Architecture
Contract Sec 3, Domain Laws: "Execution State != Outcome"). This model
never reads or writes ome_outcome_memories, and carries no
reasoning_receipt_id or situation_id of its own - provenance flows only
by lineage through decision_memory_id (Sec 12).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

ACTION_STATUSES = frozenset({"pending", "in_progress", "completed", "cancelled"})


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
class Action:
    """One row of ome_actions - the CURRENT execution state of one
    human-authorized unit of work against exactly one DecisionMemory."""

    id: UUID
    company_id: UUID
    decision_memory_id: UUID
    title: str
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    status: str = "pending"
    instructions: str | None = None
    assigned_user_id: UUID | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.status not in ACTION_STATUSES:
            raise ValueError(f"Invalid Action status: {self.status!r}")
        if not self.title or not self.title.strip():
            raise ValueError("Action title cannot be blank")
        # Mirrors migrations/015_decision_execution_foundation.sql's
        # chk_ome_actions_completed_at_consistent /
        # chk_ome_actions_cancelled_at_consistent: fail closed in
        # Python too, not only at the database boundary.
        if self.status == "completed" and self.completed_at is None:
            raise ValueError("A 'completed' Action must have completed_at set")
        if self.status != "completed" and self.completed_at is not None:
            raise ValueError("Only a 'completed' Action may have completed_at set")
        if self.status == "cancelled" and self.cancelled_at is None:
            raise ValueError("A 'cancelled' Action must have cancelled_at set")
        if self.status != "cancelled" and self.cancelled_at is not None:
            raise ValueError("Only a 'cancelled' Action may have cancelled_at set")

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Action":
        """Construct from a database row (asyncpg Record or plain dict)."""
        return cls(
            id=_required_uuid(row["id"], field_name="id"),
            company_id=_required_uuid(row["company_id"], field_name="company_id"),
            decision_memory_id=_required_uuid(row["decision_memory_id"], field_name="decision_memory_id"),
            title=row["title"],
            created_by_user_id=_required_uuid(row["created_by_user_id"], field_name="created_by_user_id"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=row.get("status", "pending"),
            instructions=row.get("instructions"),
            assigned_user_id=_optional_uuid(row.get("assigned_user_id")),
            completed_at=row.get("completed_at"),
            cancelled_at=row.get("cancelled_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        payload["id"] = str(self.id)
        payload["company_id"] = str(self.company_id)
        payload["decision_memory_id"] = str(self.decision_memory_id)
        payload["created_by_user_id"] = str(self.created_by_user_id)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        payload["assigned_user_id"] = str(self.assigned_user_id) if self.assigned_user_id else None
        payload["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        payload["cancelled_at"] = self.cancelled_at.isoformat() if self.cancelled_at else None
        return payload
