"""Lightweight Decision Context Engine for NAWA FMCG MVP."""

from __future__ import annotations

import json
from typing import Any

from app.services.operational_pattern_detector import detect_operational_patterns
from app.services.organizational_intelligence import build_organizational_intelligence
from app.services.root_cause_reasoning import build_root_cause_reasoning

# M6: AI Reasoning Layer - reasoning states (never epistemic origins; see
# app/services/operational_truth_context.py's OBSERVED/DERIVED/INFERRED,
# which is a different, unrelated vocabulary). The LLM chooses which of
# these three applies each turn (Decision Context only supplies bounded,
# deterministic structural signals below - it never decides the state
# itself, since that requires judgment about whether evidence currently
# supports a company preference, not a fact Python can compute).
REASONING_STATE_ALIGNED = "aligned"
REASONING_STATE_TENSION = "tension"
REASONING_STATE_INSUFFICIENT_EVIDENCE = "insufficient_evidence"
REASONING_STATES = (
    REASONING_STATE_ALIGNED,
    REASONING_STATE_TENSION,
    REASONING_STATE_INSUFFICIENT_EVIDENCE,
)

# Every M5 Company Brain type except INSTITUTIONAL_MEMORY (generic per-tenant
# memory facts, not curated company doctrine - see
# app/services/company_brain_context.py). Reused, not redefined: this is the
# same frozen Layer-2 type vocabulary M5 already established, not a new
# taxonomy invented for M6.
COMPANY_BRAIN_POLICY_TYPES = frozenset(
    {
        "POLICY",
        "PREFERENCE",
        "DECISION_RULE",
        "OPERATING_PRINCIPLE",
        "GOAL",
        "RISK_POSTURE",
        "MANAGEMENT_STANDARD",
    }
)

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
    operational_truth_context: list[dict[str, Any]] | None = None,
    company_brain_context: list[dict[str, Any]] | None = None,
    operational_semantics_topics: list[str] | None = None,
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
    reasoning_reference_catalog = _build_reasoning_reference_catalog(
        operational_truth_context=operational_truth_context or [],
        company_brain_context=company_brain_context or [],
    )
    reasoning_signals = _build_reasoning_signals(reasoning_reference_catalog)

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
        # M4 Slice 2: bounded KAE/OCE evidence (Evidence.to_dict() payloads,
        # see app/services/operational_truth_context.py). Kept as its own
        # key, conceptually distinct from memory_events/operational_events/
        # trends (company memory/policy) - Truth Context is never merged
        # into those, and neither overwrites the other (Founder Truth
        # Principle: conflicts are surfaced, not silently reconciled).
        "operational_truth_context": operational_truth_context or [],
        # M5: bounded Company Brain claims (CompanyBrainItem.to_dict()
        # payloads, see app/services/company_brain_context.py) - a
        # DIFFERENT question from operational_truth_context ("what is
        # objectively happening" vs "what does this company believe,
        # prefer, prioritize, require, prohibit, or normally do"). Never
        # merged into operational_truth_context, memory_events,
        # operational_events, or trends - kept as its own key so Truth and
        # Company Brain can disagree in the prompt without one silently
        # overwriting the other.
        "company_brain_context": company_brain_context or [],
        # Operational Semantics topic labels only (never full content, never
        # classified as policy - Founder instruction, Step 6): terminology/
        # meaning context is a third, distinct concept from both Truth and
        # Company Brain.
        "operational_semantics_topics": operational_semantics_topics or [],
        # M6: bounded, deterministic structural signals only (booleans and
        # counts derived from operational_truth_context/company_brain_context
        # already assembled above by M4/M5 - never reloaded independently,
        # never a new tenant/business-unit source). This is NOT a tension
        # verdict: it never decides aligned/tension/insufficient_evidence
        # itself, it only tells the model which materials are actually
        # USABLE this turn so reasoning is never silently skipped, based on
        # assumed-absent evidence, or fooled by mere row presence (an
        # INFERRED-only or missing Truth item does not count as usable
        # evidence; a conflicted/unresolved Company Brain item does not
        # count as settled policy - see _build_reasoning_signals).
        "reasoning_signals": reasoning_signals,
        # M6: turn-local T#/CB# reference handles for decision provenance
        # (recommendation_basis). Internal-only - see INTERNAL_ONLY_DECISION_
        # CONTEXT_KEYS / public_decision_context(): never reloads DB/files,
        # only classifies the operational_truth_context/company_brain_context
        # already supplied above.
        "reasoning_reference_catalog": reasoning_reference_catalog,
        "detected_patterns": detected_patterns,
        "root_cause_reasoning": root_cause_reasoning,
        "uploaded_file_summaries": _uploaded_file_summaries(context, rag_knowledge_available),
        "impact_assessment": _impact_assessment(department_key),
        "response_enforcement": _response_enforcement(),
        "confidence": "MVP directional context; use exact user, memory, profile, and retrieved-file facts when available.",
        "response_language": "ar" if response_language == "ar" else "en",
    }


