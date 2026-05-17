from app.services.company_profile import (
    build_company_profile_prompt_block,
    is_company_profile_active,
    normalize_company_profile,
)


def test_company_profile_normalization_and_activity():
    profile = normalize_company_profile(
        {
            "company_name": "  Mesopotamia Foods  ",
            "industry": "Food distribution",
            "business_type": "B2B",
            "country_market": "Iraq",
            "departments_enabled": ["CEO", "Operations", ""],
            "preferred_response_language": "ar",
        }
    )

    assert profile["company_name"] == "Mesopotamia Foods"
    assert profile["departments_enabled"] == ["CEO", "Operations"]
    assert profile["preferred_response_language"] == "ar"
    assert profile["is_active"] is True
    assert is_company_profile_active(profile) is True


def test_company_profile_prompt_block_guides_industry_specific_responses():
    block = build_company_profile_prompt_block(
        {
            "company_name": "Mesopotamia Foods",
            "industry": "Food distribution",
            "business_type": "B2B",
            "country_market": "Iraq",
            "company_size": "120 employees across branches and warehouses",
            "departments_enabled": ["CEO", "Sales", "Operations"],
            "primary_goals": "Improve branch fulfillment reliability.",
            "current_operational_challenges": "Inventory accuracy and last-mile delivery capacity.",
            "growth_priorities": "Expand into two new city branches.",
            "preferred_response_language": "en",
        }
    )

    assert "COMPANY INTELLIGENCE PROFILE" in block
    assert "Food distribution" in block
    assert "Iraq" in block
    assert "logistics, branches, fulfillment, or inventory" in block
    assert "SaaS" in block


def test_empty_company_profile_does_not_create_prompt_block():
    profile = normalize_company_profile({})

    assert profile["is_active"] is False
    assert build_company_profile_prompt_block(profile) == ""
