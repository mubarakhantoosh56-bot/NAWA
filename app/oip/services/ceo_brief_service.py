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

# Executive Language Completion (Founder-approved). Executive Action
# priority is Business Logic, not Executive Language, and must never use
# the pending_executive_language sentinel — see _executive_actions().
EXECUTIVE_ACTION_PRIORITY_VALUES = ("Critical", "High", "Medium", "Low")

# No accountable-role data source exists anywhere upstream today
# (OperationalSituation/OIE/OCE carry no role or department-assignment
# concept). Never invented. Owner may be determined in future versions
# through Company Brain role mapping.
EXECUTIVE_ACTION_OWNER_NOT_YET_ASSIGNED = "Accountable role not yet assigned."


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

    def _pending(self, note: str) -> dict[str, Any]:
        return {"status": PENDING_EXECUTIVE_LANGUAGE, "note": note}

    def _executive_priority(self, situation: OperationalSituation) -> dict[str, Any]:
        # PDS-001 §5.1 structure: four named elements. No approved rule maps
        # situation.severity to an Attention Level value yet, so all four
        # stay pending rather than guessing a mapping.
        return {
            "attention_level": self._pending(
                "Executive Priority attention level pending Aboura's Executive "
                "Brief Design Principles (PDS-001 §5.1)."
            ),
            "situation": self._pending(
                "Executive Priority situation framing pending Aboura's Executive "
                "Brief Design Principles (PDS-001 §5.1)."
            ),
            "business_risk": self._pending(
                "Executive Priority business risk framing pending Aboura's "
                "Executive Brief Design Principles (PDS-001 §5.1)."
            ),
            "executive_trigger": self._pending(
                "Executive Priority executive trigger framing pending Aboura's "
                "Executive Brief Design Principles (PDS-001 §5.1)."
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
        # PDS-001 §5.2 structure: three named elements.
        return {
            "executive_interpretation": self._pending(
                "Executive Assessment interpretation pending Aboura's design "
                "(PDS-001 §5.2)."
            ),
            "business_meaning": self._pending(
                "Executive Assessment business meaning pending Aboura's design "
                "(PDS-001 §5.2)."
            ),
            "executive_recommendation_context": self._pending(
                "Executive Assessment recommendation context pending Aboura's "
                "design (PDS-001 §5.2)."
            ),
        }

    def _business_impact(self, situation: OperationalSituation) -> dict[str, Any]:
        return {
            "operational": self._why_it_matters(situation),
            "financial": (
                "Financial impact cannot currently be quantified because the "
                "required cost and revenue inputs are unavailable."
            ),
            "strategic": self._pending(
                "Strategic impact framing pending Aboura's Business Impact "
                "Framework instantiation (PDS-001 §5.3)."
            ),
        }

    def _executive_actions(self, situation: OperationalSituation) -> list[dict[str, Any]]:
        evidence_refs = [item.get("signal_type") for item in situation.evidence]
        return [
            {
                "action": check,
                # Priority is Business Logic, not Executive Language
                # (Founder decision, Executive Language Completion) — never
                # the pending_executive_language sentinel. None means no
                # priority-assignment rule has been approved yet. Accepted
                # vocabulary once assigned: EXECUTIVE_ACTION_PRIORITY_VALUES.
                "priority": None,
                "reason": PENDING_EXECUTIVE_LANGUAGE,
                "expected_outcome": PENDING_EXECUTIVE_LANGUAGE,
                "owner": EXECUTIVE_ACTION_OWNER_NOT_YET_ASSIGNED,
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
                "field": "executive_priority.attention_level",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_priority.situation",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_priority.business_risk",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_priority.executive_trigger",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_assessment.executive_interpretation",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_assessment.business_meaning",
                "source_type": SOURCE_TYPE_SYNTHESIS,
                "source_ref": None,
                "trace_status": TRACE_STATUS_PENDING,
            },
            {
                "field": "executive_assessment.executive_recommendation_context",
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
                    "field": f"executive_actions[{index}].priority",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    # Priority is Business Logic, not Executive Language — no
                    # priority-assignment rule has been approved yet. Distinct
                    # from the executive-language-pending fields below.
                    "source_ref": {
                        "reason": "no priority-assignment business rule approved yet",
                    },
                    "trace_status": TRACE_STATUS_PENDING,
                }
            )
            trace.append(
                {
                    "field": f"executive_actions[{index}].reason",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    "source_ref": None,
                    "trace_status": TRACE_STATUS_PENDING,
                }
            )
            trace.append(
                {
                    "field": f"executive_actions[{index}].expected_outcome",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    "source_ref": None,
                    "trace_status": TRACE_STATUS_PENDING,
                }
            )
            trace.append(
                {
                    "field": f"executive_actions[{index}].owner",
                    "source_type": SOURCE_TYPE_SYNTHESIS,
                    "source_ref": {
                        "reason": (
                            "no accountable-role data source available; owner "
                            "may be determined in future versions through "
                            "Company Brain role mapping"
                        ),
                    },
                    "trace_status": TRACE_STATUS_COARSE,
                }
            )

        return trace
