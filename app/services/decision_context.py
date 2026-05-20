"""Lightweight Decision Context Engine for NAWA FMCG MVP."""

from __future__ import annotations

import json
from typing import Any

from app.services.operational_pattern_detector import detect_operational_patterns
from app.services.organizational_intelligence import build_organizational_intelligence
from app.services.root_cause_reasoning import build_root_cause_reasoning

DEPARTMENT_ALIASES = {
    "sales_ai": "sales",
    "finance_ai": "finance",
    "marketing_ai": "marketing",
    "operations_ai": "operations",
    "warehouse_ai": "warehouse",
    "production_ai": "production",
}

FMCG_RELATIONSHIPS: dict[str, list[str]] = {
    "ceo": [
        "Production capacity drives inventory availability, distribution load, sales commitments, and cash exposure.",
        "Inventory accuracy shapes sales confidence, fulfillment reliability, wastage, and working capital.",
        "Distribution delays reduce fulfillment, damage customer service, and increase sales escalation.",
        "Wastage and returns reduce gross margin and should trigger finance and operations review.",
    ],
    "production": [
        "Warehouse: receives finished goods and flags stock quality or storage constraints.",
        "Sales: depends on realistic production commitments before promising availability.",
        "Distribution: depends on production timing to sequence delivery routes.",
        "Finance: monitors wastage, overtime, and cost-per-unit pressure.",
    ],
    "sales": [
        "Inventory/Warehouse: stock availability determines what Sales can commit to customers.",
        "Production: demand spikes require capacity confirmation before accepting large orders.",
        "Distribution: delayed delivery can turn booked sales into service failures.",
        "Finance: pricing, discounts, and payment terms affect margin and cash collection.",
    ],
    "finance": [
        "Sales: discounting, credit terms, and collections drive cash and margin risk.",
        "Production: wastage, overtime, and raw material variance affect profitability.",
        "Warehouse: excess stock ties working capital and increases expiry risk.",
        "Distribution: route inefficiency and delivery failures increase cost-to-serve.",
    ],
    "operations": [
        "Production: throughput and quality shape the operating plan.",
        "Warehouse: inventory accuracy and pick/pack speed shape fulfillment.",
        "Distribution: route execution determines customer service levels.",
        "Sales: demand signals should drive weekly execution priorities.",
    ],
    "warehouse": [
        "Sales: needs reliable stock visibility before accepting orders.",
        "Production: must align receipt schedules with storage capacity.",
        "Distribution: pick accuracy and staging quality affect delivery success.",
        "Finance: shrinkage, expiry, and excess inventory affect working capital.",
    ],
    "marketing": [
        "Sales: campaigns should create demand Sales can convert and fulfill.",
        "Inventory/Warehouse: promotions must match available stock and expiry windows.",
        "Production: demand campaigns may require capacity checks.",
        "Finance: campaign economics must protect gross margin and CAC discipline.",
    ],
}

MOCK_KPI_SUMMARIES: dict[str, list[str]] = {
    "ceo": [
        "MVP directional KPIs: service level/OTIF, stock availability, gross margin, wastage, cash conversion, production adherence.",
        "Watch the chain from demand forecast to production, warehouse, distribution, sales, and collections.",
    ],
    "production": [
        "MVP directional KPIs: production plan adherence, line utilization, defect rate, wastage, downtime, overtime cost.",
        "Primary signal: output quality and timing must support committed sales and delivery windows.",
    ],
    "sales": [
        "MVP directional KPIs: sales run-rate, fill-rate lost sales, order conversion, average discount, collections risk.",
        "Primary signal: sales commitments are only strong when stock and delivery capacity are confirmed.",
    ],
    "finance": [
        "MVP directional KPIs: gross margin, cash collection, stock holding cost, wastage cost, discount leakage.",
        "Primary signal: profitability risk usually appears through wastage, excess inventory, delivery cost, or weak collections.",
    ],
    "operations": [
        "MVP directional KPIs: OTIF, backlog, cycle time, route adherence, exception rate, capacity utilization.",
        "Primary signal: bottlenecks often sit between production release, warehouse staging, and distribution execution.",
    ],
    "warehouse": [
        "MVP directional KPIs: inventory accuracy, stock-outs, expiry risk, pick accuracy, shrinkage, receiving backlog.",
        "Primary signal: inventory errors create sales promises the operation cannot fulfill.",
    ],
    "marketing": [
        "MVP directional KPIs: campaign-to-order conversion, promo margin, stock-backed promotion coverage, CAC signal.",
        "Primary signal: FMCG campaigns should match available stock, margin guardrails, and delivery capacity.",
    ],
}

