"""Synthesize local operational situations from poultry OIP signals."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.oip.models.derived_artifacts import OperationalSignal
from app.oip.models.operational_situation import OperationalSituation

RECOMMENDED_PRODUCTION_DROP_CHECKS = [
    "review feed consumption",
    "review water consumption",
    "review mortality trend",
    "review vet notes",
    "review temperature/ventilation conditions",
]


class PoultrySituationService:
    """Generate local situation summaries from related poultry signals."""

    def generate_situations(self, signals: list[OperationalSignal]) -> list[OperationalSituation]:
        """Generate all rule-based poultry situations from operational signals."""
        situations: list[OperationalSituation] = []
        situations.extend(self._production_drop_situations(signals))
        return situations

    def _production_drop_situations(
        self,
        signals: list[OperationalSignal],
    ) -> list[OperationalSituation]:
        situations: list[OperationalSituation] = []
        trend_signals = [
            signal
            for signal in signals
            if signal.signal_type == "production_declining_trend"
        ]
        below_standard_signals = [
            signal
            for signal in signals
            if signal.signal_type == "production_below_standard"
        ]

        for trend_signal in trend_signals:
            start_date = trend_signal.start_date or trend_signal.date
            end_date = trend_signal.end_date or trend_signal.date
            related_below_standard = self._signals_in_date_range(
                below_standard_signals,
                start_date,
                end_date,
            )
            if len(related_below_standard) < 2:
                continue

            related_signals = [trend_signal, *related_below_standard]
            situations.append(
                OperationalSituation(
                    situation_type="poultry_production_drop",
                    severity="warning",
                    title="Production decline detected in poultry hall",
                    summary=self._production_drop_summary(
                        trend_signal,
                        related_below_standard,
                        start_date,
                        end_date,
                    ),
                    evidence=self._evidence(related_signals),
                    recommended_next_checks=RECOMMENDED_PRODUCTION_DROP_CHECKS,
                    start_date=start_date,
                    end_date=end_date,
                    entity_type=trend_signal.entity_type,
                    entity_reference=trend_signal.entity_reference,
                )
            )
        return situations

    def _signals_in_date_range(
        self,
        signals: list[OperationalSignal],
        start_date: date | None,
        end_date: date | None,
    ) -> list[OperationalSignal]:
        if start_date is None or end_date is None:
            return [signal for signal in signals if signal.date is not None]
        return [
            signal
            for signal in signals
            if signal.date is not None and start_date <= signal.date <= end_date
        ]

    def _production_drop_summary(
        self,
        trend_signal: OperationalSignal,
        below_standard_signals: list[OperationalSignal],
        start_date: date | None,
        end_date: date | None,
    ) -> str:
        start = start_date.isoformat() if start_date else "unknown start date"
        end = end_date.isoformat() if end_date else "unknown end date"
        return (
            f"Production declined from {start} to {end}. "
            f"{len(below_standard_signals)} daily production readings in that range "
            f"were below the standard rate. Trend evidence: {trend_signal.message}"
        )

    def _evidence(self, signals: list[OperationalSignal]) -> list[dict[str, Any]]:
        # Bounded provenance per evidence item (Codex Round 1 Finding 4): the
        # source of an evidence-backed claim must stay recoverable downstream
        # without duplicating whole workbooks/raw payloads into the
        # situation itself.
        evidence: list[dict[str, Any]] = []
        for signal in signals:
            evidence.append(
                {
                    "signal_type": signal.signal_type,
                    "date": signal.date.isoformat() if signal.date else None,
                    "start_date": signal.start_date.isoformat() if signal.start_date else None,
                    "end_date": signal.end_date.isoformat() if signal.end_date else None,
                    "message": signal.message,
                    "source_file": signal.source_file,
                    "sheet_name": signal.sheet_name,
                    "source_row_number": signal.source_row_number,
                    "report_shape": signal.report_shape,
                    "entity_type": signal.entity_type,
                    "entity_reference": signal.entity_reference,
                    "source_label": signal.source_label,
                    "raw_source_value": signal.raw_source_value,
                    "epistemic_origin": signal.epistemic_origin,
                }
            )
        return evidence
