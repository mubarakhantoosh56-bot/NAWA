"""Lightweight root-cause reasoning for NAWA operational decisions."""

from __future__ import annotations

from typing import Any


IMPACT_ORDER = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "": 1,
}

FMCG_CAUSE_RULES = (
    {
        "signals": ("demand", "sales growth", "orders up", "low stock", "stock-out", "stock out"),
        "bottleneck": "Demand is running ahead of available stock.",
        "chain": [
            "Sales demand is increasing while available inventory is constrained.",
            "Sales commitments may exceed production or warehouse readiness.",
            "Fulfillment reliability and customer trust become the immediate operating risk.",
        ],
        "impact": "Supply risk, missed sales, emergency replenishment, and service-level pressure.",
        "risk": "Revenue growth can turn into customer dissatisfaction if stock is not protected before new commitments.",
        "action": "CEO/Operations: reconcile sales commitments with stock and production availability within 24 hours.",
    },
    {
        "signals": ("downtime", "line speed", "line stopped", "overtime", "wastage"),
        "bottleneck": "Production reliability is constraining fulfillment capacity.",
        "chain": [
            "Line instability reduces finished-goods output.",
            "Overtime or wastage increases the cost of catching up.",
            "Warehouse and distribution receive late or unstable supply, creating service pressure.",
        ],
        "impact": "Fulfillment bottleneck, overtime cost, wastage, and margin pressure.",
        "risk": "Operating margin deteriorates if the business tries to recover output through overtime instead of fixing line reliability.",
        "action": "Production: stabilize the line today, quantify lost output, and give Sales/Distribution a revised commitment window.",
    },
    {
        "signals": ("complaint", "market issue", "return", "delayed production", "not ready", "pending qa"),
        "bottleneck": "Customer-facing execution is unstable because upstream readiness is not synchronized.",
        "chain": [
            "Market complaints indicate customer expectations are not matching execution reality.",
            "Production or QA readiness is affecting stock release.",
            "Sales and distribution absorb the failure through escalations, returns, or missed delivery windows.",
        ],
        "impact": "Customer complaints, fulfillment exceptions, sales escalation, and reputational risk.",
        "risk": "Repeated complaints can convert operational friction into lost accounts or discount pressure.",
        "action": "Operations: run a cross-functional exception review today covering Production, Warehouse, Distribution, and Sales.",
    },
    {
        "signals": ("collections", "payment delay", "credit", "discount", "cash"),
        "bottleneck": "Commercial execution is creating cash and margin exposure.",
        "chain": [
            "Sales or customer commitments are not converting cleanly into cash.",
            "Discounts, payment delays, or credit exposure reduce financial flexibility.",
            "Finance must govern terms before growth adds more working-capital pressure.",
        ],
        "impact": "Cash-flow pressure, margin leakage, and weaker ability to fund operations.",
        "risk": "Growth becomes less profitable if collections and discount approvals lag behind sales activity.",
        "action": "Finance/Sales: lock payment follow-up owners and require approval for risky terms before the next order cycle.",
    },
)


def build_root_cause_reasoning(
    *,
    department_key: str,
    detected_patterns: list[dict[str, Any]],
    operational_events: list[dict[str, str]],
    related_departments: list[str],
) -> dict[str, Any]:
    """Build an explicit COO-style root-cause reasoning object."""

    focus = _highest_impact_pattern(detected_patterns)
    evidence_text = _evidence_text(detected_patterns, operational_events)
    rule = _match_fmcg_rule(evidence_text)

    affected_departments = _affected_departments(focus, related_departments)
    highest_issue = focus.get("finding_type", "bottleneck") if focus else "bottleneck"
    bottleneck = (
        rule["bottleneck"]
        if rule
        else _default_bottleneck(department_key, focus)
    )
    cause_chain = (
        rule["chain"]
        if rule
        else _default_chain(department_key, focus)
    )
    business_risk = (
        rule["risk"]
        if rule
        else _default_risk(focus)
    )
    impact = (
        rule["impact"]
        if rule
        else _default_impact(department_key)
    )
    first_action = (
        rule["action"]
        if rule
        else (focus.get("suggested_action") if focus else "Assign an owner and confirm the next operational checkpoint within 24 hours.")
    )

    return {
        "highest_impact_issue": highest_issue,
        "likely_operational_bottleneck": bottleneck,
        "probable_cause_effect_chain": cause_chain,
        "affected_departments": affected_departments,
        "operational_impact": impact,
        "business_risk": business_risk,
        "recommended_executive_action": first_action,
        "priority_basis": _priority_basis(focus),
        "narrative_structure": [
            "what happened",
            "why it happened",
            "which departments are affected",
            "operational impact",
            "business risk",
            "recommended executive action",
        ],
        "avoid_generic_language": [
            "there are challenges",
            "performance should improve",
            "there are operational risks",
        ],
    }


