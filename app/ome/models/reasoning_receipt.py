"""ReasoningReceipt: immutable, server-created proof of what evidence one
specific NAWA response used.

M8 Slice 1 scope: this is a persistence/domain model only, matching
migrations/014_organizational_memory.sql's ome_reasoning_receipts table.
No repository, service, or write path exists yet - creation, evidence
resolution, and response-snapshot construction are later-slice work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


def _required_uuid(value: Any, *, field_name: str) -> UUID:
    """Parse a REQUIRED identifier field. Raises ValueError if None or not
    a valid UUID/UUID-string."""
    if value is None:
        raise ValueError(f"{field_name} is required and cannot be None")
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


@dataclass(frozen=True)
class ReasoningReceipt:
    """One immutable row of ome_reasoning_receipts."""

    id: UUID
    company_id: UUID
    created_by_user_id: UUID
    created_at: datetime
    response_snapshot: dict[str, Any]
    evidence_refs: list[dict[str, Any]]
    session_id: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ReasoningReceipt":
        """Construct from a database row (asyncpg Record or plain dict)."""
        return cls(
            id=_required_uuid(row["id"], field_name="id"),
            company_id=_required_uuid(row["company_id"], field_name="company_id"),
            created_by_user_id=_required_uuid(row["created_by_user_id"], field_name="created_by_user_id"),
            created_at=row["created_at"],
            response_snapshot=row["response_snapshot"],
            evidence_refs=row["evidence_refs"],
            session_id=row.get("session_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        payload["id"] = str(self.id)
        payload["company_id"] = str(self.company_id)
        payload["created_by_user_id"] = str(self.created_by_user_id)
        payload["created_at"] = self.created_at.isoformat()
        return payload
