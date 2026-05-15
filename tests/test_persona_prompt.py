import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.core.aimx_prompt import AIMX_SYSTEM_PROMPT
from app.core.decision_prompt import AIMX_DECISION_PROMPT
from app.core.persona_prompt import build_persona_prompt, resolve_persona
from app.services.openai_client import AIService


VALID_AI_JSON = """
{
  "executive_summary": "ok",
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


def test_ceo_default_selection():
    persona = resolve_persona({})
    prompt = build_persona_prompt({})

    assert persona.key == "ceo"
    assert "Name: CEO AI" in prompt
    assert "Scope: company_wide" in prompt


def test_department_persona_selection():
    context = {"aimx_department": {"department_type": "sales_ai"}}
    persona = resolve_persona(context)
    prompt = build_persona_prompt(context)

    assert persona.key == "sales"
    assert "Name: Sales AI" in prompt
    assert "pipeline" in prompt


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
    assert messages[2]["content"].startswith("AIMX PERSONA:")
    assert "Name: Finance AI" in messages[2]["content"]
    assert "COMPANY CONTEXT:" in messages[3]["content"]

    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}
    assert set(result["meta"].keys()) == {
        "company_id",
        "session_id",
        "context",
        "parse_ok",
        "memory_injected",
        "events_count",
    }
    assert "AIMX PERSONA" not in result["ceo_text"]
