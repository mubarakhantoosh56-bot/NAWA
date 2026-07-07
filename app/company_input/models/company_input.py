"""Canonical Company Input model.

CompanyInput is the intake contract for information entering NAWA. It contains
metadata only and deliberately excludes reasoning, metrics, summaries, and
engine outputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CompanyInput:
    """Metadata envelope for one piece of information entering NAWA."""

    company_id: UUID
    source: str
    source_type: str
    media_type: str
    id: UUID = field(default_factory=uuid4)
    department_id: UUID | None = None
    user_id: UUID | None = None
    mime_type: str | None = None
    original_filename: str | None = None
    language: str | None = None
    confidence: str = "unknown"
    raw_storage_path: str | None = None
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation of the intake metadata."""
        payload = asdict(self)
        for key in ("id", "company_id", "department_id", "user_id"):
            if payload[key] is not None:
                payload[key] = str(payload[key])
        payload["received_at"] = self.received_at.isoformat()
        return payload
