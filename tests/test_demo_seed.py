from pathlib import Path

from scripts import seed_demo


def test_demo_departments_are_curated():
    departments = {department.slug: department for department in seed_demo.DEMO_DEPARTMENTS}

    assert set(departments) == {"ceo", "production", "sales", "finance", "marketing", "operations"}
    assert departments["production"].department_type == "production_ai"
    assert departments["sales"].department_type == "sales_ai"
    assert departments["finance"].department_type == "finance_ai"
    assert departments["marketing"].department_type == "marketing_ai"
    assert departments["operations"].department_type == "operations_ai"


def test_demo_files_exist_and_support_keyword_retrieval():
    filenames = set(seed_demo.COMPANY_FILES)
    filenames.update(
        department.filename
        for department in seed_demo.DEMO_DEPARTMENTS
        if department.filename is not None
    )

    assert filenames == {
        "company_profile.md",
        "growth_goals.md",
        "executive_operating_brief_q2.md",
        "board_demo_flow.md",
        "sales_playbook.md",
        "finance_budget.md",
        "marketing_campaign.md",
        "operations_sop.md",
    }

    for filename in filenames:
        path = seed_demo.DEMO_FILES_DIR / filename
        assert path.exists()
        text = path.read_text(encoding="utf-8").lower()
        assert any(
            keyword in text
            for keyword in (
                "northstar",
                "enterprise",
                "sales",
                "finance",
                "marketing",
                "operations",
            )
        )


def test_demo_seed_requires_password(monkeypatch):
    monkeypatch.delenv("DEMO_OWNER_PASSWORD", raising=False)
    assert seed_demo.DEMO_OWNER_EMAIL == "owner@northstar-demo.local"


def test_demo_department_users_are_seeded():
    users = {user.role_slug: user for user in seed_demo.DEMO_USERS}

    assert set(users) == {
        "ceo",
        "production_manager",
        "sales_manager",
        "finance_manager",
        "marketing_manager",
        "employee",
    }
    assert users["production_manager"].department_slug == "production"


def test_demo_run_instructions_exist():
    readme = Path("demo/atlas_home_supplies/README.md")
    prompts = Path("demo/atlas_home_supplies/sample_prompts.md")

    assert readme.exists()
    assert prompts.exists()
    assert "python -m scripts.seed_demo" in readme.read_text(encoding="utf-8")
    assert "CEO AI" in prompts.read_text(encoding="utf-8")