# M6: internal prompt-control/validation metadata that must never reach the
# public API response (app/api/chat.py -> ChatResponse.meta.context). These
# keys ARE used for prompt construction, the runtime reasoning_assessment
# validator, and the DECISION_CONTEXT_DEBUG snapshot (which captures the
# full decision_context dict before this filter is ever applied) - only the
# copy placed into the public response is reduced. This is distinct from
# the model-generated logic_json.reasoning_assessment, which is the
# auditable executive reasoning OUTPUT and does remain public.
INTERNAL_ONLY_DECISION_CONTEXT_KEYS = frozenset({"reasoning_signals", "reasoning_reference_catalog"})


def public_decision_context(decision_context: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of decision_context with M6 internal-only prompt-control
    metadata removed, safe to place into the public chat response."""
    if not isinstance(decision_context, dict):
        return decision_context
    return {k: v for k, v in decision_context.items() if k not in INTERNAL_ONLY_DECISION_CONTEXT_KEYS}


# M7 Slice 2A: explicit allowlist for meta.context (app/api/chat.py's
# ChatResponse.meta.context) - the ONLY top-level fields the public chat
# response may echo back. Replaces "pass the entire internal `context` dict
# accumulated during chat() straight through" with an explicit, auditable
# list. Derived only from currently-tested/required compatibility accesses:
# the three bridge-status keys, company_intelligence_profile, and (narrowed
# further below) decision_context.department / decision_context.
# operational_events - plus the new Slice 2A "explainability" block.
# Everything else chat() accumulates along the way (organizational_
# intelligence, the full operational_truth_context/company_brain_context
# lists, internal role/data-capture bookkeeping, raw client-echoed
# request.context fields, mock KPI scaffolding, internal UUID/path
# provenance, etc.) is intentionally dropped here.
PUBLIC_CONTEXT_ALLOWED_KEYS = frozenset(
    {
        "operational_events_bridge",
        "truth_context_bridge",
        "company_brain_bridge",
        "company_intelligence_profile",
        "decision_context",
        "explainability",
    }
)

# Once inside the (already reasoning_signals/reasoning_reference_catalog
# -stripped) public decision_context, only these two sub-keys survive -
# the exact two currently-tested compatibility accesses (department.key,
# operational_events). Full operational_truth_context/company_brain_context/
# organizational_intelligence/key_kpis/trends/etc. never reach the public
# response even though public_decision_context() above still carries them
# (that function's job is only to strip the M6-internal keys; this one
# narrows further to what the public contract actually needs).
PUBLIC_DECISION_CONTEXT_ALLOWED_KEYS = frozenset({"department", "operational_events"})


def public_context_allowlist(context: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict containing ONLY the approved public meta.context
    fields, safe to place into the public chat response. Never mutates the
    input `context` (which remains the full internal working dict used for
    logging/prompt construction earlier in the same turn)."""
    if not isinstance(context, dict):
        return {}

    public: dict[str, Any] = {
        key: context[key] for key in PUBLIC_CONTEXT_ALLOWED_KEYS if key in context
    }

    raw_decision_context = context.get("decision_context")
    if isinstance(raw_decision_context, dict):
        public["decision_context"] = {
            key: raw_decision_context[key]
            for key in PUBLIC_DECISION_CONTEXT_ALLOWED_KEYS
            if key in raw_decision_context
        }

    return public


def reasoning_prose_language_instruction(response_language: str | None) -> str:
    """response_language binds reasoning_assessment human-readable prose
    (operational_assessment/tensions/evidence_gaps/risk_assessment/etc.) -
    never reasoning_state (stays the English enum) or a T#/CB# reference
    ID. Single source of truth for this instruction text (Correction
    Round 1, 2A-F1): consumed both by the initial prompt (via
    build_decision_context_prompt_block) and by every repair/regeneration
    prompt through reasoning_language_contract(), so a candidate produced
    by ANY path is bound by the identical wording - never only inherited
    from the first message in a conversation an LLM may deprioritize once
    a later, more specific repair instruction is appended."""
    if response_language == "ar":
        return (
            "- response_language for this turn is 'ar': write operational_assessment, tensions, evidence_gaps, "
            "risk_assessment, and every other human-readable reasoning_assessment prose field in Arabic. "
            "reasoning_state stays the exact English enum value (aligned/tension/insufficient_evidence) and "
            "evidence_basis/company_basis/missing_evidence stay the exact reference IDs (T#/CB#) - never "
            "translate the enum value or a reference ID."
        )
    return (
        "- response_language for this turn is 'en': write operational_assessment, tensions, "
        "evidence_gaps, risk_assessment, and every other human-readable reasoning_assessment prose "
        "field in English."
    )


def company_brain_alignment_vocabulary_instruction(response_language: str | None) -> str:
    """The company_brain_alignment controlled vocabulary (Section 10) -
    same single-source-of-truth rationale as
    reasoning_prose_language_instruction above."""
    if response_language == "ar":
        return (
            "- company_brain_alignment must use EXACTLY one of these four Arabic phrases, verbatim, with no "
            "paraphrase and no translation of your own: 'مدعوم بالأدلة الحالية' (supported by current "
            "evidence), 'غير مدعوم بالأدلة الحالية' (not supported by current evidence), 'مدعوم جزئيًا' "
            "(partially supported), or 'لا يمكن التحديد' (cannot determine). Do not use these phrases to "
            "describe whether the policy itself is right or wrong."
        )
    return (
        "- Use only: 'supported by current evidence', 'not supported by current evidence', 'partially "
        "supported', or 'cannot determine' to describe whether a Company Brain position is currently "
        "actionable. Do not use these phrases to describe whether the policy itself is right or wrong."
    )


def reasoning_language_contract(response_language: str | None) -> str:
    """Combined reasoning-prose-language + company_brain_alignment-
    vocabulary contract, for prompts that need to freshly re-assert the
    FULL binding in one message (Correction Round 1, 2A-F1) - the legacy
    execution-structure retry, the operational-response regeneration
    instruction, and the M6 reasoning_assessment repair instruction all
    append this, so the binding does not rely on merely surviving from the
    initial prompt into a repair/regeneration candidate."""
    return "\n".join(
        [
            reasoning_prose_language_instruction(response_language),
            company_brain_alignment_vocabulary_instruction(response_language),
        ]
    )


def build_decision_context_prompt_block(decision_context: dict[str, Any]) -> str:
    if not decision_context:
        return ""

    payload = json.dumps(decision_context, ensure_ascii=False, indent=2)
    lines = [
        "DECISION CONTEXT ENGINE (MVP - INTERNAL):",
        payload,
    ]
    truth_context_section = _build_truth_context_section(
        decision_context.get("operational_truth_context")
    )
    if truth_context_section:
        lines.append(truth_context_section)
    company_brain_section = _build_company_brain_section(
        decision_context.get("company_brain_context"),
        decision_context.get("operational_semantics_topics"),
    )
    if company_brain_section:
        lines.append(company_brain_section)
    reasoning_signals_section = _build_reasoning_signals_section(
        decision_context.get("reasoning_signals")
    )
    if reasoning_signals_section:
        lines.append(reasoning_signals_section)
    lines.extend(
        [
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
            "- Operational Truth Context items (M4 Slice 2): OBSERVED means a direct source-backed operational fact; DERIVED means a deterministic calculation or trend; INFERRED means an AI-origin interpretation and must never be treated as a confirmed fact; UNKNOWN/missing origin means the origin is unresolved and must not be treated as observed.",
            "- Missing operational evidence means the value is unknown, not zero - never assume a missing water/feed/vet/temperature reading means zero or that no reading means no issue.",
            "- When Operational Truth Context source time is unresolved, do not describe that evidence as current, recent, fresh, or up to date - unresolved source time means freshness cannot be assumed.",
            "- Company-wide/aggregate operational evidence must not be presented as if it describes one specific hall/entity unless that evidence's own entity scope supports it.",
            "- Ground operational conclusions in the Operational Truth Context evidence actually provided; if evidence is insufficient or explicitly missing, say what is missing rather than inventing operational facts.",
            "- Operational Truth Context describes evidence-backed operational reality; Company Brain Context describes company policy, preference, philosophy, goals, and institutional context - they answer different questions and are never the same kind of statement.",
            "- Company Brain (policy/preference/philosophy) must never override contradictory operational evidence, and operational evidence must never erase or invalidate a legitimate company policy - if Truth and Company Brain disagree, state both and name the tension rather than picking a winner.",
            "- Do not treat a Company Brain preference, philosophy, or goal as an objective operational fact, and do not treat Company Brain institutional memory as current operational evidence.",
            "- Do not invent Company Brain policy that is not present in company_brain_context; if Company Brain information is missing or internally conflicted (conflict_state), say so explicitly.",
            "- Operational Semantics topics describe what company terms mean, not what management prefers or requires - never present them as policy.",
            "AI REASONING LAYER (M6) - RULES:",
            "- Populate raw_decision.reasoning_assessment on every response: reasoning_state (one of aligned/tension/insufficient_evidence - see Reasoning Signals for the allowed values), operational_assessment, company_brain_alignment, tensions, evidence_gaps, risk_assessment, confidence, and recommendation_basis (evidence_basis, company_basis, missing_evidence). These are auditable decision provenance, never hidden chain-of-thought - do not write step-by-step internal deliberation into any field.",
            reasoning_prose_language_instruction(decision_context.get("response_language")),
            "- Every Operational Truth Context item shown below is labeled with a reference ID (T1, T2, ...) and every Company Brain Context item shown below is labeled (CB1, CB2, ...). recommendation_basis.evidence_basis may ONLY cite a T# that is USABLE evidence (AVAILABLE with an OBSERVED or DERIVED origin - never missing, never inferred-only). recommendation_basis.company_basis may ONLY cite a CB# that is AUTHORITATIVE settled company doctrine (a curated policy-type item, not INSTITUTIONAL_MEMORY, whose authority is exactly 'authoritative' and which is not conflicted - never a merely-not-conflicted or unlabeled item). missing_evidence may only cite a T# that is itself missing or has unresolved source time. Never invent a reference ID, never cite a reference from the wrong section, and never cite a prose source (e.g. 'a report' or a made-up document name) - only these exact IDs are valid, and this is validated at runtime.",
            "- Reason in this order every time: first determine what the Operational Truth Context evidence actually supports; only then relate that to Company Brain Context; only then decide what action is justified. Never start from a Company Brain preference and search for supporting facts - that is confirmation bias.",
            "- Neither Operational Truth Context nor Company Brain Context automatically wins when they point in different directions. Do not say 'continue because this is company policy' and do not say 'ignore company strategy because evidence changed.' State the evidence, state the company position, name the tension explicitly, and evaluate whether current evidence supports acting on the company position now.",
            "- You may explicitly say current evidence does not support executing a Company Brain preference right now. This is an evidence-based recommendation about timing/conditions, not a claim that company policy is wrong - never mark a Company Brain item as incorrect.",
            "- When two technically valid actions are both supported by the evidence, Company Brain (risk posture, philosophy, priorities) may legitimately determine which one is recommended - if it does, say explicitly that the company's stated position influenced the choice.",
            company_brain_alignment_vocabulary_instruction(decision_context.get("response_language")),
            "- A correlation, hypothesis, or possible explanation must never be written as a confirmed cause. Only a DERIVED trend or an OBSERVED fact may be treated as established; an INFERRED explanation stays a hypothesis in the reasoning, explicitly labeled as such.",
            "- A Recommended Action is a proposal, never a fact - do not phrase a recommendation as something that has already happened or that is objectively true. Distinguish it from Facts/Key Insights.",
            "- If a recommendation depends materially on evidence that is missing (missing_evidence_count > 0 in Reasoning Signals), do not assign it a confident root cause: give a conditional recommendation, recommend collecting the missing evidence first, and lower confidence accordingly.",
            "- Confidence must go down, not stay flat, when: material evidence is missing, a Truth item's source time is unresolved (do not imply freshness), or a Company Brain item used as basis has conflict_state set. A tension that IS resolved with clear supporting evidence does not by itself require low confidence.",
            "- A Company Brain item with conflict_state set is unresolved institutional context, not a settled company position - do not silently pick the current/latest memory value as authoritative; say the institutional context is internally conflicted on this point.",
            "- Degrade conservatively based on what is actually available this turn (see Reasoning Signals): Truth available + Company Brain unavailable -> give an evidence-based assessment and state that company-policy context is unavailable, do not guess company preference. Company Brain available + Truth unavailable -> do not produce a confident operational recommendation from policy alone. Neither available -> say so; do not fabricate either.",
            "- If RAG-retrieved excerpts conflict with Operational Truth Context or Company Brain Context, state that conflict/uncertainty explicitly where material - retrieved text never silently overrides either layer.",
            "- If the user asks for a specific desired conclusion (e.g. asks you to confirm an action is safe) that the Operational Truth Context does not support, state what the evidence actually supports instead. User phrasing or pressure never overrides evidence-grounded reasoning.",
        ]
    )
    return "\n".join(lines)


def _build_truth_context_section(items: Any) -> str:
    """Render the bounded M4 Slice 2 Operational Truth Context as a
    dedicated, concise text section (not raw JSON - each item is already a
    bounded Evidence.to_dict() payload from app/services/
    operational_truth_context.py, never the full internal OCE objects).

    Epistemic origin, entity scope, source time/status, and provenance
    warnings are always shown explicitly rather than flattened away, so a
    prompt reader can tell OBSERVED from DERIVED from INFERRED from
    unresolved/UNKNOWN, and can tell an unresolved source time from an
    authoritative one, at a glance. Each line is prefixed with its M6
    turn-local reference ID (T1, T2, ...) - the SAME numbering
    _build_reasoning_reference_catalog uses (both enumerate this identical
    list in this identical order), so recommendation_basis references can
    be validated against exactly what the model was actually shown.
    """
    if not isinstance(items, list) or not items:
        return ""

    lines = ["[Operational Truth Context]"]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        ref = f"T{index}"
        origin = item.get("epistemic_origin")
        origin_label = str(origin).upper() if origin else "UNKNOWN"
        claim = item.get("canonical_field") or item.get("type") or "unknown_claim"
        status = item.get("status") or "unknown"
        value = item.get("normalized_value")
        value_label = value if value is not None else "n/a"
        entity_type = item.get("entity_type")
        entity_reference = item.get("entity_reference")
        if entity_type and entity_reference:
            entity_label = f"{entity_type}:{entity_reference}"
        else:
            entity_label = entity_type or "unresolved"
        source_time = item.get("source_time")
        source_time_status = item.get("source_time_status") or "unknown"
        evidence_label = item.get("source_label") or item.get("description") or "n/a"
        source_file = item.get("source_file")

        line = (
            f"[{ref}] Claim: {claim} | Status: {status} | Origin: {origin_label} | "
            f"Entity: {entity_label} | Value: {value_label} | "
            f"Source time: {source_time or 'unresolved'} ({source_time_status}) | "
            f"Evidence: {evidence_label}"
        )
        if source_file:
            line += f" [{source_file}]"
        warnings = item.get("provenance_warnings")
        if warnings:
            line += f" | Warnings: {'; '.join(str(w) for w in warnings)}"
        lines.append(line)
    return "\n".join(lines)


def _build_company_brain_section(items: Any, semantics_topics: Any) -> str:
    """Render the bounded M5 Company Brain Context as its own dedicated
    text section - conceptually separate from [Operational Truth Context]
    (see app/services/company_brain_context.py). Each item states its
    Layer-2 type/statement/scope/authority/source/conflict status; nothing
    here is ever rendered as an OBSERVED/DERIVED operational claim. Each
    item is prefixed with its M6 turn-local reference ID (CB1, CB2, ...) -
    see _build_truth_context_section's docstring for the matching-order
    guarantee this relies on.

    Operational Semantics topics (terminology/meaning context) are listed
    separately at the end, explicitly labeled as such rather than folded
    into the policy/preference item list (Step 6).
    """
    has_items = isinstance(items, list) and items
    has_topics = isinstance(semantics_topics, list) and semantics_topics
    if not has_items and not has_topics:
        return ""

    lines = ["[Company Brain Context]"]
    if has_items:
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            ref = f"CB{index}"
            item_type = item.get("type") or "UNKNOWN"
            statement = item.get("statement") or "n/a"
            scope = item.get("scope") or "unresolved"
            authority = item.get("authority") or "unresolved"
            source = item.get("source") or "n/a"
            conflict_state = item.get("conflict_state")

            line = (
                f"[{ref}] Type: {item_type} | Statement: {statement} | Scope: {scope} | "
                f"Authority: {authority} | Source: {source}"
            )
            if conflict_state:
                provenance_note = item.get("provenance_note")
                line += f" | Conflict: {conflict_state}"
                if provenance_note:
                    line += f" ({provenance_note})"
            lines.append(line)

    if has_topics:
        lines.append(
            "- Operational Semantics topics (terminology/meaning context only, "
            "NOT policy/preference): " + ", ".join(str(topic) for topic in semantics_topics)
        )

    return "\n".join(lines)


def _build_reasoning_reference_catalog(
    *,
    operational_truth_context: list[dict[str, Any]],
    company_brain_context: list[dict[str, Any]],
) -> dict[str, Any]:
    """M6: bounded turn-local T#/CB# reference catalog for decision
    provenance validation (recommendation_basis).

    Enumerates operational_truth_context/company_brain_context in the exact
    same order _build_truth_context_section/_build_company_brain_section
    render them (T{i}/CB{i} = items[i-1]) - this is what lets the runtime
    validator confirm a model-cited reference actually exists and classify
    it (usable evidence / missing / inferred / unresolved-time for Truth;
    policy-type / conflicted / unresolved / settled for Company Brain).

    Turn-local only: never a database ID, never persisted, never reloads
    M4/M5 sources - purely a classification of the two lists already
    supplied as arguments.
    """
    truth_items = [item for item in operational_truth_context if isinstance(item, dict)]
    brain_items = [item for item in company_brain_context if isinstance(item, dict)]

    truth_refs: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(truth_items, start=1):
        status = item.get("status")
        origin = item.get("epistemic_origin")
        source_time_status = item.get("source_time_status")
        is_missing = status == "missing"
        # Row presence alone is never enough (M6-F2): only AVAILABLE +
        # OBSERVED/DERIVED counts as usable evidence. MISSING, INFERRED-only,
        # and any other/unknown status are all explicitly excluded.
        is_usable_evidence = status == "available" and origin in {"observed", "derived"}
        # "Unresolved source time" is a freshness-claim risk about USABLE
        # evidence specifically (the Feed Mill Golden Case: OBSERVED,
        # available, but freshness cannot be assumed) - it is not the same
        # concern as an INFERRED hypothesis merely lacking a timestamp,
        # which was never being asserted as current fact in the first
        # place (that is already captured separately by is_inferred). Gating
        # on is_usable_evidence keeps this signal tied to its actual
        # purpose: confidence/freshness-claim degradation for evidence that
        # could otherwise be mistaken for current.
        is_unresolved_time = is_usable_evidence and source_time_status == "unresolved"
        truth_refs[f"T{index}"] = {
            "status": status,
            "epistemic_origin": origin,
            "source_time_status": source_time_status,
            "is_missing": is_missing,
            "is_inferred": origin == "inferred",
            "is_unresolved_time": is_unresolved_time,
            "is_usable_evidence": is_usable_evidence,
            # Eligible for recommendation_basis.missing_evidence: a genuine
            # gap (missing) or usable evidence whose freshness cannot be
            # assumed (unresolved source time) - never an available,
            # resolved item, and never an unconfirmed hypothesis (an
            # INFERRED item is not "evidence" in the first place, so its
            # own timestamp state is not a missing-evidence gap).
            "is_gap_reference": is_missing or is_unresolved_time,
            # M7 Slice 2A-F4: the exact item that received THIS T# this
            # turn, captured here (not re-derived later by indexing into
            # operational_truth_context). This is what makes T# resolution
            # immune to the caller reordering/rebuilding that list after
            # catalog creation - the catalog entry itself is the only
            # authoritative source of "what T# means". Internal-only: a
            # shallow copy so later mutation of the source list's items
            # can't retroactively change what was cited; must NEVER be
            # placed in any public/serialized payload (see
            # INTERNAL_ONLY_DECISION_CONTEXT_KEYS and explainability.py,
            # which reads this field but only re-emits an explicit
            # sanitized allowlist from it).
            "internal_source_item": dict(item),
        }

    company_brain_refs: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(brain_items, start=1):
        item_type = item.get("type")
        conflict_state = item.get("conflict_state")
        authority = item.get("authority")
        is_policy_type = item_type in COMPANY_BRAIN_POLICY_TYPES
        is_conflicted = bool(conflict_state)
        is_unresolved = authority == "unresolved"
        # M6-R2: "authoritative" is an explicit allow-list value, never a
        # not-unresolved proxy. None/"unknown"/"institutional"/any other
        # authority value (including simply absent) must NOT be treated as
        # authoritative - only an item whose authority is EXACTLY the
        # string "authoritative" qualifies. This is deliberately strict:
        # a policy-like item with unrecognized authority metadata is
        # unproven, not innocent-until-proven-conflicted.
        is_authoritative = authority == "authoritative"
        # Row presence alone is never enough (M6-F2): INSTITUTIONAL_MEMORY,
        # a conflicted item, or anything not explicitly authoritative is
        # excluded from "settled" - never auto-picked as authoritative
        # company_basis (ENG-CONF stays frozen; this only READS
        # conflict_state/authority, never resolves them).
        is_settled = is_policy_type and is_authoritative and not is_conflicted
        company_brain_refs[f"CB{index}"] = {
            "type": item_type,
            "conflict_state": conflict_state,
            "authority": authority,
            "is_policy_type": is_policy_type,
            "is_conflicted": is_conflicted,
            "is_authoritative": is_authoritative,
            "is_unresolved": is_unresolved,
            "is_settled": is_settled,
            # M7 Slice 2A-F4: see the matching truth_refs comment above -
            # the exact item that received THIS CB# this turn, immune to
            # later reordering of company_brain_context. Internal-only.
            "internal_source_item": dict(item),
        }

    return {"truth": truth_refs, "company_brain": company_brain_refs}


def _build_reasoning_signals(reasoning_reference_catalog: dict[str, Any]) -> dict[str, Any]:
    """M6: bounded structural signals for the AI Reasoning Layer, derived
    from the reference catalog's per-item classification (never from mere
    row presence - M6-F2). Never inspects statement text, never matches
    domain-specific keywords (e.g. "poultry", "expansion"), and never
    decides whether a tension actually exists - only whether usable
    evidence / settled policy context exist this turn. The LLM performs
    the actual reasoning-state judgment, guided by the REASONING RULES in
    build_decision_context_prompt_block.
    """
    truth_refs = reasoning_reference_catalog.get("truth") or {}
    company_brain_refs = reasoning_reference_catalog.get("company_brain") or {}

    usable_truth_refs = [ref for ref, meta in truth_refs.items() if meta["is_usable_evidence"]]
    inferred_refs = [ref for ref, meta in truth_refs.items() if meta["is_inferred"]]
    missing_refs = [ref for ref, meta in truth_refs.items() if meta["is_missing"]]
    unresolved_time_refs = [ref for ref, meta in truth_refs.items() if meta["is_unresolved_time"]]

    settled_policy_refs = [ref for ref, meta in company_brain_refs.items() if meta["is_settled"]]
    conflicted_policy_refs = [ref for ref, meta in company_brain_refs.items() if meta["is_conflicted"]]

    truth_available = bool(usable_truth_refs)
    company_brain_policy_available = bool(settled_policy_refs)

    return {
        "allowed_reasoning_states": list(REASONING_STATES),
        "truth_context_item_count": len(truth_refs),
        "usable_truth_evidence_count": len(usable_truth_refs),
        "inferred_context_count": len(inferred_refs),
        "missing_evidence_count": len(missing_refs),
        "unresolved_source_time_count": len(unresolved_time_refs),
        "truth_available": truth_available,
        "company_brain_context_item_count": len(company_brain_refs),
        "settled_company_brain_policy_count": len(settled_policy_refs),
        "conflicted_company_brain_policy_count": len(conflicted_policy_refs),
        "company_brain_policy_available": company_brain_policy_available,
        "both_layers_present": truth_available and company_brain_policy_available,
    }


def _build_reasoning_signals_section(reasoning_signals: Any) -> str:
    """Render the M6 reasoning signals as their own dedicated text section,
    distinct from [Operational Truth Context] and [Company Brain Context] -
    a pointer to what materials are USABLE, never a verdict."""
    if not isinstance(reasoning_signals, dict) or not reasoning_signals:
        return ""

    return "\n".join(
        [
            "[Reasoning Signals]",
            f"- Truth Context items supplied: {reasoning_signals.get('truth_context_item_count', 0)} "
            f"(usable evidence: {reasoning_signals.get('usable_truth_evidence_count', 0)}, "
            f"inferred-only: {reasoning_signals.get('inferred_context_count', 0)})",
            f"- Usable Truth evidence available: {reasoning_signals.get('truth_available')}",
            f"- Company Brain items supplied: {reasoning_signals.get('company_brain_context_item_count', 0)} "
            f"(settled policy/preference: {reasoning_signals.get('settled_company_brain_policy_count', 0)}, "
            f"conflicted/unresolved: {reasoning_signals.get('conflicted_company_brain_policy_count', 0)})",
            f"- Settled Company Brain policy/preference available: {reasoning_signals.get('company_brain_policy_available')}",
            f"- Both layers present this turn: {reasoning_signals.get('both_layers_present')}",
            f"- Missing Truth evidence items: {reasoning_signals.get('missing_evidence_count', 0)}",
            f"- Truth items with unresolved source time: {reasoning_signals.get('unresolved_source_time_count', 0)}",
            f"- Allowed reasoning_state values: {', '.join(reasoning_signals.get('allowed_reasoning_states', []))}",
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
                    # M4 Slice 2 (Scenario F): preserve
                    # OperationalEventRepository.to_intelligence_event's
                    # conservative origin tag (e.g. "inferred" for a
                    # confirmed AI-drafted event) - previously computed but
                    # silently dropped here. None means unresolved/unknown,
                    # never fabricated as "observed".
                    "origin": context.get("origin"),
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
