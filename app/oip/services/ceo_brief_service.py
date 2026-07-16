"""Generate local executive briefs from OIP situations."""

from __future__ import annotations

from typing import Any

from app.oip.models.ceo_brief import CEOBrief
from app.oip.models.operational_situation import OperationalSituation

PENDING_EXECUTIVE_LANGUAGE = "pending_executive_language"
TREND_SIGNAL_TYPES = frozenset({"production_declining_trend"})

# ENG-EX1-003 accepted vocabulary (category-level traceability; row/file
# lineage is unavailable at this layer and is deferred to Backlog).
SOURCE_TYPE_OIE_SIGNAL = "oie_signal"
SOURCE_TYPE_OCE_CONTEXT = "oce_context"
SOURCE_TYPE_SYNTHESIS = "synthesis"

TRACE_STATUS_TRACED = "traced"
TRACE_STATUS_COARSE = "coarse"
TRACE_STATUS_PENDING = "pending"


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
            statement_trace=self._statement_trace(situation),
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

    def _statement_trace(self, situation: OperationalSituation) -> list[dict[str, Any]]:
        """ENG-EX1-003: category-level source reference per statement.

        "coarse" marks statements whose content is a fixed template invariant
        to the specific evidence present (situation_type-keyed only, e.g.
        why_it_matters and the rule-based action checklist); "traced" marks
        statements whose content is directly derived from the specific
        evidence instance(s) in this brief. Row/file-level lineage is not
        available at this layer and is never fabricated here.
        """
        situation_ref = {"situation_type": situation.situation_type}
        signal_types = [item.get("signal_type") for item in situation.evidence]

        trace: list[dict[str, Any]] = [
            {
                "field": "headline",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": situation_ref,
                "trace_status": TRACE_STATUS_COARSE,
            },
            {
                "field": "what_happened",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": {**situation_ref, "evidence_signal_types": signal_types},
                "trace_status": TRACE_STATUS_TRACED,
            },
            {
                "field": "why_it_matters",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": situation_ref,
                "trace_status": TRACE_STATUS_COARSE,
            },
            {
                "field": "business_impact.operational",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": situation_ref,
                "trace_status": TRACE_STATUS_COARSE,
            },
            {
                "field": "business_impact.financial",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": situation_ref,
                "trace_status": TRACE_STATUS_COARSE,
            },
            {
                "field": "executive_attention",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": {**situation_ref, "severity": situation.severity},
                "trace_status": TRACE_STATUS_COARSE,
            },
            {
                "field": "executive_priority",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_assessment",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "business_impact.strategic",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
        ]

        for index, item in enumerate(situation.evidence):
            item_ref = {
                "signal_type": item.get("signal_type"),
                "date": item.get("date"),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
            }
            trace.append(
                {
                    "field": f"evidence_summary[{index}]",
                    "source_type": SOURCE_TYPE_OIE_SIGNAL,
                    "source_ref": item_ref,
                    "trace_status": TRACE_STATUS_TRACED,
                }
            )
            trace.append(
                {
                    "field": f"facts[{index}]",
                    "source_type": SOURCE_TYPE_OIE_SIGNAL,
                    "source_ref": item_ref,
                    "trace_status": TRACE_STATUS_TRACED,
                }
            )

        what_changed_index = 0
        for item in situation.evidence:
            if item.get("signal_type") not in TREND_SIGNAL_TYPES:
                continue
            trace.append(
                {
                    "field": f"what_changed[{what_changed_index}]",
                    "source_type": SOURCE_TYPE_OIE_SIGNAL,
                    "source_ref": {
                        "signal_type": item.get("signal_type"),
                        "date": item.get("date"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                    },
                    "trace_status": TRACE_STATUS_TRACED,
                }
            )
            what_changed_index += 1

        for index, _check in enumerate(situation.recommended_next_checks):
            trace.append(
                {
                    "field": f"recommended_next_actions[{index}]",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    "source_ref": situation_ref,
                    "trace_status": TRACE_STATUS_COARSE,
                }
            )
            trace.append(
                {
                    "field": f"executive_actions[{index}].action",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    "source_ref": situation_ref,
                    "trace_status": TRACE_STATUS_COARSE,
                }
            )
            trace.append(
                {
                    "field": f"executive_actions[{index}].priority_reason_outcome",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    "source_ref": {
                        "pending_fields": ["priority", "reason", "expected_outcome"],
                    },
                    "trace_status": TRACE_STATUS_PENDING,
                }
            )

        return trace
