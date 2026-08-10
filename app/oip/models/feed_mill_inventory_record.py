"""Typed feed mill raw-material inventory records produced by NAWA OIP."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.oip.models.operational_record import EpistemicOrigin, validate_epistemic_origin


@dataclass(frozen=True)
class FeedMillInventoryRecord:
    """One raw-material row from a feed mill inventory snapshot.

    This is a distinct concept from poultry hall/field feed_received and
    feed_consumed (Founder Business Semantics Ruling - M3: the feed mill and
    poultry halls represent different process stages and their feed/material
    concepts must never be merged).

    ``epistemic_origin`` is always ``"observed"``: the inventory balance is a
    direct parse of a source workbook cell (M4 Slice 1). This is independent
    of ``report_date_status`` - the *value* is observed even when the
    source's own snapshot *date* is unresolved; the two must never be
    conflated (Feed Mill Golden Case).
    """

    material_name: str
    raw_material_inventory: float | None
    source_reported_days_coverage: float | None
    report_date: date | None
    source_file: str
    sheet_name: str
    row_number: int
    entity_type: str
    entity_reference: str | None
    report_shape: str
    raw_values: dict[str, Any]
    report_date_status: str = "unresolved"
    provenance_warnings: tuple[str, ...] = ()
    epistemic_origin: EpistemicOrigin | None = None

    def __post_init__(self) -> None:
        validate_epistemic_origin(self.epistemic_origin)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        if self.report_date is not None:
            payload["report_date"] = self.report_date.isoformat()
        payload["source_file"] = Path(self.source_file).as_posix()
        return payload
