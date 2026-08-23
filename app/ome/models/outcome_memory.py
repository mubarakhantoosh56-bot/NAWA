"""OutcomeMemory: one HUMAN-recorded historical outcome of one
DecisionMemory.

M8 Slice 1 scope: persistence/domain model only, matching
migrations/014_organizational_memory.sql's ome_outcome_memories table.
No repository, service, or write path exists yet.

Deliberately carries no evidence_refs field: outcome-level evidence
provenance beyond the human-attributed outcome itself is deferred until a
server-verifiable trust boundary is separately designed (M8 OME
Provenance Integrity Decision, Table 3). The original decision remains
traceable to its evidence through decision_memory_id -> reasoning_receipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

OUTCOME_STATUSES = frozenset({"active", "superseded"})
OUTCOME_RESULT_STATES = frozenset({"positive", "negative", "mixed", "unknown"})


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
class OutcomeMemory:
    """One row of ome_outcome_memories."""

    id: UUID
    company_id: UUID
    decision_memory_id: UUID
    outcome_summary: str
    result_state: str
    recorded_by_user_id: UUID
    observed_at: datetime
    created_at: datetime
    status: str = "active"
    superseded_by: UUID | None = None

    def __post_init__(self) -> None:
        if self.status not in OUTCOME_STATUSES:
            raise ValueError(f"Invalid OutcomeMemory status: {self.status!r}")
        if self.result_state not in OUTCOME_RESULT_STATES:
            raise ValueError(f"Invalid OutcomeMemory result_state: {self.result_state!r}")
        # Mirrors migrations/014_organizational_memory.sql's
        # chk_ome_outcome_memories_status_supersession_consistent.
        if self.status == "active" and self.superseded_by is not None:
            raise ValueError("An 'active' OutcomeMemory cannot have superseded_by set")
        if self.status == "superseded" and self.superseded_by is None:
            raise ValueError("A 'superseded' OutcomeMemory must have superseded_by set")

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OutcomeMemory":
        """Construct from a database row (asyncpg Record or plain dict)."""
        return cls(
            id=_required_uuid(row["id"], field_name="id"),
            company_id=_required_uuid(row["company_id"], field_name="company_id"),
            decision_memory_id=_required_uuid(row["decision_memory_id"], field_name="decision_memory_id"),
            outcome_summary=row["outcome_summary"],
            result_state=row["result_state"],
            recorded_by_user_id=_required_uuid(row["recorded_by_user_id"], field_name="recorded_by_user_id"),
            observed_at=row["observed_at"],
            created_at=row["created_at"],
            status=row.get("status", "active"),
            superseded_by=_optional_uuid(row.get("superseded_by")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        payload["id"] = str(self.id)
        payload["company_id"] = str(self.company_id)
        payload["decision_memory_id"] = str(self.decision_memory_id)
        payload["recorded_by_user_id"] = str(self.recorded_by_user_id)
        payload["observed_at"] = self.observed_at.isoformat()
        payload["created_at"] = self.created_at.isoformat()
        payload["superseded_by"] = str(self.superseded_by) if self.superseded_by else None
        return payload
