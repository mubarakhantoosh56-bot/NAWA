"""Generate local executive briefs from OIP situations."""

from __future__ import annotations

from typing import Any

from app.oip.models.ceo_brief import CEOBrief
from app.oip.models.operational_situation import OperationalSituation


class CEOBriefService:
    """Convert operational situations into short CEO-facing briefs."""

    def generate_briefs(self, situations: list[OperationalSituation]) -> list[CEOBrief]:
        """Generate one executive brief for each operational situation."""
        return [self._brief_for_situation(situation) for situation in situations]

    def _brief_for_situation(self, situation: OperationalSituation) -> CEOBrief:
        return CEOBrief(
            headline=situation.title,
            severity=situation.severity,
            what_happened=situation.summary,
            why_it_matters=self._why_it_matters(situation),
            evidence_summary=self._evidence_summary(situation),
            recommended_next_actions=situation.recommended_next_checks,
            confidence="initial",
        )

    def _why_it_matters(self, situation: OperationalSituation) -> str:
        if situation.situation_type == "poultry_production_drop":
            return (
                "A sustained poultry production drop can affect output planning, "
                "daily yield expectations, and the operating assumptions behind feed, "
                "water, veterinary, and hall-condition decisions."
            )
        return "This situation may affect operational performance and should be reviewed."

    def _evidence_summary(self, situation: OperationalSituation) -> list[dict[str, Any]]:
        return [
            {
                "signal_type": item.get("signal_type"),
                "date": item.get("date"),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
            }
            for item in situation.evidence
        ]