BOTTLENECK_HINTS: dict[str, list[str]] = {
    "ceo": ["Cross-functional decisions stall when sales demand, production capacity, and inventory reality are not reconciled weekly."],
    "production": ["Production delays or quality fallout can cascade into warehouse congestion, missed delivery windows, and margin loss."],
    "sales": ["Sales targets become risky when inventory availability, delivery dates, or finance terms are unclear."],
    "finance": ["Margin leakage can hide inside discounts, wastage, returns, overtime, and high delivery cost-to-serve."],
    "operations": ["Fulfillment risk usually compounds across handoffs: production release, warehouse staging, route planning, delivery confirmation."],
    "warehouse": ["Stock inaccuracy creates false availability, delayed picks, sales disputes, and emergency replenishment."],
    "marketing": ["Promotions can generate unprofitable demand if they ignore stock age, capacity, and delivery cost."],
}


def build_decision_context(
    *,
    context: dict[str, Any],
    response_language: str,
    memory_events: list[dict[str, Any]] | None = None,
    memory_profile: dict[str, Any] | None = None,
    memory_facts: list[dict[str, Any]] | None = None,
    rag_knowledge_available: bool = False,
) -> dict[str, Any]:
    """Assemble a compact operational context object before AI generation."""

    department = _resolve_department(context)
    profile = _compact_company_profile(context.get("company_intelligence_profile"), memory_profile)
    organization = context.get("organizational_intelligence")
    if not isinstance(organization, dict):
        organization = build_organizational_intelligence(
            company_profile=profile,
            snapshot=None,
        )
    department_key = department["key"]
    detected_patterns = detect_operational_patterns(
        memory_events or [],
        active_department=department_key,
    )

    trends = _build_trends(profile, department_key, rag_knowledge_available, memory_facts or [])
    bottlenecks = _merge_unique(
        _profile_challenges(profile),
        BOTTLENECK_HINTS.get(department_key, BOTTLENECK_HINTS["ceo"]),
    )
    risks = _build_risks(department_key, profile)
    related_departments = FMCG_RELATIONSHIPS.get(department_key, FMCG_RELATIONSHIPS["ceo"])
    operational_events = _compact_operational_events(memory_events or [])
    unified_capture_context = _compact_unified_capture_context(memory_events or [])
    root_cause_reasoning = build_root_cause_reasoning(
        department_key=department_key,
        detected_patterns=detected_patterns,
        operational_events=operational_events,
        related_departments=related_departments,
    )

    return {
        "department": department,
        "role_perspective": _resolve_role_perspective(context),
        "company_profile": profile,
        "organizational_intelligence": organization,
        "key_kpis": MOCK_KPI_SUMMARIES.get(department_key, MOCK_KPI_SUMMARIES["ceo"]),
        "trends": trends,
        "bottlenecks": bottlenecks[:6],
        "related_departments": related_departments,
        "operational_risks": risks[:6],
        "memory_events": _compact_memory_events(memory_events or []),
        "raw_input_summaries": unified_capture_context["raw_input_summaries"],
        "parsed_entities": unified_capture_context["parsed_entities"],
        "structured_drafts": unified_capture_context["structured_drafts"],
        "operational_events": operational_events,
        "detected_patterns": detected_patterns,
        "root_cause_reasoning": root_cause_reasoning,
        "uploaded_file_summaries": _uploaded_file_summaries(context, rag_knowledge_available),
        "impact_assessment": _impact_assessment(department_key),
        "response_enforcement": _response_enforcement(),
        "confidence": "MVP directional context; use exact user, memory, profile, and retrieved-file facts when available.",
        "response_language": "ar" if response_language == "ar" else "en",
    }