def _highest_impact_pattern(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    if not patterns:
        return {}
    return max(
        patterns,
        key=lambda item: (
            IMPACT_ORDER.get(str(item.get("severity") or ""), 0),
            int(item.get("confidence") or 0),
            1 if item.get("finding_type") in {"risk", "bottleneck", "issue"} else 0,
        ),
    )


def _match_fmcg_rule(text: str) -> dict[str, Any] | None:
    lowered = text.lower()
    best_rule = None
    best_score = 0
    for rule in FMCG_CAUSE_RULES:
        score = sum(1 for signal in rule["signals"] if signal in lowered)
        if score > best_score:
            best_score = score
            best_rule = rule
    return best_rule if best_score else None


def _evidence_text(patterns: list[dict[str, Any]], events: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for pattern in patterns[:5]:
        parts.extend(str(item) for item in pattern.get("evidence", []) if item)
        parts.append(str(pattern.get("suggested_action") or ""))
    for event in events[:5]:
        parts.append(str(event.get("summary") or ""))
        parts.append(str(event.get("category") or ""))
        parts.append(str(event.get("priority") or ""))
    return " ".join(parts)


def _affected_departments(
    focus: dict[str, Any],
    related_departments: list[str],
) -> list[str]:
    departments = []
    department = str(focus.get("department") or "").strip()
    if department:
        departments.append(department)
    for item in focus.get("related_departments", []) if focus else []:
        if isinstance(item, str):
            departments.append(item)
    for relationship in related_departments[:4]:
        department_name = relationship.split(":", 1)[0].strip().lower()
        if department_name:
            departments.append(department_name)
    return _dedupe(departments)[:5]


def _default_bottleneck(department_key: str, focus: dict[str, Any]) -> str:
    if focus:
        department = focus.get("department") or department_key
        finding_type = focus.get("finding_type") or "issue"
        return f"{str(department).title()} is the current {finding_type} control point."
    if department_key == "ceo":
        return "The highest-impact bottleneck is the cross-department handoff between demand, supply, and fulfillment."
    return f"{department_key.title()} needs a clearer handoff into the next operating function."


def _default_chain(department_key: str, focus: dict[str, Any]) -> list[str]:
    evidence = focus.get("evidence", []) if focus else []
    first_evidence = str(evidence[0]) if evidence else "Recent operational updates show execution friction."
    return [
        first_evidence,
        "The issue affects the next department in the operating chain.",
        "If not closed quickly, it creates service, margin, cash, or customer-commitment pressure.",
    ]


def _default_risk(focus: dict[str, Any]) -> str:
    severity = str(focus.get("severity") or "medium") if focus else "medium"
    return f"The business risk is {severity} because the issue can spread from local execution into customer service, margin, or cash exposure."


def _default_impact(department_key: str) -> str:
    if department_key == "sales":
        return "Sales commitments may outpace operational readiness."
    if department_key == "finance":
        return "Margin and cash discipline may weaken if operational leakage continues."
    if department_key == "production":
        return "Output, wastage, and downstream fulfillment reliability are exposed."
    return "Service level, execution speed, margin, and cross-department accountability are exposed."


def _priority_basis(focus: dict[str, Any]) -> str:
    if not focus:
        return "Priority is based on operational impact and missing evidence."
    return (
        f"Priority is based on {focus.get('severity', 'medium')} severity, "
        f"{focus.get('confidence', 0)} confidence, and evidence from {focus.get('department', 'operations')}."
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = value.strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result
