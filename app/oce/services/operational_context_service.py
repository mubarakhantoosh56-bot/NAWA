"""Operational Context Engine orchestration service."""

from __future__ import annotations

from app.oce.collectors.poultry_context_collector import PoultryContextCollector
from app.oce.models.operational_context import OperationalContext
from app.oip.models.derived_artifacts import OperationalEvent, OperationalMetric, OperationalSignal
from app.oip.models.operational_record import PoultryOperationalRecord
from app.oip.models.operational_situation import OperationalSituation


class OperationalContextService:
    """Build local operational context from OIP situations and artifacts."""

    def __init__(self, poultry_collector: PoultryContextCollector | None = None) -> None:
        self.poultry_collector = poultry_collector or PoultryContextCollector()

    def build_contexts(
        self,
        situations: list[OperationalSituation],
        metrics: list[OperationalMetric],
        events: list[OperationalEvent],
        signals: list[OperationalSignal],
        records: list[PoultryOperationalRecord],
    ) -> list[OperationalContext]:
        """Build operational contexts for supported local situations."""
        contexts: list[OperationalContext] = []
        for situation in situations:
            if situation.situation_type == "poultry_production_drop":
                contexts.append(
                    self.poultry_collector.collect(
                        situation=situation,
                        metrics=metrics,
                        events=events,
                        signals=signals,
                        records=records,
                    )
                )
        return contexts
