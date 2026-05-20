"""Organizational Intelligence Layer for NAWA enterprise reasoning."""

from __future__ import annotations

from typing import Any


JANNAAT_ORG_TEMPLATE: dict[str, Any] = {
    "company": {
        "name": "Jannat Al-Firdaws",
        "operating_model": "multi-division enterprise",
        "native_operational_mode": True,
        "philosophy": "ERP is one source; NAWA is the company brain across people, work, KPIs, and dependencies.",
    },
    "divisions": [
        {
            "name": "Dairtna Poultry",
            "division_type": "business_unit",
            "focus": "poultry production, feed, halls, flock health, warehouse, sales, and logistics execution",
        },
        {
            "name": "Caesar Beverage",
            "division_type": "business_unit",
            "focus": "beverage production, sales, distribution, inventory, and trade execution",
        },
        {
            "name": "Shared Corporate Departments",
            "division_type": "shared_services",
            "focus": "finance, HR, procurement, accounting, leadership, reporting, and governance",
        },
    ],
    "department_relationships": [
        {
            "source_department_key": "sales",
            "target_department_key": "production",
            "relationship_type": "capacity_dependency",
            "description": "Sales commitments depend on production capacity, finished goods availability, and reliable production timing.",
            "risk_if_broken": "Overpromising, lost sales, customer disputes, and service-level failure.",
        },
        {
            "source_department_key": "sales",
            "target_department_key": "warehouse",
            "relationship_type": "availability_dependency",
            "description": "Sales depends on warehouse stock accuracy and release readiness before promising customer delivery.",
            "risk_if_broken": "False availability, delayed fulfillment, returns, and customer trust erosion.",
        },
        {
            "source_department_key": "sales",
            "target_department_key": "logistics",
            "relationship_type": "fulfillment_dependency",
            "description": "Sales depends on logistics route capacity and dispatch timing to convert orders into delivered revenue.",
            "risk_if_broken": "Booked orders become failed deliveries and collection delays.",
        },
        {
            "source_department_key": "production",
            "target_department_key": "procurement",
            "relationship_type": "material_dependency",
            "description": "Production depends on procurement for feed, raw materials, packaging, spare parts, and vendor reliability.",
            "risk_if_broken": "Line stoppage, feed shortage, lower output, and emergency purchasing cost.",
        },
        {
            "source_department_key": "production",
            "target_department_key": "inventory",
            "relationship_type": "stock_dependency",
            "description": "Production depends on inventory accuracy for feed levels, consumables, vaccines, and finished goods handoff.",
            "risk_if_broken": "Shortage surprises, excess stock, spoilage, and unplanned downtime.",
        },
        {
            "source_department_key": "production",
            "target_department_key": "hr",
            "relationship_type": "staffing_dependency",
            "description": "Production execution depends on staffing, attendance, shifts, leave planning, and role coverage.",
            "risk_if_broken": "Understaffed halls, weak supervision, overtime pressure, and lower productivity.",
        },
        {
            "source_department_key": "procurement",
            "target_department_key": "finance",
            "relationship_type": "approval_dependency",
            "description": "Procurement depends on finance for budget guardrails, supplier payment readiness, and scaling decisions.",
            "risk_if_broken": "Delayed replenishment, supplier friction, cash pressure, and blocked growth.",
        },
        {
            "source_department_key": "operations",
            "target_department_key": "hr",
            "relationship_type": "execution_dependency",
            "description": "HR attendance, absence, leave, and performance signals directly affect operational execution quality.",
            "risk_if_broken": "Plans look correct on paper but fail through missing people, weak shifts, or unclear ownership.",
        },
    ],
    "kpi_ownership": [
        {"kpi_key": "production_output", "owner": "production", "related": ["warehouse", "sales", "finance"]},
        {"kpi_key": "feed_consumption", "owner": "production", "related": ["procurement", "inventory", "finance"]},
        {"kpi_key": "mortality_rate", "owner": "production", "related": ["veterinary", "quality", "hr"]},
        {"kpi_key": "stock_accuracy", "owner": "warehouse", "related": ["sales", "production", "finance"]},
        {"kpi_key": "attendance_coverage", "owner": "hr", "related": ["production", "warehouse", "logistics"]},
        {"kpi_key": "cash_availability", "owner": "finance", "related": ["procurement", "sales", "production"]},
    ],
    "integration_sources": [
        {"provider_type": "erp", "source_system": "ERP systems", "status": "planned", "native_fallback_enabled": True},
        {"provider_type": "hr", "source_system": "HR systems", "status": "planned", "native_fallback_enabled": True},
        {"provider_type": "accounting", "source_system": "Accounting systems", "status": "planned", "native_fallback_enabled": True},
        {"provider_type": "attendance", "source_system": "Attendance systems", "status": "planned", "native_fallback_enabled": True},
        {"provider_type": "sales", "source_system": "Sales systems", "status": "planned", "native_fallback_enabled": True},
        {"provider_type": "warehouse", "source_system": "Warehouse systems", "status": "planned", "native_fallback_enabled": True},
    ],
    "native_operational_mode": {
        "enabled": True,
        "description": "When no ERP is connected, NAWA uses chat, forms, files, automations, and integrations-ready raw inputs as operational truth candidates.",
    },
}


