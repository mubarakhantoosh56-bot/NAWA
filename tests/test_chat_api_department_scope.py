"""API-level tests for app/api/chat.py::_build_chat_context (Codex M5
re-review Blocker 2 / M5-R2-F2).

aimx_department is server-authoritative context: it gates whether
pilot-specific Company Brain documents (app/services/company_brain_context.py)
and pilot Truth Context apply to a chat request. request.context is fully
client-controlled JSON with no schema on its keys, so any client-supplied
aimx_department must never survive into the authoritative context - it may
only ever be populated from a validated, company-scoped, RBAC-checked
department row resolved from request.department_id.
"""

from __future__ import annotations

import asyncio
import dataclasses
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import chat as chat_api
from app.core.dependencies import AuthContext
from app.models.request import ChatRequest
from app.services import operational_truth_context as otc
from app.services.openai_client import AIService

COMPANY_ID = uuid4()
OTHER_COMPANY_ID = uuid4()
DAIRTNA_DEPARTMENT_ID = uuid4()
CAESAR_DEPARTMENT_ID = uuid4()
FOREIGN_DEPARTMENT_ID = uuid4()

DAIRTNA_DEPARTMENT_ROW = {
    "id": DAIRTNA_DEPARTMENT_ID,
    "name": "Dairtna Poultry",
    "slug": "dairtna-poultry",
    "department_type": "production_ai",
    "ai_agent_enabled": True,
}
CAESAR_DEPARTMENT_ROW = {
    "id": CAESAR_DEPARTMENT_ID,
    "name": "Caesar Beverage",
    "slug": "caesar-beverage",
    "department_type": "production_ai",
    "ai_agent_enabled": True,
}
# Belongs to a different company - department_repo.get_by_id is
# company-scoped (WHERE company_id = $1 AND id = $2); even a matching slug
# must not help a department_id that doesn't belong to the caller's company.
FOREIGN_DEPARTMENT_ROW = {
    "id": FOREIGN_DEPARTMENT_ID,
    "name": "Someone Else's Department",
    "slug": "dairtna-poultry",
    "department_type": "production_ai",
    "ai_agent_enabled": True,
}


class _FakeCompanyRepo:
    async def get_intelligence_profile(self, company_id):
        return {}


class _FakeDepartmentRepo:
    """Mirrors DepartmentRepository.get_by_id's company-scoped lookup:
    keyed by (company_id, department_id), never department_id alone."""

    def __init__(self, rows_by_company_and_id: dict) -> None:
        self._rows = rows_by_company_and_id

    async def get_by_id(self, company_id, department_id):
        return self._rows.get((company_id, department_id))


def _fake_request() -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))


def _auth_context(*, permissions: list[str], company_id=COMPANY_ID) -> AuthContext:
    return AuthContext(
        company_id=str(company_id),
        user_id=str(uuid4()),
        permissions=permissions,
        role_slug="ceo",
    )


def _patch_repos(monkeypatch: pytest.MonkeyPatch, department_rows: dict) -> None:
    async def _fake_get_company_repository(request):
        return _FakeCompanyRepo()

    async def _fake_get_department_repository(request):
        return _FakeDepartmentRepo(department_rows)

    monkeypatch.setattr(chat_api, "_get_company_repository", _fake_get_company_repository)
    monkeypatch.setattr(chat_api, "_get_department_repository", _fake_get_department_repository)


def _configure_jannat_company_id(monkeypatch: pytest.MonkeyPatch, company_id: object) -> None:
    monkeypatch.setattr(otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID=str(company_id)))


# ---------------------------------------------------------------------------
# F2-T1 / F2-T2: client-supplied aimx_department is scrubbed
# ---------------------------------------------------------------------------


