"""DecisionMemory: one explicit HUMAN decision, bound to the
ReasoningReceipt it was made in response to.

M8 Slice 1 scope: persistence/domain model only, matching
migrations/014_organizational_memory.sql's ome_decision_memories table.
No repository, service, or write path exists yet.

Authoritative evidence provenance for a decision comes ONLY through
reasoning_receipt_id (decision -> receipt -> evidence_refs) - this model
deliberately carries no evidence_refs field of its own (M8 OME Provenance
Integrity Decision, Table 2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

DECISION_STATUSES = frozenset({"active", "superseded"})


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
class DecisionMemory:
    """One row of ome_decision_memories."""

    id: UUID
    company_id: UUID
    reasoning_receipt_id: UUID
    decision_text: str
    decided_by_user_id: UUID
    decided_at: datetime
    created_at: datetime
    status: str = "active"
    situation_id: UUID | None = None
    rationale: str | None = None
    superseded_by: UUID | None = None

    def __post_init__(self) -> None:
        if self.status not in DECISION_STATUSES:
            raise ValueError(f"Invalid DecisionMemory status: {self.status!r}")
        # Mirrors migrations/014_organizational_memory.sql's
        # chk_ome_decision_memories_status_supersession_consistent: an
        # 'active' decision never carries a superseded_by, and a
        # 'superseded' decision always does. Fail closed in Python too,
        # not only at the database boundary.
        if self.status == "active" and self.superseded_by is not None:
            raise ValueError("An 'active' DecisionMemory cannot have superseded_by set")
        if self.status == "superseded" and self.superseded_by is None:
            raise ValueError("A 'superseded' DecisionMemory must have superseded_by set")

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "DecisionMemory":
        """Construct from a database row (asyncpg Record or plain dict)."""
        return cls(
            id=_required_uuid(row["id"], field_name="id"),
            company_id=_required_uuid(row["company_id"], field_name="company_id"),
            reasoning_receipt_id=_required_uuid(row["reasoning_receipt_id"], field_name="reasoning_receipt_id"),
            decision_text=row["decision_text"],
            decided_by_user_id=_required_uuid(row["decided_by_user_id"], field_name="decided_by_user_id"),
            decided_at=row["decided_at"],
            created_at=row["created_at"],
            status=row.get("status", "active"),
            situation_id=_optional_uuid(row.get("situation_id")),
            rationale=row.get("rationale"),
            superseded_by=_optional_uuid(row.get("superseded_by")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        payload["id"] = str(self.id)
        payload["company_id"] = str(self.company_id)
        payload["reasoning_receipt_id"] = str(self.reasoning_receipt_id)
        payload["decided_by_user_id"] = str(self.decided_by_user_id)
        payload["decided_at"] = self.decided_at.isoformat()
        payload["created_at"] = self.created_at.isoformat()
        payload["situation_id"] = str(self.situation_id) if self.situation_id else None
        payload["superseded_by"] = str(self.superseded_by) if self.superseded_by else None
        return payload
