from app.services.organizational_intelligence import (
    build_organizational_intelligence,
    build_organizational_intelligence_prompt_block,
)


def test_jannat_template_models_company_as_connected_organization():
    org = build_organizational_intelligence(
        company_profile={
            "company_name": "Jannat Al-Firdaws",
            "industry": "Poultry and beverage operations",
            "country_market": "Jordan",
        },
        snapshot=None,
    )

    division_names = {division["name"] for division in org["divisions"]}
    assert {"Dairtna Poultry", "Caesar Beverage", "Shared Corporate Departments"} <= division_names
    assert org["native_operational_mode"]["enabled"] is True
    assert any(
        relationship["source_department_key"] == "sales"
        and relationship["target_department_key"] == "production"
        for relationship in org["department_relationships"]
    )
    assert any(item["kpi_key"] == "attendance_coverage" for item in org["kpi_ownership"])
    assert any(source["provider_type"] == "erp" for source in org["integration_sources"])


def test_organizational_prompt_preserves_company_brain_behavior():
    org = build_organizational_intelligence(
        company_profile={"company_name": "Dairtna Poultry"},
        snapshot=None,
    )
    block = build_organizational_intelligence_prompt_block(org)

    assert "ORGANIZATIONAL INTELLIGENCE LAYER" in block
    assert "ERP is only one data source" in block
    assert "Native Operational Mode" in block
    assert "HR signals such as attendance" in block
    assert "SOPs, PPT outlines, avatar briefing scripts" in block
    assert "Dairtna Poultry" in block
