"""Derive NAWA OIP metrics, events, and signals from poultry records."""

from __future__ import annotations

from typing import Any

from app.oip.models.derived_artifacts import (
    OperationalEvent,
    OperationalMetric,
    OperationalSignal,
    PoultryDerivedArtifacts,
)
from app.oip.models.operational_record import EpistemicOrigin, PoultryOperationalRecord
from app.oip.translators.poultry_report_translator import resolve_source_label

# M4 Slice 1 (Truth Contract Hardening) epistemic-origin classification for
# this service's outputs. Rule (documented, not assumed - see class/method
# docstrings for the per-artifact justification):
#   - OperationalMetric: OBSERVED only when the metric carries BOTH a
#     non-null normalized value AND resolvable source-claim provenance
#     (source_label + raw_source_value both present - see
#     _metric_epistemic_origin, Codex Round 2: a non-null value alone is not
#     sufficient proof of a source claim). A metric_name with no
#     corresponding value/provenance on the record (missing column, empty
#     cell, unresolved field, or a malformed/manually-constructed record
#     with no source claim) is still emitted (existing M3/OCE
#     missing-evidence detection depends on the metric object existing),
#     but its epistemic_origin is None (unresolved), never "observed".
#   - OperationalEvent (poultry_daily_report): DERIVED (deterministic
#     reformatting of multiple observed fields, not one source cell).
#   - OperationalSignal (all four generated types): DERIVED (deterministic
#     threshold/comparison/presence rules, zero AI or interpretation - never
#     INFERRED, since this service performs no non-deterministic reasoning).
METRIC_ORIGIN: EpistemicOrigin = "observed"
EVENT_ORIGIN: EpistemicOrigin = "derived"
SIGNAL_ORIGIN: EpistemicOrigin = "derived"


def _metric_epistemic_origin(
    value: Any,
    source_label: str | None,
    raw_source_value: Any,
) -> EpistemicOrigin | None:
    """OBSERVED requires actual source-backed evidence, not merely a
    non-null normalized value (Codex Round 2 finding: a malformed or
    manually-constructed record could carry a non-null ``value`` with no
    resolvable ``source_label``/``raw_source_value`` at all - a non-null
    value alone is not sufficient proof of a source claim).

    All three must hold, using ``is not None`` semantics throughout - never
    truthiness, since legitimate source values can be ``0``/``0.0``/
    ``False``:
      1. the normalized value is not None;
      2. the canonical field has a resolvable original source label
         (``resolve_source_label`` found a matching header on this record);
      3. the corresponding raw source value is actually present.

    An empty source cell already coerces to ``value is None`` upstream in
    the translator (``_coerce_value`` returns None for ``(None, "")``), so
    it is already excluded by condition 1 and never reaches this function
    with a non-null value - existing M3 empty-cell semantics are preserved
    unchanged.

    If any condition fails, the metric stays unresolved (``None``) - never
    silently defaulted to OBSERVED because the value merely "looks valid".
    """
    if value is None:
        return None
    if source_label is None:
        return None
    if raw_source_value is None:
        return None
    return METRIC_ORIGIN


METRIC_FIELDS = (
    "bird_balance",
    "daily_mortality",
    "weekly_mortality_rate",
    "daily_tray_production",
    "box_production",
    "daily_production_rate",
    "standard_production_rate",
    "broken_eggs",
    "dirty_eggs",
    "water_consumption",
    "feed_received",
    "feed_consumed",
    "feed_per_bird_average",
)
REQUIRED_SIGNAL_FIELDS = (
    "date",
    "bird_balance",
    "daily_mortality",
    "daily_production_rate",
    "standard_production_rate",
)
HIGH_DAILY_MORTALITY_THRESHOLD = 20


