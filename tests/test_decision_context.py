import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.services.decision_context import build_decision_context, build_decision_context_prompt_block
from app.services.decision_debug import list_decision_debug_snapshots
from app.services.openai_client import AIService


_REASONING_ASSESSMENT_JSON = """"reasoning_assessment": {
      "reasoning_state": "insufficient_evidence",
      "operational_assessment": "n/a",
      "company_brain_alignment": "cannot determine",
      "tensions": [],
      "evidence_gaps": [],
      "risk_assessment": "n/a",
      "confidence": 50,
      "recommendation_basis": {"evidence_basis": [], "company_basis": [], "missing_evidence": []}
    }"""

VALID_AI_JSON = (
    """
{
  "executive_summary": "Executive Summary\\n- Production delay is creating fulfillment risk.\\n\\nKey Insights\\n- Inventory and distribution must be aligned before Sales commits more orders.\\n\\nRisks\\n- Wastage and service misses can pressure margin.\\n\\nRecommended Actions\\n- Operations: confirm stock, delivery capacity, and margin impact within 48 hours.\\n\\nPriority Level\\n- High.",
  "raw_decision": {
    "truth_validation": {
      "contradictions": []
    },
    """
    + _REASONING_ASSESSMENT_JSON
    + """
  }
}
"""
)

GENERIC_AI_JSON = (
    """
{
  "executive_summary": "Executive Summary\\n- There are challenges and performance should improve.\\n\\nRecommended Actions\\n- Focus on efficiency.\\n\\nPriority Level\\n- High.",
  "raw_decision": {
    "truth_validation": {
      "contradictions": []
    },
    """
    + _REASONING_ASSESSMENT_JSON
    + """
  }
}
"""
)

OPERATIONAL_AI_JSON = (
    """
{
  "executive_summary": "Executive Summary\\n- Root operational bottleneck: production capacity is constraining Baghdad orange fulfillment after demand rose while line speed slowed.\\n- Cause/effect chain: higher Sales orders plus slower Production output creates Distribution backlog and Finance margin pressure from overtime and delayed collections.\\n- Affected departments: Production, Sales, Distribution/Ops, and Finance.\\n- Operational impact: fulfillment windows and OTIF are at risk for orange orders.\\n- Business impact: overtime cost and weak collections pressure margin and cash.\\n\\nRecommended Actions\\n- CEO: freeze new orange commitments for 48 hours until Production confirms line recovery, Distribution resequences priority routes, and Finance clears collection exposure.\\n\\nPriority Level\\n- Critical.",
  "raw_decision": {
    "truth_validation": {
      "contradictions": []
    },
    """
    + _REASONING_ASSESSMENT_JSON
    + """
  }
}
"""
)


class _FakeRepo:
    async def fetch_recent_events(self, **kwargs):
        return [
            {
                "event_type": "operational.update",
                "user_message": "Baghdad orange orders are 22% above forecast.",
                "executive_summary": "Sales KPI direction: Baghdad orange demand up 22% and order intake above forecast.",
                "context": {"source_department": "sales", "category": "kpi", "priority": "high"},
            },
            {
                "event_type": "operational.update",
                "user_message": "Orange line speed is down 14% and overtime was added after downtime.",
                "executive_summary": "Production KPI direction: orange line speed down 14%, with overtime added after downtime.",
                "context": {"source_department": "production", "category": "issue", "priority": "high"},
            },
            {
                "event_type": "operational.update",
                "user_message": "Two distributors delayed collections while overtime cost increased.",
                "executive_summary": "Finance event: delayed collections from two distributors while overtime cost increased.",
                "context": {"source_department": "finance", "category": "issue", "priority": "high"},
            },
        ]

    async def fetch_facts(self, **kwargs):
        return [{"fact_key": "orange_demand", "fact_value": "up 22% in Baghdad"}]

    async def build_company_profile(self, **kwargs):
        return {"industry": "FMCG juice distribution", "country_market": "Baghdad"}

    async def insert_event(self, *args, **kwargs):
        return {}

    async def upsert_fact(self, **kwargs):
        return {}


class _FakeChatCompletions:
    def __init__(self, responses=None):
        self.messages = []
        self.responses = list(responses or [VALID_AI_JSON])

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        response_text = self.responses.pop(0) if self.responses else VALID_AI_JSON
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response_text))]
        )


