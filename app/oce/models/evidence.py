"""Evidence objects collected by the Operational Context Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

EvidenceStatus = Literal["available", "missing"]


@dataclass(frozen=True)
class Evidence:
    """One available or missing evidence item for operational reasoning context."""

    source: str
    type: str
    status: EvidenceStatus
    description: str
    date_range: tuple[date | None, date | None]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        start_date, end_date = self.date_range
        payload["date_range"] = {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        }
        return payload

