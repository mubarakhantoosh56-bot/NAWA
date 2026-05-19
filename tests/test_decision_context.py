import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services.decision_context import build_decision_context, build_decision_context_prompt_block
from app.services.openai_client import AIService


VALID_AI_JSON = """
{
  "executive_summary": "Executive Summary\\n- Production delay is creating fulfillment risk.\\n\\nKey Insights\\n- Inventory and distribution must be aligned before Sales commits more orders.\\n\\nRisks\\n- Wastage and service misses can pressure margin.\\n\\nRecommended Actions\\n- Operations: confirm stock, delivery capacity, and margin impact within 48 hours.\\n\\nPriority Level\\n- High.",
  "raw_decision": {
    "truth_validation": {
      "contradictions": []
    }
  }
}
"""


class _FakeChatCompletions:
    def __init__(self):
        self.messages = []

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=VALID_AI_JSON))]
        )


class _FakeOpenAIClient:
    def __init__(self):
        self.chat_completions = _FakeChatCompletions()
        self.chat = SimpleNamespace(completions=self.chat_completions)


def _service_with_fake_client() -> tuple[AIService, _FakeOpenAIClient]:
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = False
    service.db_pool = None
    service.repo = None
    return service, fake_client


def test_decision_context_builds_ceo_fmcg_operating_lens():
    decision_context = build_decision_context(
        context={
            "company_intelligence_profile": {
                "company_name": "Mesopotamia Foods",
                "industry": "FMCG food distribution",
                "departments_enabled": ["CEO", "Sales", "Finance", "Production"],
                "current_operational_challenges": "Inventory accuracy and delayed fulfillment.",
                "growth_priorities": "Improve branch service level.",
            }
        },
        response_language="en",
        memory_events=[
            {
                "user_message": "Review wastage issue",
                "executive_summary": "Wastage increased after late production handoff.",
            }
        ],
        memory_facts=[{"fact_key": "service_level", "fact_value": "below target"}],
    )

    assert decision_context["department"]["key"] == "ceo"
    assert "service level/OTIF" in " ".join(decision_context["key_kpis"])
    assert "production" in " ".join(decision_context["related_departments"]).lower()
    assert "Wastage increased" in decision_context["memory_events"][0]
    assert "Memory signal: service_level = below target" in decision_context["trends"]
    assert "detected_patterns" in decision_context
    assert decision_context["response_enforcement"]["generation_hierarchy"][0] == "root_cause_reasoning"


def test_decision_context_covers_production_sales_finance_relationships():
    for department_type, expected in [
        ("production_ai", "Sales: depends on realistic production commitments"),
        ("sales_ai", "Inventory/Warehouse: stock availability determines"),
        ("finance_ai", "Production: wastage, overtime"),
    ]:
        decision_context = build_decision_context(
            context={"aimx_department": {"department_type": department_type}},
            response_language="en",
        )

        assert any(expected in item for item in decision_context["related_departments"])
        assert decision_context["impact_assessment"]
        assert decision_context["operational_risks"]


def test_decision_context_prompt_rules_force_decisive_operational_reasoning():
    block = build_decision_context_prompt_block(
        build_decision_context(context={"aimx_department": {"department_type": "sales_ai"}}, response_language="en")
    )

    assert "DECISION CONTEXT ENGINE" in block
    assert "likely root cause" in block
    assert "production, inventory/warehouse, sales, distribution/operations, and finance" in block
    assert "detected_patterns" in block
    assert "MANDATORY OPERATIONAL RESPONSE ENFORCEMENT" in block
    assert "root_cause_reasoning, detected_patterns, operational_events" in block
    assert "concise, executive, structured, decisive" in block


def test_chat_injects_decision_context_without_changing_response_contract(monkeypatch):
    service, fake_client = _service_with_fake_client()
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="decision-context-session",
            message="What should Sales do about delayed fulfillment?",
            context={
                "response_language": "en",
                "aimx_department": {
                    "id": str(uuid4()),
                    "name": "Sales",
                    "department_type": "sales_ai",
                },
                "company_intelligence_profile": {
                    "company_name": "Mesopotamia Foods",
                    "industry": "FMCG food distribution",
                    "current_operational_challenges": "Stock-outs and delayed fulfillment.",
                },
            },
            company_id=str(uuid4()),
        )
    )

    prompt_text = "\n".join(message["content"] for message in fake_client.chat_completions.messages[0])
    assert "DECISION CONTEXT ENGINE (MVP - INTERNAL)" in prompt_text
    assert "Inventory/Warehouse: stock availability determines what Sales can commit" in prompt_text
    assert "FMCG risk" in prompt_text
    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}
    assert result["meta"]["context"]["decision_context"]["department"]["key"] == "sales"
