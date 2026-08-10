"""Evidence objects collected by the Operational Context Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Literal

from app.oip.models.operational_record import EpistemicOrigin, validate_epistemic_origin

EvidenceStatus = Literal["available", "missing"]


@dataclass(frozen=True)
class Evidence:
    """One available or missing evidence item for operational reasoning context.

    M4 Slice 1 (Truth Contract Hardening) adds optional, backward-compatible
    provenance fields so evidence can answer, where the underlying source
    claim supports it: what is this claim, what is its epistemic origin,
    what exact source backs it, what entity it applies to, and what time the
    SOURCE establishes (as distinct from ``date_range``, which is the
    situation/reasoning window this evidence was fetched for - never the
    same thing as the source's own report/snapshot time).

    Every new field defaults to ``None``/empty and every existing
    construction site continues to work unchanged. Nothing here is
    fabricated: a legacy or multi-claim evidence path that cannot honestly
    supply one of these fields simply leaves it ``None`` rather than
    guessing (Founder instruction - absence must stay visible, never be
    manufactured into false completeness).
    """

    source: str
    type: str
    status: EvidenceStatus
    description: str
    date_range: tuple[date | None, date | None]

    # --- M4 Slice 1 additive provenance (all optional) ---------------------
    epistemic_origin: EpistemicOrigin | None = None
    canonical_field: str | None = None
    normalized_value: Any | None = None
    source_label: str | None = None
    raw_source_value: Any | None = None
    source_file: str | None = None
    sheet_name: str | None = None
    source_row_number: int | None = None
    report_shape: str | None = None
    entity_type: str | None = None
    entity_reference: str | None = None
    # The SOURCE's own authoritative report/snapshot date - distinct from
    # ``date_range`` above. ``source_time_status`` is one of "authoritative"
    # / "unresolved" / None (unknown or not applicable to this evidence).
    # When unresolved, ``source_time`` MUST stay None - it is never replaced
    # by ingestion time, current time, or the situation window.
    source_time: date | None = None
    source_time_status: str | None = None
    provenance_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_epistemic_origin(self.epistemic_origin)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        start_date, end_date = self.date_range
        payload["date_range"] = {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        }
        if self.source_time is not None:
            payload["source_time"] = self.source_time.isoformat()
        return payload

