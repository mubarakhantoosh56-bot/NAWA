"""Typed operational records produced by NAWA OIP translators."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PoultryOperationalRecord:
    """Normalized daily Dairtna poultry technical report row.

    ``report_shape`` and ``entity_type``/``entity_reference`` are provenance
    fields required for the M4 Truth Layer (Founder Business Semantics Ruling
    - M3). ``entity_type`` is one of ``production_hall``, ``rearing_hall``,
    ``company_aggregate``, or ``None`` when hall/entity identity is not
    structurally supported by the source - it is never guessed.
    """

    date: date | None
    day_name: str | None
    age_week: int | None
    age_day: int | None
    bird_balance: int | None
    daily_mortality: int | None
    weekly_mortality: int | None
    weekly_mortality_rate: float | None
    daily_tray_production: int | None
    box_production: int | None
    daily_production_rate: float | None
    standard_production_rate: float | None
    broken_eggs: int | None
    dirty_eggs: int | None
    water_consumption: int | None
    feed_received: float | None
    feed_consumed: float | None
    feed_per_bird_average: float | None
    unknown_marker_field: Any | None
    source_file: str
    sheet_name: str
    row_number: int
    report_shape: str
    entity_type: str | None
    entity_reference: str | None
    raw_values: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        if self.date is not None:
            payload["date"] = self.date.isoformat()
        payload["source_file"] = Path(self.source_file).as_posix()
        return payload