def build_decision_context_prompt_block(decision_context: dict[str, Any]) -> str:
    if not decision_context:
        return ""

    payload = json.dumps(decision_context, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            "DECISION CONTEXT ENGINE (MVP - INTERNAL):",
            payload,
            "MANDATORY OPERATIONAL RESPONSE ENFORCEMENT:",
            "1) Use this hierarchy in order: root_cause_reasoning, detected_patterns, operational_events, KPI/trend context, company profile, generic executive formatting.",
            "2) Final CEO executive_summary MUST explicitly include the root operational bottleneck, cause/effect chain, affected departments, operational impact, business impact, and priority executive action.",
            "3) The final answer MUST reference operational events, KPI direction, detected patterns, and department relationships when present in the context.",
            "4) The narrative must answer: what is actually happening, why it is happening, what is affected, what risk this creates, and what should happen next.",
            "5) Keep it concise: use the existing response headings, but make every bullet operational and evidence-aware.",
            "RULES:",
            "- Use this context before generating the recommendation; do not mention the Decision Context Engine by name.",
            "- Treat raw_input_summaries, parsed_entities, and structured_drafts as first-capture operational evidence that may explain the event trail.",
            "- Use organizational_intelligence to reason about company divisions, department dependencies, HR execution signals, KPI ownership, workflows, users, and integration sources.",
            "- Identify the likely root cause, the cross-department dependency, and the operational impact.",
            "- Use root_cause_reasoning as the operating narrative spine: what happened, why it happened, affected departments, operational impact, business risk, executive action.",
            "- Give extra weight to operational_events because they came from submitted daily forms.",
            "- Use detected_patterns to infer risks, mistakes, positives, bottlenecks, missing follow-ups, KPI changes, and recurring friction even when the user did not state them explicitly.",
            "- For FMCG decisions, reason across production, inventory/warehouse, sales, distribution/operations, and finance.",
            "- CEO responses must explicitly reason about execution capacity, fulfillment constraints, production readiness, distribution pressure, sales impact, profitability pressure, and operational dependencies when relevant.",
            "- Apply FMCG cause rules: rising demand plus slower production line means fulfillment bottleneck; overtime plus delayed collections means margin pressure; delayed production plus sales growth means execution instability; low stock plus sales growth means supply risk.",
            "- If the user asks for a report, CEO scope may summarize all departments; department roles must stay department-scoped unless evidence names another dependency.",
            "- CEO responses must summarize biggest risks, operational mistakes, positive signals, dependencies, and recommended decisions when detected_patterns are present.",
            "- Department responses must summarize department-specific problems, repeated mistakes, positive signals, and follow-up needs when detected_patterns are present.",
            "- Prioritize actions that protect fulfillment, margin, cash, service level, and execution speed.",
            "- Recommended Actions must be operationally actionable, prioritized, department-aware, and time-sensitive.",
            "- Block vague phrases unless backed by concrete operational reasoning: 'there are challenges', 'performance should improve', 'focus on efficiency', 'increase revenue', 'there are operational risks'. Replace them with concrete bottlenecks, inferred cause/effect, evidence, owner, and deadline.",
            "- Treat MVP directional KPIs as operating hints, not audited metrics; do not present mock values as measured facts.",
            "- Keep the answer concise, executive, structured, decisive, and aligned to response_language.",
        ]
    )


def _response_enforcement() -> dict[str, Any]:
    return {
        "generation_hierarchy": [
            "root_cause_reasoning",
            "detected_patterns",
            "operational_events",
            "key_kpis_and_trends",
            "company_profile",
            "generic_executive_formatting",
        ],
        "mandatory_ceo_elements": [
            "root operational bottleneck",
            "cause/effect chain",
            "affected departments",
            "operational impact",
            "business impact",
            "priority executive action",
        ],
        "mandatory_evidence": [
            "operational events",
            "KPI direction",
            "detected patterns",
            "department relationships",
        ],
        "narrative_questions": [
            "what is actually happening",
            "why it is happening",
            "what is affected",
            "what risk this creates",
            "what should happen next",
        ],
        "blocked_generic_phrases": [
            "there are challenges",
            "performance should improve",
            "focus on efficiency",
            "increase revenue",
            "there are operational risks",
        ],
        "fmcg_examples": [
            "rising demand + slower production line = fulfillment bottleneck",
            "overtime + delayed collections = margin pressure",
            "delayed production + sales growth = execution instability",
        ],
    }


def _resolve_department(context: dict[str, Any]) -> dict[str, Any]:
    department = context.get("aimx_department")
    if not isinstance(department, dict):
        return {"key": "ceo", "name": "CEO", "scope": "company_wide"}

    raw_type = str(department.get("department_type") or "").strip().lower()
    key = DEPARTMENT_ALIASES.get(raw_type, raw_type or "department")
    return {
        "key": key,
        "name": str(department.get("name") or key.title()),
        "type": raw_type,
        "scope": "department",
    }


