"""Operational situations synthesized by local NAWA OIP rules."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class OperationalSituation:
    """A local situation summary produced from related operational signals."""

    situation_type: str
    severity: str
    title: str
    summary: str
    evidence: list[dict[str, Any]]
    recommended_next_checks: list[str]
    start_date: date | None
    end_date: date | None
    entity_type: str | None = None
    entity_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        if self.start_date is not None:
            payload["start_date"] = self.start_date.isoformat()
        if self.end_date is not None:
            payload["end_date"] = self.end_date.isoformat()
        return payload
