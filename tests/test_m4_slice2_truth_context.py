"""M4 Slice 2 (Truth Context -> Decision Context -> LLM wiring) acceptance
tests.

Golden rule for this module: never assert on the exact numeric value of a
real pilot-file reading. Tests that touch the real ``data_sources/``
workbooks only assert structural/epistemic properties (status, origin,
entity, source_time/status, presence/absence) - never a specific quantity -
matching the confidentiality discipline used throughout this project's
pilot-data work. Fixtures that need concrete numbers are synthetic.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.oce.collectors.poultry_context_collector import PoultryContextCollector
from app.services import operational_truth_context as otc
from app.services.decision_context import (
    build_decision_context,
    build_decision_context_prompt_block,
)
from app.services.openai_client import AIService

JANNAT_COMPANY = {"slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}
OTHER_COMPANY = {"slug": "acme-fmcg", "name": "Acme FMCG", "metadata": {}}
POULTRY_DEPARTMENT = {"name": "Dairtna Poultry", "department_type": "poultry_ai", "slug": "dairtna-poultry"}
SALES_DEPARTMENT = {"name": "Sales", "department_type": "sales_ai", "slug": "sales"}


# ---------------------------------------------------------------------------
# Tenant / department classification (T8, T9)
# ---------------------------------------------------------------------------


def test_is_jannat_tenant_true_for_pilot_company() -> None:
    assert otc.is_jannat_tenant(JANNAT_COMPANY) is True


def test_is_jannat_tenant_false_for_other_company() -> None:
    assert otc.is_jannat_tenant(OTHER_COMPANY) is False
    assert otc.is_jannat_tenant(None) is False


def test_is_poultry_department_scope_true_for_dairtna() -> None:
    assert otc.is_poultry_department_scope(POULTRY_DEPARTMENT) is True


def test_is_poultry_department_scope_false_for_other_department() -> None:
    assert otc.is_poultry_department_scope(SALES_DEPARTMENT) is False
    assert otc.is_poultry_department_scope(None) is False


# ---------------------------------------------------------------------------
# T9 - company isolation
# ---------------------------------------------------------------------------


def test_assemble_truth_context_not_applicable_for_non_jannat_company() -> None:
    result = otc.assemble_truth_context(company=OTHER_COMPANY, aimx_department=None)
    assert result.status == "not_applicable"
    assert result.items == []


def test_assemble_truth_context_not_applicable_for_missing_company() -> None:
    result = otc.assemble_truth_context(company=None, aimx_department=None)
    assert result.status == "not_applicable"


# ---------------------------------------------------------------------------
# T8 - department / hall / company scope
# ---------------------------------------------------------------------------


def test_assemble_truth_context_not_applicable_for_non_poultry_department() -> None:
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=SALES_DEPARTMENT)
    assert result.status == "not_applicable"
    assert result.items == []


def test_assemble_truth_context_ok_for_ceo_scope_real_pilot_data() -> None:
    """T1: real pilot files produce evidence reaching the bounded contract."""
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    assert result.status == "ok"
    assert result.evidence_count > 0
    assert result.items


def test_entity_scope_distinguishes_halls_from_company_aggregate() -> None:
    """T8: distinct halls and the company aggregate stay distinguishable,
    never collapsed into one undifferentiated entity."""
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    entity_pairs = {
        (item.get("entity_type"), item.get("entity_reference")) for item in result.items
    }
    assert ("company_aggregate", None) in entity_pairs
    hall_entities = {pair for pair in entity_pairs if pair[0] == "production_hall"}
    assert len(hall_entities) >= 2  # at least two distinct real halls present
    assert ("feed_mill", None) in entity_pairs


# ---------------------------------------------------------------------------
# T2 - OBSERVED origin survives; T7 - Feed Mill Golden Case
# ---------------------------------------------------------------------------


def test_headline_production_metric_is_observed_with_authoritative_time() -> None:
    """T2: a direct observed production claim carries entity + provenance +
    an authoritative source time - value itself is never asserted."""
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    headline = [
        item
        for item in result.items
        if item.get("type") in otc.HEADLINE_OBSERVED_METRIC_FIELDS
    ]
    assert headline
    for item in headline:
        assert item["epistemic_origin"] == "observed"
        assert item["normalized_value"] is not None
        assert item["source_label"] is not None
        assert item["source_time_status"] == "authoritative"
        assert item["source_time"] is not None


def test_feed_mill_golden_case_observed_with_unresolved_source_time() -> None:
    """T7: Feed Mill inventory is OBSERVED while its own report/source time
    stays unresolved - the two properties coexist without contradiction."""
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    feed_mill_items = [item for item in result.items if item.get("entity_type") == "feed_mill"]
    assert feed_mill_items
    for item in feed_mill_items:
        assert item["epistemic_origin"] == "observed"
        assert item["source_time"] is None
        assert item["source_time_status"] == "unresolved"


# ---------------------------------------------------------------------------
# T3 - DERIVED origin survives, distinct from OBSERVED
# ---------------------------------------------------------------------------


def test_production_trend_item_is_derived_not_observed() -> None:
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    trend_items = [item for item in result.items if item.get("type") == "production_trend"]
    assert trend_items
    for item in trend_items:
        assert item["epistemic_origin"] == "derived"
        assert item["epistemic_origin"] != "observed"


# ---------------------------------------------------------------------------
# T5 - missing evidence stays missing, never becomes zero
# ---------------------------------------------------------------------------


def test_missing_evidence_items_stay_missing_never_zero() -> None:
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    missing_items = [item for item in result.items if item.get("status") == "missing"]
    assert missing_items
    for item in missing_items:
        assert item["normalized_value"] is None
        assert item["normalized_value"] != 0


# ---------------------------------------------------------------------------
# T11 - no evidence creates no fake truth
# ---------------------------------------------------------------------------


def test_no_evidence_when_pilot_directory_absent(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", tmp_path / "does_not_exist")
    result = otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)
    assert result.status == "no_evidence"
    assert result.items == []
    assert result.evidence_count == 0


# ---------------------------------------------------------------------------
# T12 - unexpected OCE failure is visible/testable (never silently swallowed)
# ---------------------------------------------------------------------------


def test_unexpected_collector_failure_propagates_not_silently_swallowed(monkeypatch) -> None:
    def _boom(self, **kwargs):
        raise RuntimeError("synthetic unexpected OCE failure")

    monkeypatch.setattr(PoultryContextCollector, "collect", _boom)
    with pytest.raises(RuntimeError):
        otc.assemble_truth_context(company=JANNAT_COMPANY, aimx_department=None)


# ---------------------------------------------------------------------------
# decision_context.py wiring (T1, T5, T6, T10, T15)
# ---------------------------------------------------------------------------


SYNTHETIC_TRUTH_ITEMS = [
    {
        "type": "bird_balance",
        "status": "available",
        "epistemic_origin": "observed",
        "canonical_field": "bird_balance",
        "normalized_value": 12345,
        "source_label": "رصيد الطيور",
        "raw_source_value": "12345",
        "source_file": "hall2.xlsx",
        "entity_type": "production_hall",
        "entity_reference": "2",
        "source_time": "2026-06-01",
        "source_time_status": "authoritative",
        "provenance_warnings": (),
    },
    {
        "type": "production_trend",
        "status": "available",
        "epistemic_origin": "derived",
        "canonical_field": "daily_production_rate",
        "normalized_value": None,
        "entity_type": "production_hall",
        "entity_reference": "2",
        "source_time": "2026-06-03",
        "source_time_status": "authoritative",
        "provenance_warnings": (),
    },
    {
        "type": "raw_material_inventory",
        "status": "available",
        "epistemic_origin": "observed",
        "canonical_field": None,
        "normalized_value": None,
        "entity_type": "feed_mill",
        "entity_reference": None,
        "source_time": None,
        "source_time_status": "unresolved",
        "provenance_warnings": ("report_date_not_authoritative: ...",),
    },
    {
        "type": "water_consumption",
        "status": "missing",
        "epistemic_origin": None,
        "canonical_field": None,
        "normalized_value": None,
        "entity_type": None,
        "entity_reference": None,
        "source_time": None,
        "source_time_status": None,
        "provenance_warnings": (),
    },
]


def test_build_decision_context_carries_operational_truth_context_key() -> None:
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
    )
    assert decision_context["operational_truth_context"] == SYNTHETIC_TRUTH_ITEMS
    # T10: distinct from memory/company-brain-adjacent keys, never merged in.
    assert decision_context["operational_truth_context"] is not decision_context["memory_events"]
    assert decision_context["operational_truth_context"] is not decision_context["operational_events"]
    assert decision_context["operational_truth_context"] is not decision_context["trends"]


def test_decision_context_backward_compatible_without_truth_context() -> None:
    """T15: the pre-Slice-2 call signature (no operational_truth_context
    kwarg) still works and defaults to an empty list."""
    decision_context = build_decision_context(context={}, response_language="en")
    assert decision_context["operational_truth_context"] == []


def test_prompt_block_shows_observed_and_derived_distinctly() -> None:
    """T2 / T3: the prompt text distinguishes OBSERVED from DERIVED, not a
    flattened 'facts' list."""
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=SYNTHETIC_TRUTH_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "[Operational Truth Context]" in block
    assert "Claim: bird_balance" in block
    assert "Origin: OBSERVED" in block
    assert "Origin: DERIVED" in block


def test_prompt_block_shows_missing_as_missing_not_zero() -> None:
    """T5."""
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=SYNTHETIC_TRUTH_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "Claim: water_consumption | Status: missing" in block
    assert "Value: 0" not in block


def test_prompt_block_preserves_unresolved_source_time_for_feed_mill() -> None:
    """T6 / T7."""
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=SYNTHETIC_TRUTH_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "Entity: feed_mill" in block
    assert "Source time: unresolved (unresolved)" in block


def test_prompt_block_includes_truth_context_reasoning_rules() -> None:
    """T11 supportive: the model is instructed not to invent facts and to
    treat missing/unresolved evidence conservatively."""
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=SYNTHETIC_TRUTH_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "must never be treated as a confirmed fact" in block
    assert "Missing operational evidence means the value is unknown, not zero" in block
    assert "do not describe that evidence as current, recent, fresh, or up to date" in block
    assert "must not be presented as if it describes one specific hall/entity" in block
    assert "rather than inventing operational facts" in block


def test_prompt_block_empty_when_no_truth_context_items() -> None:
    decision_context = build_decision_context(context={}, response_language="en")
    block = build_decision_context_prompt_block(decision_context)
    assert "[Operational Truth Context]" not in block


# ---------------------------------------------------------------------------
# T4 / T13 - M2 Operational Event origin cannot masquerade as observed
# ---------------------------------------------------------------------------


def test_compact_operational_events_preserves_inferred_origin() -> None:
    from app.services.decision_context import _compact_operational_events

    events = [
        {
            "event_type": "operational.file_draft",
            "executive_summary": "AI-drafted mortality note confirmed by a user.",
            "context": {"source_role": "manager", "origin": "inferred"},
        }
    ]
    compacted = _compact_operational_events(events)
    assert compacted[0]["origin"] == "inferred"
    assert compacted[0]["origin"] != "observed"


def test_compact_operational_events_defaults_origin_to_none_when_absent() -> None:
    from app.services.decision_context import _compact_operational_events

    events = [
        {
            "event_type": "operational.manual",
            "executive_summary": "Manually reported issue.",
            "context": {},
        }
    ]
    compacted = _compact_operational_events(events)
    assert compacted[0]["origin"] is None


# ---------------------------------------------------------------------------
# AIService.chat() integration (T1, T8, T9, T12, T15)
# ---------------------------------------------------------------------------


class _FakeChatCompletions:
    def __init__(self, responses=None):
        self.messages = []
        self.responses = list(responses or [_VALID_AI_JSON])

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        response_text = self.responses.pop(0) if self.responses else _VALID_AI_JSON
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response_text))]
        )


class _FakeOpenAIClient:
    def __init__(self, responses=None):
        self.chat_completions = _FakeChatCompletions(responses)
        self.chat = SimpleNamespace(completions=self.chat_completions)


class _FakeDbPool:
    """Minimal asyncpg-pool stand-in supporting only what CompanyRepository
    needs; every other query method (.fetch/.fetchval) used by the other
    _load_*_block methods is intentionally absent - those methods already
    wrap their own queries in try/except and degrade to "" (verified
    against the existing codebase pattern), so this does not need to
    implement them.
    """

    def __init__(self, company_row: dict | None) -> None:
        self._company_row = company_row

    async def fetchrow(self, query, *args):
        return self._company_row


_VALID_AI_JSON = """
{
  "executive_summary": "Executive Summary\\n- Operational review complete.\\n\\nRecommended Actions\\n- Monitor hall performance.\\n\\nPriority Level\\n- Medium.",
  "raw_decision": {"truth_validation": {"contradictions": []}}
}
"""


def _service_with_fake_db(company_row: dict | None) -> tuple[AIService, _FakeOpenAIClient]:
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeDbPool(company_row)
    return service, fake_client


def test_chat_truth_context_not_configured_without_db_pool(monkeypatch) -> None:
    """T15: pre-Slice-2 behavior (no db pool) is unaffected."""
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = False
    service.db_pool = None
    service.repo = None
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="s1", message="Status update?", context={}, company_id=str(uuid4())
        )
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "not_configured"
    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}


def test_chat_truth_context_not_applicable_for_non_jannat_company(monkeypatch) -> None:
    """T9: company isolation - a non-pilot tenant never sees pilot evidence."""
    service, fake_client = _service_with_fake_db(OTHER_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="s2", message="Status update?", context={}, company_id=str(uuid4())
        )
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "not_applicable"
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "[Operational Truth Context]" not in prompt_text


def test_chat_truth_context_ok_for_jannat_ceo_scope(monkeypatch) -> None:
    """T1 / T7: real evidence reaches the actual assembled prompt text for
    the pilot tenant at CEO (company-wide) scope."""
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="s3", message="Status update?", context={}, company_id=str(uuid4())
        )
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "ok"
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "[Operational Truth Context]" in prompt_text
    assert "OBSERVED" in prompt_text
    assert "feed_mill" in prompt_text


def test_chat_truth_context_department_scoped_non_poultry_is_not_applicable(monkeypatch) -> None:
    """T8: a non-poultry department scope excludes pilot evidence even for
    the pilot tenant."""
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="s4",
            message="Status update?",
            context={"aimx_department": SALES_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "not_applicable"


def test_chat_truth_context_unexpected_failure_degrades_gracefully(monkeypatch) -> None:
    """T12: an unexpected assembly failure is visible via status="error"
    and does not crash the overall chat response."""
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    def _boom(**kwargs):
        raise RuntimeError("synthetic unexpected truth-context failure")

    monkeypatch.setattr("app.services.openai_client.assemble_truth_context", _boom)

    result = asyncio.run(
        service.chat(
            session_id="s5", message="Status update?", context={}, company_id=str(uuid4())
        )
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "error"
    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}