def build_organizational_intelligence(
    *,
    company_profile: dict[str, Any] | None,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge persisted org facts with the first-enterprise Jannat template."""
    snapshot = snapshot or {}
    profile = company_profile or {}
    company_name = str(profile.get("company_name") or "").strip()
    use_jannat_template = _looks_like_jannat(company_name) or not snapshot.get("divisions")
    base = JANNAAT_ORG_TEMPLATE if use_jannat_template else {"company": {"name": company_name}}

    divisions = snapshot.get("divisions") or base.get("divisions") or []
    relationships = snapshot.get("department_relationships") or base.get("department_relationships") or []
    kpi_ownership = snapshot.get("kpi_ownerships") or base.get("kpi_ownership") or []
    integrations = snapshot.get("integration_sources") or base.get("integration_sources") or []

    native_mode = base.get("native_operational_mode") or {}
    if isinstance(native_mode, dict):
        native_enabled = bool(native_mode.get("enabled", True))
    else:
        native_enabled = True

    return {
        "company": {
            **(base.get("company") or {}),
            "profile_name": company_name,
            "industry": profile.get("industry") or "",
            "country_market": profile.get("country_market") or "",
        },
        "divisions": _compact_items(divisions, 8),
        "operational_units": _compact_items(snapshot.get("operational_units") or [], 12),
        "department_relationships": _compact_items(relationships, 12),
        "operational_workflows": _compact_items(snapshot.get("operational_workflows") or [], 10),
        "kpi_ownership": _compact_items(kpi_ownership, 12),
        "integration_sources": _compact_items(integrations, 10),
        "current_user_profile": snapshot.get("current_user_profile"),
        "native_operational_mode": {
            "enabled": native_enabled,
            "input_sources": ["chat", "forms", "files", "integrations", "automations"],
            "rule": "If no ERP is connected, use NAWA native operational inputs while preserving source confidence.",
        },
        "capabilities_to_preserve": [
            "conversational questions",
            "analysis and reports",
            "SOP generation",
            "PPT/storyline generation",
            "avatar briefing prompts",
            "automation triggers",
        ],
    }


def build_organizational_intelligence_prompt_block(org: dict[str, Any] | None) -> str:
    """Build a compact prompt block that frames NAWA as the company brain."""
    if not org:
        return ""

    lines = ["ORGANIZATIONAL INTELLIGENCE LAYER (COMPANY BRAIN):"]
    company = org.get("company") if isinstance(org.get("company"), dict) else {}
    if company:
        lines.append(f"- Company: {company.get('profile_name') or company.get('name') or 'Unknown'}")
        if company.get("industry"):
            lines.append(f"- Industry: {company['industry']}")

    lines.append("- Operating principle: ERP is only one data source; departments, users, workflows, HR, files, chat, and automations are also operational signals.")
    lines.append("- Native Operational Mode: enabled when ERP is absent; use NAWA raw inputs, drafts, events, and memory as lightweight operating evidence.")

    for label, key in [
        ("Divisions", "divisions"),
        ("Department dependencies", "department_relationships"),
        ("KPI ownership", "kpi_ownership"),
        ("Integration sources", "integration_sources"),
    ]:
        items = org.get(key) if isinstance(org.get(key), list) else []
        if not items:
            continue
        lines.append(f"{label}:")
        for item in items[:8]:
            lines.append(f"- {_item_summary(item)}")

    lines.extend(
        [
            "RULES:",
            "- Reason about the organization as connected people, departments, workflows, KPIs, and dependencies.",
            "- When analyzing Dairtna Poultry, connect halls/feed/production/mortality/warehouse/sales/logistics/HR/finance before recommending action.",
            "- HR signals such as attendance, leave, shifts, performance notes, and productivity affect execution reliability.",
            "- For every operational issue, identify affected departments, KPI owners, workflow dependency, user/team impact, and likely business consequence.",
            "- Preserve conversational AI behavior: answer questions, create reports, SOPs, PPT outlines, avatar briefing scripts, and automation-ready actions.",
            "- Do not present NAWA as ERP-first. Present it as live organizational awareness and company brain.",
        ]
    )
    return "\n".join(lines)


def _looks_like_jannat(company_name: str) -> bool:
    lowered = company_name.lower()
    return any(token in lowered for token in ("jannat", "firdaws", "dairtna", "dairitna", "dairetna"))


def _compact_items(items: list[Any], limit: int) -> list[Any]:
    compact: list[Any] = []
    for item in items[:limit]:
        compact.append(item)
    return compact


def _item_summary(item: Any) -> str:
    if not isinstance(item, dict):
        return str(item)
    if item.get("description"):
        lead = item.get("name") or item.get("source_department_key") or item.get("kpi_label") or item.get("source_system") or "item"
        return f"{lead}: {item['description']}"
    if item.get("source_department_key") and item.get("target_department_key"):
        return f"{item['source_department_key']} depends on {item['target_department_key']} ({item.get('relationship_type', 'dependency')})"
    if item.get("kpi_key"):
        return f"{item.get('kpi_label') or item['kpi_key']} owner={item.get('owner') or item.get('ownership_type') or 'unknown'}"
    if item.get("source_system"):
        return f"{item['source_system']} ({item.get('provider_type', 'system')}, {item.get('status', 'planned')})"
    if item.get("name"):
        return f"{item['name']} ({item.get('division_type') or item.get('unit_type') or 'unit'})"
    return ", ".join(f"{key}={value}" for key, value in list(item.items())[:3])
