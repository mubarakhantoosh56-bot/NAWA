import asyncio
from uuid import uuid4

from app.core.role_permissions import OPERATIONAL_ROLE_TEMPLATES, visible_department_types
from app.services.decision_context import build_decision_context
from app.services.integrations.providers import ProviderRegistry
from app.services.operational_input_service import OperationalInputService


class _FakeAcquire:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeDb:
    def __init__(self):
        self.executed = []

    def acquire(self):
        return _FakeAcquire(self)

    async def execute(self, query, *args):
        self.executed.append((query, args))
        return "INSERT 0 1"


def test_operational_role_templates_cover_mvp_users():
    assert set(OPERATIONAL_ROLE_TEMPLATES) == {
        "ceo",
        "production_manager",
        "sales_manager",
        "finance_manager",
        "marketing_manager",
        "employee",
    }
    assert "workspace.ceo" in OPERATIONAL_ROLE_TEMPLATES["ceo"]["permissions"]
    assert "agents.production_ai.use" in OPERATIONAL_ROLE_TEMPLATES["production_manager"]["permissions"]
    assert "operational.forms.submit" in OPERATIONAL_ROLE_TEMPLATES["sales_manager"]["permissions"]


def test_visible_department_types_restrict_manager_workspaces():
    visible = visible_department_types(["departments.read", "agents.sales_ai.use"])

    assert visible == {"sales_ai"}
    assert visible_department_types(["*"]) is None
    assert visible_department_types(["workspace.ceo"]) is None


def test_operational_input_submission_creates_memory_event():
    db = _FakeDb()
    service = OperationalInputService(db)
    department_id = uuid4()

    result = asyncio.run(
        service.submit_input(
            company_id=uuid4(),
            user_id=uuid4(),
            source_role="production_manager",
            source_department_id=department_id,
            source_department_type="production_ai",
            target_department_id=None,
            target_department_type=None,
            category="issue",
            priority="high",
            event_date="2026-05-19",
            text="Packaging line stopped twice.",
            metrics={
                "downtime": "45 minutes",
                "wastage": "2.1%",
            },
            files_attached=[{"id": "file-1", "filename": "line-report.pdf"}],
            payload={"shift": "morning"},
        )
    )

    assert result["memory_event_created"] is True
    assert result["event_type"] == "operational.production.issue"
    assert "Production issue" in result["summary"]
    assert result["category"] == "issue"
    assert result["priority"] == "high"

    args = db.executed[0][1]
    assert args[2] == "operational.production.issue"
    assert "Packaging line stopped twice" in args[4]
    assert "production_manager" in args[6]
    assert "line-report.pdf" in args[6]


def test_decision_context_uses_operational_events():
    decision_context = build_decision_context(
        context={
            "aimx_department": {"department_type": "finance_ai"},
            "nawa_role": {"slug": "finance_manager"},
        },
        response_language="en",
        memory_events=[
            {
                "event_type": "operational.sales.daily_input",
                "executive_summary": "Sales daily input (watch): collections delayed by 3 key accounts.",
                "context": {
                    "source_role": "sales_manager",
                    "source_department": "sales",
                    "target_department": "finance",
                    "category": "kpi",
                    "priority": "watch",
                },
            }
        ],
    )

    assert decision_context["role_perspective"] == {
        "slug": "finance_manager",
        "scope": "department_scoped",
    }
    assert decision_context["operational_events"] == [
        {
            "event_type": "operational.sales.daily_input",
            "summary": "Sales daily input (watch): collections delayed by 3 key accounts.",
            "source_role": "sales_manager",
            "source_department": "sales",
            "target_department": "finance",
            "category": "kpi",
            "priority": "watch",
            # M4 Slice 2: epistemic origin preserved from context["origin"];
            # this event's context sets none, so it stays unresolved (None).
            "origin": None,
        }
    ]


def test_provider_registry_exposes_future_erp_foundation():
    registry = ProviderRegistry()
    providers = {provider["key"]: provider for provider in registry.list_providers()}

    assert set(providers) == {"sap", "odoo", "erpnext", "zoho", "oracle"}
    assert providers["sap"]["status"] == "planned"