class PoultryDerivationService:
    """Generate deterministic OIP artifacts from normalized poultry records."""

    def derive(self, records: list[PoultryOperationalRecord]) -> PoultryDerivedArtifacts:
        """Generate metrics, events, and rule-based signals for poultry records."""
        return PoultryDerivedArtifacts(
            metrics=self.generate_metrics(records),
            events=self.generate_events(records),
            signals=self.generate_signals(records),
            situations=[],
            ceo_briefs=[],
        )

    def generate_metrics(self, records: list[PoultryOperationalRecord]) -> list[OperationalMetric]:
        """Generate one metric artifact for each configured metric field.

        A metric is still emitted for every METRIC_FIELDS entry even when
        the record has no value for it - existing missing-evidence detection
        (e.g. PoultryContextCollector's water/feed-consumption evidence
        checks, which filter on ``metric.value is not None``) depends on the
        metric object existing so absence can be represented and detected.
        What changes is ``epistemic_origin``: only a metric with an actual
        source-backed value is OBSERVED (Codex Round 1 Finding 1).
        """
        metrics: list[OperationalMetric] = []
        for record in records:
            for metric_name in METRIC_FIELDS:
                value = getattr(record, metric_name)
                source_label, raw_source_value = resolve_source_label(
                    record.raw_values, metric_name
                )
                metrics.append(
                    OperationalMetric(
                        metric_name=metric_name,
                        value=value,
                        date=record.date,
                        source_file=record.source_file,
                        source_row_number=record.row_number,
                        entity_type=record.entity_type,
                        entity_reference=record.entity_reference,
                        sheet_name=record.sheet_name,
                        report_shape=record.report_shape,
                        source_label=source_label,
                        raw_source_value=raw_source_value,
                        epistemic_origin=_metric_epistemic_origin(
                            value, source_label, raw_source_value
                        ),
                        source_file_id=record.source_file_id,
                        source_filename=record.source_filename,
                        source_company_id=record.source_company_id,
                        source_department_id=record.source_department_id,
                    )
                )
        return metrics

    def generate_events(self, records: list[PoultryOperationalRecord]) -> list[OperationalEvent]:
        """Generate one daily report event for each normalized poultry record."""
        return [
            OperationalEvent(
                event_type="poultry_daily_report",
                entity_type=record.entity_type,
                entity_reference=record.entity_reference,
                source_file=record.source_file,
                date=record.date,
                summary=self._summarize_record(record),
                source_row_number=record.row_number,
                sheet_name=record.sheet_name,
                report_shape=record.report_shape,
                epistemic_origin=EVENT_ORIGIN,
                source_file_id=record.source_file_id,
                source_filename=record.source_filename,
                source_company_id=record.source_company_id,
                source_department_id=record.source_department_id,
            )
            for record in records
        ]

    def generate_signals(self, records: list[PoultryOperationalRecord]) -> list[OperationalSignal]:
        """Generate deterministic operational signals from poultry records."""
        signals: list[OperationalSignal] = []
        for record in records:
            signals.extend(self._production_signals(record))
            signals.extend(self._mortality_signals(record))
            signals.extend(self._data_quality_signals(record))
        signals.extend(self._production_trend_signals(records))
        return signals

    def _production_signals(self, record: PoultryOperationalRecord) -> list[OperationalSignal]:
        daily_rate = record.daily_production_rate
        standard_rate = record.standard_production_rate
        if daily_rate is None or standard_rate is None or daily_rate >= standard_rate:
            return []
        gap = standard_rate - daily_rate
        source_label, raw_source_value = resolve_source_label(
            record.raw_values, "daily_production_rate"
        )
        return [
            OperationalSignal(
                signal_type="production_below_standard",
                severity="watch",
                message=(
                    f"Daily production rate {daily_rate:.2f}% is below "
                    f"standard {standard_rate:.2f}% by {gap:.2f} points."
                ),
                date=record.date,
                source_file=record.source_file,
                source_row_number=record.row_number,
                entity_type=record.entity_type,
                entity_reference=record.entity_reference,
                sheet_name=record.sheet_name,
                report_shape=record.report_shape,
                source_label=source_label,
                raw_source_value=raw_source_value,
                epistemic_origin=SIGNAL_ORIGIN,
                source_file_id=record.source_file_id,
                source_filename=record.source_filename,
                source_company_id=record.source_company_id,
                source_department_id=record.source_department_id,
            )
        ]

    def _mortality_signals(self, record: PoultryOperationalRecord) -> list[OperationalSignal]:
        daily_mortality = record.daily_mortality
        if daily_mortality is None or daily_mortality <= HIGH_DAILY_MORTALITY_THRESHOLD:
            return []
        source_label, raw_source_value = resolve_source_label(
            record.raw_values, "daily_mortality"
        )
        return [
            OperationalSignal(
                signal_type="high_daily_mortality",
                severity="warning",
                message=(
                    f"Daily mortality {daily_mortality} is above the provisional "
                    f"threshold of {HIGH_DAILY_MORTALITY_THRESHOLD}."
                ),
                date=record.date,
                source_file=record.source_file,
                source_row_number=record.row_number,
                entity_type=record.entity_type,
                entity_reference=record.entity_reference,
                sheet_name=record.sheet_name,
                report_shape=record.report_shape,
                source_label=source_label,
                raw_source_value=raw_source_value,
                epistemic_origin=SIGNAL_ORIGIN,
                source_file_id=record.source_file_id,
                source_filename=record.source_filename,
                source_company_id=record.source_company_id,
                source_department_id=record.source_department_id,
            )
        ]

    def _data_quality_signals(self, record: PoultryOperationalRecord) -> list[OperationalSignal]:
        missing_fields = [
            field_name
            for field_name in REQUIRED_SIGNAL_FIELDS
            if getattr(record, field_name) is None
        ]
        if not missing_fields:
            return []
        return [
            OperationalSignal(
                signal_type="data_quality_warning",
                severity="warning",
                message=f"Required values are missing: {', '.join(missing_fields)}.",
                date=record.date,
                source_file=record.source_file,
                source_row_number=record.row_number,
                entity_type=record.entity_type,
                entity_reference=record.entity_reference,
                sheet_name=record.sheet_name,
                report_shape=record.report_shape,
                epistemic_origin=SIGNAL_ORIGIN,
                source_file_id=record.source_file_id,
                source_filename=record.source_filename,
                source_company_id=record.source_company_id,
                source_department_id=record.source_department_id,
            )
        ]

    def _production_trend_signals(
        self,
        records: list[PoultryOperationalRecord],
    ) -> list[OperationalSignal]:
        """Generate warning signals for three-record production declines."""
        ordered_records = sorted(
            records,
            key=lambda record: (
                record.date is None,
                record.date,
                record.row_number,
            ),
        )
        signals: list[OperationalSignal] = []
        for index in range(len(ordered_records) - 2):
            window = ordered_records[index : index + 3]
            rates = [record.daily_production_rate for record in window]
            if any(rate is None for rate in rates):
                continue

            first_rate, second_rate, third_rate = rates
            if not (first_rate > second_rate > third_rate):
                continue

            start_record = window[0]
            end_record = window[-1]
            drop = first_rate - third_rate
            start_date = start_record.date.isoformat() if start_record.date else "unknown"
            end_date = end_record.date.isoformat() if end_record.date else "unknown"
            source_label, raw_source_value = resolve_source_label(
                end_record.raw_values, "daily_production_rate"
            )
            signals.append(
                OperationalSignal(
                    signal_type="production_declining_trend",
                    severity="warning",
                    message=(
                        f"Daily production rate declined across 3 consecutive records "
                        f"from {start_date} to {end_date}, dropping {drop:.2f} "
                        f"percentage points."
                    ),
                    date=end_record.date,
                    source_file=end_record.source_file,
                    source_row_number=end_record.row_number,
                    entity_type=end_record.entity_type,
                    entity_reference=end_record.entity_reference,
                    sheet_name=end_record.sheet_name,
                    report_shape=end_record.report_shape,
                    source_label=source_label,
                    raw_source_value=raw_source_value,
                    epistemic_origin=SIGNAL_ORIGIN,
                    start_date=start_record.date,
                    end_date=end_record.date,
                    source_file_id=end_record.source_file_id,
                    source_filename=end_record.source_filename,
                    source_company_id=end_record.source_company_id,
                    source_department_id=end_record.source_department_id,
                )
            )
        return signals

    def _summarize_record(self, record: PoultryOperationalRecord) -> str:
        values: dict[str, Any] = {
            "date": record.date.isoformat() if record.date else None,
            "day": record.day_name,
            "bird_balance": record.bird_balance,
            "daily_mortality": record.daily_mortality,
            "daily_tray_production": record.daily_tray_production,
            "daily_production_rate": record.daily_production_rate,
            "standard_production_rate": record.standard_production_rate,
            "water_consumption": record.water_consumption,
            "feed_received": record.feed_received,
            "feed_consumed": record.feed_consumed,
        }
        parts = [f"{key}={value}" for key, value in values.items() if value is not None]
        return "Poultry daily report: " + ", ".join(parts)
