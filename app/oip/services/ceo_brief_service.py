"""Generate local executive briefs from OIP situations."""

from __future__ import annotations

from typing import Any

from app.oip.models.ceo_brief import CEOBrief
from app.oip.models.operational_situation import OperationalSituation

PENDING_EXECUTIVE_LANGUAGE = "pending_executive_language"
TREND_SIGNAL_TYPES = frozenset({"production_declining_trend"})


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
            executive_priority=self._executive_priority(situation),
            what_changed=self._what_changed(situation),
            facts=self._facts(situation),
            executive_assessment=self._executive_assessment(situation),
            business_impact=self._business_impact(situation),
            executive_actions=self._executive_actions(situation),
            executive_attention=self._executive_attention(situation),
        )

    def _executive_priority(self, situation: OperationalSituation) -> dict[str, Any]:
        return {
            "status": PENDING_EXECUTIVE_LANGUAGE,
            "known_facts": {"severity": situation.severity},
            "note": (
                "Executive Priority urgency framing pending Aboura's Executive "
                "Brief Design Principles (PDS-001 §5.1)."
            ),
        }

    def _what_changed(self, situation: OperationalSituation) -> list[dict[str, Any]]:
        return [
            self._evidence_item(item)
            for item in situation.evidence
            if item.get("signal_type") in TREND_SIGNAL_TYPES
        ]

    def _facts(self, situation: OperationalSituation) -> list[dict[str, Any]]:
        return [self._evidence_item(item) for item in situation.evidence]

    def _evidence_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "signal_type": item.get("signal_type"),
            "date": item.get("date"),
            "start_date": item.get("start_date"),
            "end_date": item.get("end_date"),
            "statement": item.get("message"),
        }

    def _executive_assessment(self, situation: OperationalSituation) -> dict[str, Any]:
        return {
            "status": PENDING_EXECUTIVE_LANGUAGE,
            "note": (
                "Executive Assessment (Executive Thinking) prioritization pending "
                "Aboura's design (PDS-001 §5.5)."
            ),
        }

    def _business_impact(self, situation: OperationalSituation) -> dict[str, Any]:
        return {
            "operational": self._why_it_matters(situation),
            "financial": "Unknown",
            "strategic": {
                "status": PENDING_EXECUTIVE_LANGUAGE,
                "note": (
                    "Strategic impact framing pending Aboura's Business Impact "
                    "Framework instantiation (PDS-001 §5.6)."
                ),
            },
        }

    def _executive_actions(self, situation: OperationalSituation) -> list[dict[str, Any]]:
        evidence_refs = [item.get("signal_type") for item in situation.evidence]
        return [
            {
                "action": check,
                "priority": PENDING_EXECUTIVE_LANGUAGE,
                "reason": PENDING_EXECUTIVE_LANGUAGE,
                "expected_outcome": PENDING_EXECUTIVE_LANGUAGE,
                "evidence_refs": evidence_refs,
            }
            for check in situation.recommended_next_checks
        ]

    def _executive_attention(self, situation: OperationalSituation) -> dict[str, Any]:
        if situation.severity == "warning":
            return {"immediate": [situation.title], "monitor": []}
        return {"immediate": [], "monitor": [situation.title]}

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