def test_no_department_id_scrubs_client_supplied_dairtna_department(monkeypatch) -> None:
    """F2-T1: no department_id + client context aimx_department=dairtna-poultry
    -> resulting authoritative context has no aimx_department."""
    _patch_repos(monkeypatch, {})
    auth_context = _auth_context(permissions=["workspace.ceo"])
    request = ChatRequest(
        company_id=str(COMPANY_ID),
        session_id="s1",
        message="Status?",
        department_id=None,
        context={
            "aimx_department": {
                "id": str(uuid4()),
                "slug": "dairtna-poultry",
                "department_type": "production_ai",
            }
        },
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    assert "aimx_department" not in context


def test_no_department_id_scrubs_arbitrary_client_department_object(monkeypatch) -> None:
    """F2-T2: any arbitrary client-supplied department-shaped object is
    removed too, not just ones that look like a real department."""
    _patch_repos(monkeypatch, {})
    auth_context = _auth_context(permissions=["workspace.ceo"])
    request = ChatRequest(
        company_id=str(COMPANY_ID),
        session_id="s2",
        message="Status?",
        department_id=None,
        context={"aimx_department": {"slug": "anything-at-all", "name": "Whatever"}},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    assert "aimx_department" not in context


# ---------------------------------------------------------------------------
# F2-T3 / F2-T4: server-populated department scope from a validated row
# ---------------------------------------------------------------------------


def test_validated_dairtna_department_id_populates_server_authoritative_scope(monkeypatch) -> None:
    """F2-T3."""
    _patch_repos(monkeypatch, {(COMPANY_ID, DAIRTNA_DEPARTMENT_ID): DAIRTNA_DEPARTMENT_ROW})
    auth_context = _auth_context(permissions=["agents.production_ai.use"])
    request = ChatRequest(
        company_id=str(COMPANY_ID),
        session_id="s3",
        message="Status?",
        department_id=str(DAIRTNA_DEPARTMENT_ID),
        context={},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    assert context["aimx_department"]["slug"] == "dairtna-poultry"
    assert context["aimx_department"]["id"] == str(DAIRTNA_DEPARTMENT_ID)


def test_validated_caesar_department_id_populates_server_authoritative_scope(monkeypatch) -> None:
    """F2-T4."""
    _patch_repos(monkeypatch, {(COMPANY_ID, CAESAR_DEPARTMENT_ID): CAESAR_DEPARTMENT_ROW})
    auth_context = _auth_context(permissions=["agents.production_ai.use"])
    request = ChatRequest(
        company_id=str(COMPANY_ID),
        session_id="s4",
        message="Status?",
        department_id=str(CAESAR_DEPARTMENT_ID),
        context={},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    assert context["aimx_department"]["slug"] == "caesar-beverage"


def test_client_supplied_aimx_department_cannot_override_validated_row(monkeypatch) -> None:
    """A client sending BOTH a valid department_id AND a spoofed
    context.aimx_department must get the server-validated value, never the
    client-supplied one."""
    _patch_repos(monkeypatch, {(COMPANY_ID, CAESAR_DEPARTMENT_ID): CAESAR_DEPARTMENT_ROW})
    auth_context = _auth_context(permissions=["agents.production_ai.use"])
    request = ChatRequest(
        company_id=str(COMPANY_ID),
        session_id="s4b",
        message="Status?",
        department_id=str(CAESAR_DEPARTMENT_ID),
        context={"aimx_department": {"slug": "dairtna-poultry", "department_type": "production_ai"}},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    assert context["aimx_department"]["slug"] == "caesar-beverage"


# ---------------------------------------------------------------------------
# F2-T5: department_id from another company is rejected
# ---------------------------------------------------------------------------


def test_department_id_from_another_company_is_rejected(monkeypatch) -> None:
    """F2-T5."""
    _patch_repos(monkeypatch, {(OTHER_COMPANY_ID, FOREIGN_DEPARTMENT_ID): FOREIGN_DEPARTMENT_ROW})
    auth_context = _auth_context(permissions=["agents.production_ai.use"], company_id=COMPANY_ID)
    request = ChatRequest(
        company_id=str(COMPANY_ID),
        session_id="s5",
        message="Status?",
        department_id=str(FOREIGN_DEPARTMENT_ID),
        context={},
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
        )
    assert exc_info.value.status_code == 403


def test_no_department_id_without_ceo_permission_is_rejected(monkeypatch) -> None:
    """Sanity check: unrelated pre-existing authorization behavior is
    unaffected by the scrub fix - a non-CEO request with no department_id
    is still rejected."""
    _patch_repos(monkeypatch, {})
    auth_context = _auth_context(permissions=[])
    request = ChatRequest(
        company_id=str(COMPANY_ID), session_id="s6", message="Status?", department_id=None, context={}
    )
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
        )
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# F2-T6 / F2-T7 / F2-T8: end to end through API context construction AND
# the real AIService.chat() path together (not just the assembler, and not
# just _build_chat_context in isolation).
# ---------------------------------------------------------------------------


class _FakeChatCompletions:
    def __init__(self) -> None:
        self.messages: list = []

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=_VALID_AI_JSON))])


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.chat_completions = _FakeChatCompletions()
        self.chat = SimpleNamespace(completions=self.chat_completions)