class _FakeOpenAIClient:
    def __init__(self, responses=None):
        self.chat_completions = _FakeChatCompletions(responses)
        self.chat = SimpleNamespace(completions=self.chat_completions)


def _service_with_fake_client(responses=None) -> tuple[AIService, _FakeOpenAIClient]:
    service = AIService()
    fake_client = _FakeOpenAIClient(responses)
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


def test_decision_debug_captures_prompt_context_and_raw_response(monkeypatch):
    service, fake_client = _service_with_fake_client()
    service.db_enabled = True
    service.repo = _FakeRepo()
    company_id = str(uuid4())
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)
    monkeypatch.setattr("app.services.decision_debug.decision_debug_enabled", lambda: True)

    async def skip_fact_extraction(**kwargs):
        return None

    monkeypatch.setattr(service, "_extract_and_upsert_facts", skip_fact_extraction)

    result = asyncio.run(
        service.chat(
            session_id="baghdad-orange-debug",
            message="Give me the CEO operational view for Baghdad orange demand.",
            context={
                "response_language": "en",
                "company_intelligence_profile": {
                    "company_name": "Baghdad Juices",
                    "industry": "FMCG juice distribution",
                    "country_market": "Baghdad",
                },
            },
            company_id=company_id,
        )
    )

    snapshots = list_decision_debug_snapshots(company_id=company_id, session_id="baghdad-orange-debug")
    assert snapshots
    snapshot = snapshots[0]
    assert snapshot["decision_context"]["root_cause_reasoning"]["likely_operational_bottleneck"]
    assert "detected_patterns" in snapshot["decision_context"]
    assert "operational_events" in snapshot["decision_context"]
    assert "response_enforcement" in snapshot["decision_context"]
    assert "root_cause_reasoning" in snapshot["final_prompt"]
    assert "MANDATORY OPERATIONAL RESPONSE ENFORCEMENT" in snapshot["final_prompt"]
    assert snapshot["prompt_diagnostics"]["root_cause_reasoning_present"] is True
    assert snapshot["prompt_diagnostics"]["root_cause_before_formatting"] is True
    assert snapshot["prompt_diagnostics"]["likely_truncated"] is False
    assert snapshot["raw_model_response"] == VALID_AI_JSON
    assert result["meta"]["context"]["decision_context"]["department"]["key"] == "ceo"


def test_generic_ceo_response_regenerates_with_stricter_operational_instruction(monkeypatch):
    service, fake_client = _service_with_fake_client([GENERIC_AI_JSON, OPERATIONAL_AI_JSON])
    service.db_enabled = True
    service.repo = _FakeRepo()
    company_id = str(uuid4())
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)
    monkeypatch.setattr("app.services.decision_debug.decision_debug_enabled", lambda: True)

    async def skip_fact_extraction(**kwargs):
        return None

    monkeypatch.setattr(service, "_extract_and_upsert_facts", skip_fact_extraction)

    result = asyncio.run(
        service.chat(
            session_id="baghdad-orange-regenerate",
            message="CEO summary for Baghdad orange demand.",
            context={
                "response_language": "en",
                "company_intelligence_profile": {
                    "company_name": "Baghdad Juices",
                    "industry": "FMCG juice distribution",
                    "country_market": "Baghdad",
                },
            },
            company_id=company_id,
        )
    )

    assert len(fake_client.chat_completions.messages) == 2
    retry_prompt = "\n".join(message["content"] for message in fake_client.chat_completions.messages[1])
    assert "failed NAWA operational-response enforcement" in retry_prompt
    assert "root_cause_reasoning, detected_patterns, operational_events" in retry_prompt
    assert "Root operational bottleneck: production capacity" in result["ceo_text"]
    assert "Affected departments: Production, Sales, Distribution/Ops, and Finance" in result["ceo_text"]
    assert "fulfillment windows and OTIF are at risk" in result["ceo_text"]
    assert "overtime cost and weak collections pressure margin and cash" in result["ceo_text"]

    snapshots = list_decision_debug_snapshots(company_id=company_id, session_id="baghdad-orange-regenerate")
    assert snapshots[0]["raw_model_response_before_regeneration"] == GENERIC_AI_JSON
    assert snapshots[0]["raw_model_response"] == OPERATIONAL_AI_JSON
    assert snapshots[0]["operational_regeneration"]["accepted"] is True
