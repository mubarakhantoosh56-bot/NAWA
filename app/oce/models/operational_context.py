"""Operational context prepared by the NAWA Operational Context Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from app.oce.models.evidence import Evidence


@dataclass(frozen=True)
class OperationalContext:
    """Context packet prepared for future reasoning without making decisions."""

    context_type: str
    situation: dict[str, Any]
    company: str
    department: str
    related_entities: list[str]
    time_window: tuple[date | None, date | None]
    related_metrics: list[dict[str, Any]]
    related_events: list[dict[str, Any]]
    related_signals: list[dict[str, Any]]
    available_evidence: list[Evidence]
    missing_evidence: list[Evidence]
    recommended_next_data: list[str]
    context_ready_for_reasoning: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        start_date, end_date = self.time_window
        payload["time_window"] = {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        }
        payload["available_evidence"] = [
            evidence.to_dict() for evidence in self.available_evidence
        ]
        payload["missing_evidence"] = [
            evidence.to_dict() for evidence in self.missing_evidence
        ]
        return payload