def _resolve_role_perspective(context: dict[str, Any]) -> dict[str, str]:
    role = context.get("nawa_role") if isinstance(context.get("nawa_role"), dict) else {}
    slug = str(role.get("slug") or "").strip().lower()
    if slug in {"owner", "admin", "ceo"}:
        scope = "company_wide"
    elif slug:
        scope = "department_scoped"
    else:
        scope = "unknown"
    return {"slug": slug or "unknown", "scope": scope}


def _compact_company_profile(
    profile: Any,
    memory_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    source = profile if isinstance(profile, dict) else {}
    memory_profile = memory_profile or {}
    fields = (
        "company_name",
        "industry",
        "business_type",
        "country_market",
        "company_size",
        "departments_enabled",
        "primary_goals",
        "current_operational_challenges",
        "growth_priorities",
    )
    compact: dict[str, Any] = {}
    for field in fields:
        value = source.get(field) or memory_profile.get(field)
        if value:
            compact[field] = value
    return compact


def _build_trends(
    profile: dict[str, Any],
    department_key: str,
    rag_knowledge_available: bool,
    memory_facts: list[dict[str, Any]],
) -> list[str]:
    trends: list[str] = []
    if profile.get("growth_priorities"):
        trends.append(f"Growth priority: {profile['growth_priorities']}")
    if profile.get("primary_goals"):
        trends.append(f"Goal pressure: {profile['primary_goals']}")
    if rag_knowledge_available:
        trends.append("Uploaded file evidence is available and should be used when directly relevant.")
    for fact in memory_facts[:3]:
        key = str(fact.get("fact_key") or fact.get("fact_type") or "").strip()
        value = str(fact.get("fact_value") or "").strip()
        if value:
            trends.append(f"Memory signal: {key} = {value}" if key else f"Memory signal: {value}")
    trends.append(_department_trend(department_key))
    return _merge_unique(trends)


def _department_trend(department_key: str) -> str:
    trends = {
        "production": "Production reliability is a leading indicator for distribution promises and service level.",
        "sales": "Demand quality should be checked against available stock, delivery capacity, and margin guardrails.",
        "finance": "Profitability pressure is likely tied to discounts, wastage, inventory carrying cost, or delivery inefficiency.",
        "operations": "Fulfillment performance depends on handoff discipline between production, warehouse, and distribution.",
        "warehouse": "Inventory accuracy is the control point for stock-outs, expiry, fulfillment, and sales confidence.",
        "marketing": "Promotion intensity must stay synchronized with stock, margin, and delivery capacity.",
    }
    return trends.get(department_key, "Executive decisions should connect KPI movement to cross-department operating constraints.")


def _profile_challenges(profile: dict[str, Any]) -> list[str]:
    challenge = str(profile.get("current_operational_challenges") or "").strip()
    return [f"Profile challenge: {challenge}"] if challenge else []


def _build_risks(department_key: str, profile: dict[str, Any]) -> list[str]:
    risks = [
        "Generic recommendations may miss the operational tradeoff between fulfillment, margin, and cash.",
    ]
    if _looks_like_fmcg(profile):
        risks.append("FMCG risk: stock-outs, expiry, wastage, and delivery failures can quickly become margin and customer-service losses.")
    risks.extend(
        {
            "production": ["Late production release can create distributor delays and lost sales.", "Quality issues increase returns, wastage, and finance exposure."],
            "sales": ["Overpromising without stock confirmation can damage fulfillment and customer trust.", "Discounting without finance guardrails can leak margin."],
            "finance": ["Cash and margin can deteriorate if stock, wastage, returns, and discounts are reviewed separately."],
            "operations": ["Weak handoffs can hide the true bottleneck and create repeated fulfillment misses."],
            "warehouse": ["Inventory variance can mislead Sales and trigger unnecessary production or emergency delivery."],
            "marketing": ["Campaign demand can overload operations if stock and delivery capacity are not checked first."],
        }.get(department_key, [])
    )
    return _merge_unique(risks)


def _impact_assessment(department_key: str) -> list[str]:
    impact = {
        "production": ["Primary impact: service level and inventory availability.", "Secondary impact: distribution cost, sales confidence, wastage, and margin."],
        "sales": ["Primary impact: revenue quality and customer commitments.", "Secondary impact: stock pressure, fulfillment reliability, cash collection, and margin."],
        "finance": ["Primary impact: margin protection and cash discipline.", "Secondary impact: pricing approvals, inventory exposure, wastage, and cost-to-serve."],
        "operations": ["Primary impact: fulfillment reliability and execution speed.", "Secondary impact: customer service, route cost, backlog, and sales escalations."],
        "warehouse": ["Primary impact: stock availability and fulfillment accuracy.", "Secondary impact: expiry, shrinkage, working capital, and sales confidence."],
        "marketing": ["Primary impact: demand quality and promo economics.", "Secondary impact: stock pressure, sales conversion, delivery capacity, and margin."],
    }
    return impact.get(
        department_key,
        ["Primary impact: cross-department operating performance.", "Secondary impact: service level, margin, cash, and execution focus."],
    )


def _compact_memory_events(events: list[dict[str, Any]]) -> list[str]:
    compact: list[str] = []
    for event in events[:5]:
        summary = str(event.get("executive_summary") or event.get("user_message") or "").strip()
        if summary:
            compact.append(summary[:220])
    return compact


def _compact_operational_events(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for event in events[:10]:
        event_type = str(event.get("event_type") or "")
        if not event_type.startswith("operational."):
            continue
        summary = str(event.get("executive_summary") or event.get("user_message") or "").strip()
        context = event.get("context") if isinstance(event.get("context"), dict) else {}
        classification = context.get("classification") if isinstance(context.get("classification"), dict) else {}
        if summary:
            compact.append(
                {
                    "event_type": event_type,
                    "summary": summary[:260],
                    "source_role": str(context.get("source_role") or ""),
                    "source_department": str(context.get("source_department") or classification.get("inferred_department") or ""),
                    "target_department": str(context.get("target_department") or classification.get("inferred_department") or ""),
                    "category": str(context.get("category") or ""),
                    "priority": str(context.get("priority") or ""),
                }
            )
    return compact[:5]


def _compact_unified_capture_context(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    raw_input_summaries: list[dict[str, Any]] = []
    parsed_entities: list[dict[str, Any]] = []
    structured_drafts: list[dict[str, Any]] = []

    for event in events[:10]:
        context = event.get("context") if isinstance(event.get("context"), dict) else {}
        raw_input_id = context.get("raw_input_id")
        if raw_input_id:
            raw_input_summaries.append(
                {
                    "raw_input_id": str(raw_input_id),
                    "summary": str(event.get("executive_summary") or event.get("user_message") or "").strip()[:240],
                    "classification": context.get("classification") if isinstance(context.get("classification"), dict) else {},
                }
            )
        entities = context.get("parsed_entities") if isinstance(context.get("parsed_entities"), list) else []
        for entity in entities[:8]:
            if not isinstance(entity, dict):
                continue
            parsed_entities.append(
                {
                    "raw_input_id": str(raw_input_id or entity.get("raw_input_id") or ""),
                    "entity_type": str(entity.get("entity_type") or ""),
                    "entity_value": str(entity.get("entity_value") or "")[:120],
                    "confidence": entity.get("confidence"),
                }
            )
        draft_id = context.get("structured_record_draft_id")
        if draft_id:
            structured_drafts.append(
                {
                    "structured_record_draft_id": str(draft_id),
                    "raw_input_id": str(raw_input_id or ""),
                    "category": str(context.get("category") or ""),
                    "priority": str(context.get("priority") or ""),
                }
            )

    return {
        "raw_input_summaries": raw_input_summaries[:5],
        "parsed_entities": parsed_entities[:20],
        "structured_drafts": structured_drafts[:5],
    }


def _uploaded_file_summaries(context: dict[str, Any], rag_knowledge_available: bool) -> list[str]:
    raw = context.get("uploaded_file_summaries")
    if isinstance(raw, list):
        return [str(item).strip()[:220] for item in raw if str(item).strip()][:5]
    if rag_knowledge_available:
        return ["Relevant uploaded file excerpts were retrieved for this request."]
    return []


def _looks_like_fmcg(profile: dict[str, Any]) -> bool:
    text = " ".join(str(value) for value in profile.values()).lower()
    keywords = ("fmcg", "food", "beverage", "distribution", "warehouse", "inventory", "retail", "fulfillment")
    return any(keyword in text for keyword in keywords)


def _merge_unique(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for group in groups:
        for item in group:
            cleaned = " ".join(str(item).split())
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                merged.append(cleaned)
    return merged
