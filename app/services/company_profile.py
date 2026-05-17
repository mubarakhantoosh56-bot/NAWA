"""Company Intelligence Profile helpers for NAWA MVP."""

from typing import Any


PROFILE_FIELDS = (
    "company_name",
    "industry",
    "business_type",
    "country_market",
    "company_size",
    "departments_enabled",
    "primary_goals",
    "current_operational_challenges",
    "growth_priorities",
    "preferred_response_language",
)


def normalize_company_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    """Return a stable, trimmed Company Intelligence Profile payload."""
    source = profile or {}
    language = str(source.get("preferred_response_language") or "en").strip().lower()
    if language not in {"en", "ar"}:
        language = "en"

    departments = source.get("departments_enabled") or []
    if not isinstance(departments, list):
        departments = []

    normalized = {
        "company_name": _clean_text(source.get("company_name")),
        "industry": _clean_text(source.get("industry")),
        "business_type": _clean_text(source.get("business_type")),
        "country_market": _clean_text(source.get("country_market")),
        "company_size": _clean_text(source.get("company_size")),
        "departments_enabled": [
            _clean_text(item)
            for item in departments
            if _clean_text(item)
        ],
        "primary_goals": _clean_text(source.get("primary_goals"), max_chars=1200),
        "current_operational_challenges": _clean_text(
            source.get("current_operational_challenges"),
            max_chars=1200,
        ),
        "growth_priorities": _clean_text(source.get("growth_priorities"), max_chars=1200),
        "preferred_response_language": language,
    }
    normalized["is_active"] = is_company_profile_active(normalized)
    return normalized


def is_company_profile_active(profile: dict[str, Any] | None) -> bool:
    """Return whether the profile has enough content to influence AI behavior."""
    if not profile:
        return False
    for key in PROFILE_FIELDS:
        value = profile.get(key)
        if key == "preferred_response_language":
            continue
        if isinstance(value, list) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
    return False


def build_company_profile_prompt_block(profile: dict[str, Any] | None) -> str:
    """Build a compact prompt block from the persistent Company Intelligence Profile."""
    normalized = normalize_company_profile(profile)
    if not normalized["is_active"]:
        return ""

    labels = {
        "company_name": "Company name",
        "industry": "Industry",
        "business_type": "Business type",
        "country_market": "Country / market",
        "company_size": "Company size",
        "departments_enabled": "Departments enabled",
        "primary_goals": "Primary goals",
        "current_operational_challenges": "Current operational challenges",
        "growth_priorities": "Growth priorities",
        "preferred_response_language": "Preferred response language",
    }

    lines = ["COMPANY INTELLIGENCE PROFILE (PERSISTENT CONTEXT):"]
    for key in PROFILE_FIELDS:
        value = normalized.get(key)
        if isinstance(value, list):
            if value:
                lines.append(f"- {labels[key]}: {', '.join(value)}")
        elif value:
            lines.append(f"- {labels[key]}: {value}")

    lines.extend(
        [
            "RULES:",
            "- Treat this profile as stable company context for all responses.",
            "- Make recommendations specific to the company's industry, model, market, operating structure, goals, challenges, and growth priorities.",
            "- If the profile indicates distribution, logistics, branches, fulfillment, or inventory, reflect those operating realities in risks and actions.",
            "- If the profile indicates SaaS, reflect CAC, retention, onboarding, pipeline, MRR, churn, activation, and customer success where relevant.",
            "- Do not invent metrics not present in the profile, memory, retrieved files, or user request.",
        ]
    )
    return "\n".join(lines)


def _clean_text(value: Any, max_chars: int = 240) -> str:
    cleaned = " ".join(str(value or "").split())
    return cleaned[:max_chars].strip()
