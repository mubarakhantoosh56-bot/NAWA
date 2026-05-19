import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.core.aimx_prompt import AIMX_SYSTEM_PROMPT
from app.core.decision_prompt import AIMX_DECISION_PROMPT
from app.core.persona_prompt import build_persona_prompt, resolve_persona, resolve_response_language
from app.services.openai_client import AIService
from app.services.output_formatter import format_ai_response


VALID_AI_JSON = """
{
  "executive_summary": "Executive Summary\\n- Operating posture is clear.\\n\\nKey Insights\\n- Execution quality is improving.\\n\\nRisks\\n- Capacity remains the main constraint.\\n\\nRecommended Actions\\n- CEO: confirm the weekly execution review within 7 days.\\n\\nPriority Level\\n- High.",
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
        content = VALID_AI_JSON
        if any("response_language: ar" in message["content"] for message in kwargs["messages"]):
            content = """
{
  "executive_summary": "الملخص التنفيذي\\n- الموقف التشغيلي واضح ويتطلب ضبط الأولويات.\\n\\nأبرز الملاحظات\\n- جودة التنفيذ تتحسن.\\n\\nالمخاطر\\n- السعة التشغيلية هي القيد الرئيسي.\\n\\nالإجراءات الموصى بها\\n- الإدارة التنفيذية: تثبيت مراجعة أسبوعية للتنفيذ خلال 7 أيام.\\n\\nمستوى الأولوية\\n- عال.",
  "raw_decision": {
    "truth_validation": {
      "contradictions": []
    }
  }
}
"""
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
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


def test_ceo_default_selection():
    persona = resolve_persona({})
    prompt = build_persona_prompt({})

    assert persona.key == "ceo"
    assert "Name: CEO AI" in prompt
    assert "Scope: company_wide" in prompt
    assert "priorities, risks, execution" in prompt
    assert "Executive Summary, Key Insights, Risks, Recommended Actions, Priority Level" in prompt


def test_arabic_response_language_rules():
    context = {"response_language": "ar"}
    prompt = build_persona_prompt(context)

    assert resolve_response_language(context) == "ar"
    assert "Response language: Arabic" in prompt
    assert "الملخص التنفيذي" in prompt
    assert "أبرز الملاحظات" in prompt
    assert "مستوى الأولوية" in prompt
    assert "literal translation" in prompt


def test_department_persona_selection():
    context = {"aimx_department": {"department_type": "sales_ai"}}
    persona = resolve_persona(context)
    prompt = build_persona_prompt(context)

    assert persona.key == "sales"
    assert "Name: Sales AI" in prompt
    assert "pipeline quality" in prompt
    assert "conversion blockers" in prompt


def test_finance_persona_is_financially_focused():
    context = {"aimx_department": {"department_type": "finance_ai"}}
    prompt = build_persona_prompt(context)

    assert "Name: Finance AI" in prompt
    assert "margins, cash flow, costs, forecasts, financial risk" in prompt
    assert "approval guardrails" in prompt


def test_marketing_persona_is_campaign_focused():
    context = {"aimx_department": {"department_type": "marketing_ai"}}
    prompt = build_persona_prompt(context)

    assert "Name: Marketing AI" in prompt
    assert "campaigns, CAC, engagement, acquisition, positioning" in prompt
    assert "campaign quality" in prompt


def test_unknown_department_fallback_safety():
    context = {"aimx_department": {"department_type": "legal"}}
    persona = resolve_persona(context)
    prompt = build_persona_prompt(context)

    assert persona.key == "department"
    assert "Name: Department AI" in prompt
    assert "Operate inside this department's scope" in prompt


def test_persona_prompt_order_and_response_contract(monkeypatch):
    service, fake_client = _service_with_fake_client()
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="persona-session",
            message="hello",
            context={"aimx_department": {"department_type": "finance"}},
            company_id=str(uuid4()),
        )
    )

    messages = fake_client.chat_completions.messages[0]
    assert messages[0]["content"] == AIMX_SYSTEM_PROMPT
    assert messages[1]["content"] == AIMX_DECISION_PROMPT
    assert messages[2]["content"].startswith("NAWA PERSONA:")
    assert "Name: Finance AI" in messages[2]["content"]
    assert "Executive Summary, Key Insights, Risks, Recommended Actions, Priority Level" in messages[2]["content"]
    assert "DECISION CONTEXT ENGINE" in messages[3]["content"]
    assert "COMPANY CONTEXT:" in messages[4]["content"]
    assert "response_language: en" in messages[4]["content"]

    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}
    assert set(result["meta"].keys()) == {
        "company_id",
        "session_id",
        "context",
        "language",
        "parse_ok",
        "memory_injected",
        "events_count",
    }
    assert "NAWA PERSONA" not in result["ceo_text"]


def test_output_formatter_normalizes_arabic_headings():
    parsed = {
        "executive_summary": (
            "Executive Summary\n"
            "- Margin pressure is contained.\n\n"
            "Key Insights\n"
            "- Pipeline quality is improving.\n\n"
            "Risks\n"
            "- Capacity may constrain delivery.\n\n"
            "Recommended Actions\n"
            "- CEO: approve the weekly operating review.\n\n"
            "Priority Level\n"
            "- High."
        ),
        "raw_decision": {},
    }

    result = format_ai_response(
        answer_text="{}",
        parsed=parsed,
        session_id="s1",
        company_id="c1",
        language="ar",
    )

    assert "الملخص التنفيذي" in result["ceo_text"]
    assert "أبرز الملاحظات" in result["ceo_text"]
    assert "Executive Summary" not in result["ceo_text"]
    assert result["meta"]["language"] == "ar"


def test_ceo_chat_response_follows_arabic_language(monkeypatch):
    service, fake_client = _service_with_fake_client()
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="ceo-ar-session",
            message="اعطني الإحاطة التنفيذية",
            context={"response_language": "ar", "ui_language": "ar"},
            company_id=str(uuid4()),
        )
    )

    messages = fake_client.chat_completions.messages[0]
    assert any("response_language: ar" in message["content"] for message in messages)
    assert "الملخص التنفيذي" in result["ceo_text"]
    assert "مستوى الأولوية" in result["ceo_text"]
    assert "Executive Summary" not in result["ceo_text"]
    assert result["meta"]["language"] == "ar"


def test_ceo_chat_response_follows_english_language(monkeypatch):
    service, _fake_client = _service_with_fake_client()
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="ceo-en-session",
            message="Give me the CEO briefing.",
            context={"response_language": "en", "ui_language": "en"},
            company_id=str(uuid4()),
        )
    )

    assert "Executive Summary" in result["ceo_text"]
    assert "Priority Level" in result["ceo_text"]
    assert "الملخص التنفيذي" not in result["ceo_text"]
    assert result["meta"]["language"] == "en"


def test_company_profile_is_injected_when_active(monkeypatch):
    service, fake_client = _service_with_fake_client()
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="company-profile-session",
            message="Give me the CEO briefing.",
            context={
                "response_language": "en",
                "company_intelligence_profile": {
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
                    "is_active": True,
                },
            },
            company_id=str(uuid4()),
        )
    )

    messages = fake_client.chat_completions.messages[0]
    profile_blocks = [message["content"] for message in messages if "COMPANY INTELLIGENCE PROFILE" in message["content"]]
    assert len(profile_blocks) == 1
    assert "Food distribution" in profile_blocks[0]
    assert "branches, fulfillment, or inventory" in profile_blocks[0]
    assert result["meta"]["context"]["company_intelligence_profile"]["company_name"] == "Mesopotamia Foods"
