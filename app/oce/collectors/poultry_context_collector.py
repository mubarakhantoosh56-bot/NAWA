"""Poultry context collection for the Operational Context Engine."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from app.oce.collectors.feed_mill_context_collector import FeedMillContextCollector
from app.oce.models.evidence import Evidence
from app.oce.models.operational_context import OperationalContext
from app.oip.models.derived_artifacts import OperationalEvent, OperationalMetric, OperationalSignal
from app.oip.models.operational_record import PoultryOperationalRecord
from app.oip.models.operational_situation import OperationalSituation

COMPANY_NAME = "Jannat Al-Firdaws"
DEPARTMENT_NAME = "Dairtna Poultry"
UNRESOLVED_ENTITY = "unresolved"
DECISION_RULES_PATH = Path("knowledge/dairtna/DAIRTNA_DECISION_RULES.md")
OPERATIONAL_SEMANTICS_PATH = Path("knowledge/dairtna/DAIRTNA_OPERATIONAL_SEMANTICS.md")
REQUIRED_CONTEXT_ITEMS = (
    "Feed consumption",
    "Water consumption",
    "Mortality trend",
    "Vet reports",
    "Temperature / ventilation",
    "Previous production history",
    "Company decision rules",
    "Operational semantics",
)


class PoultryContextCollector:
    """Collect relevant local context for poultry OIP situations."""

    def __init__(self, feed_mill_collector: FeedMillContextCollector | None = None) -> None:
        self.feed_mill_collector = feed_mill_collector or FeedMillContextCollector()

    def collect(
        self,
        situation: OperationalSituation,
        metrics: list[OperationalMetric],
        events: list[OperationalEvent],
        signals: list[OperationalSignal],
        records: list[PoultryOperationalRecord],
    ) -> OperationalContext:
        """Build an operational context packet for a poultry situation."""
        start_date, end_date = situation.start_date, situation.end_date
        related_metrics = self._filter_metrics(metrics, start_date, end_date)
        related_events = self._filter_events(events, start_date, end_date)
        related_signals = self._filter_signals(signals, start_date, end_date)
        available_evidence, missing_evidence = self._collect_evidence(
            situation,
            related_metrics,
            related_events,
            related_signals,
            records,
            start_date,
            end_date,
        )
        recommended_next_data = [
            evidence.description for evidence in missing_evidence
        ]

        return OperationalContext(
            context_type=situation.situation_type,
            situation=situation.to_dict(),
            company=COMPANY_NAME,
            department=DEPARTMENT_NAME,
            related_entities=self._related_entities(situation),
            time_window=(start_date, end_date),
            related_metrics=[metric.to_dict() for metric in related_metrics],
            related_events=[event.to_dict() for event in related_events],
            related_signals=[signal.to_dict() for signal in related_signals],
            available_evidence=available_evidence,
            missing_evidence=missing_evidence,
            recommended_next_data=recommended_next_data,
            context_ready_for_reasoning=self._is_ready_for_reasoning(
                available_evidence,
                missing_evidence,
            ),
        )

    def _collect_evidence(
        self,
        situation: OperationalSituation,
        metrics: list[OperationalMetric],
        events: list[OperationalEvent],
        signals: list[OperationalSignal],
        records: list[PoultryOperationalRecord],
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[list[Evidence], list[Evidence]]:
        available: list[Evidence] = [
            Evidence(
                source="oip.situation",
                type="situation",
                status="available",
                description=f"Generated situation: {situation.situation_type}",
                date_range=(start_date, end_date),
            )
        ]
        missing: list[Evidence] = []

        if any(signal.signal_type == "production_declining_trend" for signal in signals):
            available.append(
                Evidence(
                    source="oip.signals",
                    type="production_trend",
                    status="available",
                    description="Production declining trend signal is available.",
                    date_range=(start_date, end_date),
                )
            )

        if any(metric.metric_name == "daily_mortality" for metric in metrics):
            available.append(
                Evidence(
                    source="oip.metrics",
                    type="mortality_trend",
                    status="available",
                    description="Daily mortality metrics are available for the situation window.",
                    date_range=(start_date, end_date),
                )
            )
        else:
            missing.append(self._missing("Mortality trend", start_date, end_date))

        if any(event.event_type == "poultry_daily_report" for event in events):
            available.append(
                Evidence(
                    source="oip.events",
                    type="daily_report",
                    status="available",
                    description="Daily poultry report events are available for the situation window.",
                    date_range=(start_date, end_date),
                )
            )

        water_evidence = self._water_consumption_evidence(metrics, start_date, end_date)
        if water_evidence is not None:
            available.append(water_evidence)

        # "Feed consumption" evidence for poultry halls/fields is answered by
        # the field_feed_consumption metric (feed_consumed), never by the
        # feed mill's raw-material data. The two stages are kept distinct per
        # the Founder Business Semantics Ruling - M3.
        feed_consumption_evidence = self._feed_consumption_evidence(
            situation, metrics, start_date, end_date
        )
        if feed_consumption_evidence is not None:
            available.append(feed_consumption_evidence)

        available.extend(self._knowledge_evidence(start_date, end_date))
        feed_mill_evidence = self.feed_mill_collector.collect_evidence(
            date_range=(start_date, end_date),
        )
        if feed_mill_evidence is not None:
            available.append(feed_mill_evidence)
        raw_material_inventory_evidence = (
            self.feed_mill_collector.collect_raw_material_inventory_evidence(
                date_range=(start_date, end_date),
            )
        )
        if raw_material_inventory_evidence is not None:
            available.append(raw_material_inventory_evidence)
        production_history_evidence = self._production_history_evidence(records)
        if production_history_evidence is not None:
            available.append(production_history_evidence)
        missing.extend(
            self._missing_operational_reports(
                start_date,
                end_date,
                include_feed=feed_consumption_evidence is None,
                include_water=water_evidence is None,
                include_previous_history=production_history_evidence is None,
            )
        )

        return available, missing

    def _knowledge_evidence(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[Evidence]:
        evidence: list[Evidence] = []
        if DECISION_RULES_PATH.exists():
            evidence.append(
                Evidence(
                    source=DECISION_RULES_PATH.as_posix(),
                    type="company_decision_rules",
                    status="available",
                    description="Company decision rules document is available for context.",
                    date_range=(start_date, end_date),
                )
            )
        if OPERATIONAL_SEMANTICS_PATH.exists():
            evidence.append(
                Evidence(
                    source=OPERATIONAL_SEMANTICS_PATH.as_posix(),
                    type="operational_semantics",
                    status="available",
                    description="Dairtna operational semantics document is available for context.",
                    date_range=(start_date, end_date),
                )
            )
        return evidence

    def _missing_operational_reports(
        self,
        start_date: date | None,
        end_date: date | None,
        include_feed: bool = True,
        include_water: bool = True,
        include_previous_history: bool = True,
    ) -> list[Evidence]:
        missing = [
            self._missing("Vet reports", start_date, end_date),
            self._missing("Temperature / ventilation", start_date, end_date),
        ]
        if include_feed:
            missing.insert(0, self._missing("Feed consumption", start_date, end_date))
        if include_water:
            insert_at = 1 if include_feed else 0
            missing.insert(insert_at, self._missing("Water consumption", start_date, end_date))
        if include_previous_history:
            missing.append(self._missing("Previous production history", start_date, end_date))
        return missing

    def _water_consumption_evidence(
        self,
        metrics: list[OperationalMetric],
        start_date: date | None,
        end_date: date | None,
    ) -> Evidence | None:
        water_metrics = [
            metric
            for metric in metrics
            if metric.metric_name == "water_consumption" and metric.value is not None
        ]
        if not water_metrics:
            return None
        return Evidence(
            source="oip.metrics",
            type="water_consumption",
            status="available",
            description="Water consumption metrics are available from parsed daily poultry records.",
            date_range=(start_date, end_date),
        )

    def _feed_consumption_evidence(
        self,
        situation: OperationalSituation,
        metrics: list[OperationalMetric],
        start_date: date | None,
        end_date: date | None,
    ) -> Evidence | None:
        """Return feed_consumption evidence only when it is scoped to the
        situation's own entity (Codex Round 1 Finding 6).

        Company-wide aggregate feed data must never satisfy a hall-specific
        evidence requirement, and one hall's feed data must never satisfy
        another hall's requirement. A situation whose own entity is
        unresolved cannot claim entity-scoped feed evidence either - that
        would be guessing an allocation that the source does not support.
        """
        if situation.entity_type is None:
            return None
        feed_metrics = [
            metric
            for metric in metrics
            if metric.metric_name == "feed_consumed"
            and metric.value is not None
            and metric.entity_type == situation.entity_type
            and metric.entity_reference == situation.entity_reference
        ]
        if not feed_metrics:
            return None
        return Evidence(
            source="oip.metrics",
            type="feed_consumption",
            status="available",
            description=(
                "Feed consumption metrics (field_feed_consumption) are available "
                "for this situation's own entity scope "
                f"({situation.entity_type}: {situation.entity_reference})."
            ),
            date_range=(start_date, end_date),
        )

    def _related_entities(self, situation: OperationalSituation) -> list[str]:
        if situation.entity_type is None:
            return [UNRESOLVED_ENTITY]
        if situation.entity_reference is None:
            return [situation.entity_type]
        return [f"{situation.entity_type}:{situation.entity_reference}"]

    def _production_history_evidence(
        self,
        records: list[PoultryOperationalRecord],
    ) -> Evidence | None:
        if len(records) <= 3:
            return None
        record_dates = sorted(record.date for record in records if record.date is not None)
        if not record_dates:
            return None
        return Evidence(
            source="oip.parsed_poultry_records",
            type="previous_production_history",
            status="available",
            description="Production history is available from parsed daily poultry records.",
            date_range=(record_dates[0], record_dates[-1]),
        )

    def _missing(
        self,
        label: str,
        start_date: date | None,
        end_date: date | None,
    ) -> Evidence:
        evidence_type = (
            label.lower()
            .replace(" / ", "_")
            .replace(" ", "_")
        )
        return Evidence(
            source="local_oce_request",
            type=evidence_type,
            status="missing",
            description=f"Request context for {label}.",
            date_range=(start_date, end_date),
        )

    def _filter_metrics(
        self,
        metrics: list[OperationalMetric],
        start_date: date | None,
        end_date: date | None,
    ) -> list[OperationalMetric]:
        return [
            metric
            for metric in metrics
            if self._within_window(metric.date, start_date, end_date)
        ]

    def _filter_events(
        self,
        events: list[OperationalEvent],
        start_date: date | None,
        end_date: date | None,
    ) -> list[OperationalEvent]:
        return [
            event
            for event in events
            if self._within_window(event.date, start_date, end_date)
        ]

    def _filter_signals(
        self,
        signals: list[OperationalSignal],
        start_date: date | None,
        end_date: date | None,
    ) -> list[OperationalSignal]:
        return [
            signal
            for signal in signals
            if self._within_window(signal.date, start_date, end_date)
            or self._overlaps_window(signal.start_date, signal.end_date, start_date, end_date)
        ]

    def _within_window(
        self,
        value: date | None,
        start_date: date | None,
        end_date: date | None,
    ) -> bool:
        if value is None:
            return False
        if start_date is not None and value < start_date:
            return False
        if end_date is not None and value > end_date:
            return False
        return True

    def _overlaps_window(
        self,
        value_start: date | None,
        value_end: date | None,
        window_start: date | None,
        window_end: date | None,
    ) -> bool:
        if value_start is None or value_end is None:
            return False
        if window_start is not None and value_end < window_start:
            return False
        if window_end is not None and value_start > window_end:
            return False
        return True

    def _is_ready_for_reasoning(
        self,
        available_evidence: list[Evidence],
        missing_evidence: list[Evidence],
    ) -> bool:
        available_types = {evidence.type for evidence in available_evidence}
        missing_types = {evidence.type for evidence in missing_evidence}
        required_available = {
            "production_trend",
            "mortality_trend",
            "company_decision_rules",
            "operational_semantics",
        }
        blocking_missing = {
            "feed_consumption",
            "water_consumption",
            "vet_reports",
            "temperature_ventilation",
        }
        return required_available.issubset(available_types) and not (
            blocking_missing & missing_types
        )
