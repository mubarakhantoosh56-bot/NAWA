"""Typed operational records produced by NAWA OIP translators."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

# M4 Slice 1 (Truth Contract Hardening) - Founder Core Trust Principle:
# information-origin classification. Bounded on purpose (never free text).
# OBSERVED != DERIVED != INFERRED != RECOMMENDED - no downstream code may
# silently promote one into another. Shared by app.oip and app.oce so both
# layers speak the same vocabulary without a new parallel model/package.
EpistemicOrigin = Literal["observed", "derived", "inferred", "recommended"]

# The vocabulary is a runtime contract, not only a static typing hint
# (Codex Round 1 Finding 2) - a Literal alone is not enforced by Python at
# construction time, so every model carrying epistemic_origin validates
# against this set via validate_epistemic_origin() in __post_init__.
VALID_EPISTEMIC_ORIGINS = frozenset({"observed", "derived", "inferred", "recommended"})

# Feed Mill's existing source-time vocabulary (Round 2 hardening), reused
# unchanged here rather than duplicated, per "do not duplicate the same
# information into multiple competing structures."
SOURCE_TIME_AUTHORITATIVE = "authoritative"
SOURCE_TIME_UNRESOLVED = "unresolved"


def validate_epistemic_origin(value: EpistemicOrigin | None, *, field_name: str = "epistemic_origin") -> None:
    """Raise ValueError unless ``value`` is None or an exact allowed
    EpistemicOrigin literal (Codex Round 1 Finding 2).

    None is accepted everywhere this validator is used: every model field
    it guards is typed ``EpistemicOrigin | None`` with a default of None
    (legacy/unresolved-origin evidence, or a metric with no source-backed
    value - see PoultryDerivationService._metric_epistemic_origin). Beyond
    that, only the four exact lower-case strings are accepted - no case
    normalization, no aliases, no silent default to "observed".
    """
    if value is None:
        return
    if value not in VALID_EPISTEMIC_ORIGINS:
        raise ValueError(
            f"{field_name} must be one of {sorted(VALID_EPISTEMIC_ORIGINS)} or None, "
            f"got {value!r}"
        )


@dataclass(frozen=True)
class PoultryOperationalRecord:
    """Normalized daily Dairtna poultry technical report row.

    ``report_shape`` and ``entity_type``/``entity_reference`` are provenance
    fields required for the M4 Truth Layer (Founder Business Semantics Ruling
    - M3). ``entity_type`` is one of ``production_hall``, ``rearing_hall``,
    ``company_aggregate``, or ``None`` when hall/entity identity is not
    structurally supported by the source - it is never guessed.

    ``epistemic_origin`` is always ``"observed"`` for this record type: every
    field is a direct, unmodified parse of a validated source workbook cell
    (Founder Core Trust Principle, M4 Slice 1). No computation happens here.
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
    epistemic_origin: EpistemicOrigin | None = None

    def __post_init__(self) -> None:
        validate_epistemic_origin(self.epistemic_origin)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        payload = asdict(self)
        if self.date is not None:
            payload["date"] = self.date.isoformat()
        payload["source_file"] = Path(self.source_file).as_posix()
        return payload