class _FakeChatDbPool:
    def __init__(self, company_row: dict) -> None:
        self._company_row = company_row

    async def fetchrow(self, query, *args):
        return self._company_row


_VALID_REASONING_ASSESSMENT = """
{
  "reasoning_state": "insufficient_evidence",
  "operational_assessment": "n/a",
  "company_brain_alignment": "cannot determine",
  "tensions": [],
  "evidence_gaps": [],
  "risk_assessment": "n/a",
  "confidence": 50,
  "recommendation_basis": {"evidence_basis": [], "company_basis": [], "missing_evidence": [], "organizational_memory_basis": []}
}
"""

_VALID_AI_JSON = (
    """
{
  "executive_summary": "Executive Summary\\n- Operational review complete for Production; inventory operational impact assessed as normal.\\n\\nRecommended Actions\\n- Monitor hall performance.\\n\\nPriority Level\\n- Medium.",
  "raw_decision": {"truth_validation": {"contradictions": []}, "reasoning_assessment": """
    + _VALID_REASONING_ASSESSMENT
    + """}
}
"""
)


def _service_with_fake_db(company_row: dict) -> tuple[AIService, _FakeOpenAIClient]:
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeChatDbPool(company_row)
    return service, fake_client


def test_end_to_end_ceo_scope_malicious_context_excludes_dairtna_company_brain(monkeypatch) -> None:
    """F2-T6: a CEO/no-department request whose client context tries to
    inject aimx_department=dairtna-poultry must not get Dairtna Company
    Brain content in the final prompt, proven through _build_chat_context
    -> AIService.chat() together."""
    jannat_company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, jannat_company_id)
    _patch_repos(monkeypatch, {})
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    auth_context = _auth_context(permissions=["workspace.ceo"], company_id=jannat_company_id)
    request = ChatRequest(
        company_id=str(jannat_company_id),
        session_id="s7",
        message="Status?",
        department_id=None,
        context={"aimx_department": {"slug": "dairtna-poultry", "department_type": "production_ai"}},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    company_row = {"id": jannat_company_id, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}
    service, fake_client = _service_with_fake_db(company_row)

    result = asyncio.run(
        service.chat(session_id="s7", message="Status?", context=context, company_id=str(jannat_company_id))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "Type: DECISION_RULE" not in prompt_text
    assert "Type: PREFERENCE" not in prompt_text


def test_end_to_end_dairtna_department_request_includes_company_brain(monkeypatch) -> None:
    """F2-T7: a real Dairtna Poultry department request, with JANNAT_COMPANY_ID
    matching the authenticated company, gets Company Brain content."""
    jannat_company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, jannat_company_id)
    _patch_repos(monkeypatch, {(jannat_company_id, DAIRTNA_DEPARTMENT_ID): DAIRTNA_DEPARTMENT_ROW})
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    auth_context = _auth_context(permissions=["agents.production_ai.use"], company_id=jannat_company_id)
    request = ChatRequest(
        company_id=str(jannat_company_id),
        session_id="s8",
        message="Status?",
        department_id=str(DAIRTNA_DEPARTMENT_ID),
        context={},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    company_row = {"id": jannat_company_id, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}
    service, fake_client = _service_with_fake_db(company_row)

    result = asyncio.run(
        service.chat(session_id="s8", message="Status?", context=context, company_id=str(jannat_company_id))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is True
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "[Company Brain Context]" in prompt_text
    assert "Type: DECISION_RULE" in prompt_text


def test_end_to_end_caesar_department_request_excludes_company_brain(monkeypatch) -> None:
    """F2-T8."""
    jannat_company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, jannat_company_id)
    _patch_repos(monkeypatch, {(jannat_company_id, CAESAR_DEPARTMENT_ID): CAESAR_DEPARTMENT_ROW})
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    auth_context = _auth_context(permissions=["agents.production_ai.use"], company_id=jannat_company_id)
    request = ChatRequest(
        company_id=str(jannat_company_id),
        session_id="s9",
        message="Status?",
        department_id=str(CAESAR_DEPARTMENT_ID),
        context={},
    )

    context = asyncio.run(
        chat_api._build_chat_context(http_request=_fake_request(), request=request, auth_context=auth_context)
    )
    company_row = {"id": jannat_company_id, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}
    service, fake_client = _service_with_fake_db(company_row)

    result = asyncio.run(
        service.chat(session_id="s9", message="Status?", context=context, company_id=str(jannat_company_id))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
