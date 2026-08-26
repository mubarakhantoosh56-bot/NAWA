"""M5 (Company Brain Integration) acceptance tests.

Company Brain answers "what does this company believe/prefer/prioritize/
require/prohibit/normally do" - never "what is objectively happening
operationally right now" (that is Truth Context, M4 Slice 2). These tests
prove that separation holds end to end, that memory-fact conflict state
(ENG-CONF-001, read-only here) survives without being silently resolved,
and that tenant/department scope is respected.

Golden rule for this module: real Dairtna Company Brain document text is
quoted directly in several assertions below (it is company governance/
policy text, not a confidential operational value like a bird count or
production rate - the whole point of M5 is getting this text to the LLM).
No operational VALUE from data_sources/ is ever asserted here.
"""

from __future__ import annotations

import asyncio
import dataclasses
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import company_brain_context as cbc
from app.services import operational_truth_context as otc
from app.services.decision_context import (
    build_decision_context,
    build_decision_context_prompt_block,
)
from app.services.openai_client import AIService

JANNAT_COMPANY_ID = uuid4()
JANNAT_COMPANY = {
    "id": JANNAT_COMPANY_ID,
    "slug": "jannat-al-firdaws",
    "name": "Jannat Al-Firdaws",
    "metadata": {},
}
OTHER_COMPANY = {"id": uuid4(), "slug": "acme-fmcg", "name": "Acme FMCG", "metadata": {}}
POULTRY_DEPARTMENT = {"name": "Dairtna Poultry", "department_type": "poultry_ai", "slug": "dairtna-poultry"}
SALES_DEPARTMENT = {"name": "Sales", "department_type": "sales_ai", "slug": "sales"}
CAESAR_DEPARTMENT = {"name": "Caesar Beverage", "department_type": "production_ai", "slug": "caesar-beverage"}
SHARED_CORPORATE_DEPARTMENT = {
    "name": "Shared Corporate Services",
    "department_type": "custom",
    # Verified against the real pilot tenant's live departments table
    # (read-only check, structural identifier only) - "shared-corporate",
    # not "shared-corporate-services".
    "slug": "shared-corporate",
}

# F1 adversarial fixtures: every one of these is designed to defeat the OLD
# fuzzy substring/alias matching that used to live in
# operational_truth_context.is_jannat_tenant, and must be rejected by the
# exact, authoritative id/slug check that replaced it.
SPOOFED_NAME_COMPANY = {
    "id": uuid4(),
    "slug": "new-jannat-firdaws-foods",
    "name": "New Jannat Firdaws Foods Co.",
    "metadata": {},
}
SPOOFED_SLUG_SUFFIX_COMPANY = {
    "id": uuid4(),
    "slug": "jannat-al-firdaws-holdings",
    "name": "Jannat Al-Firdaws Holdings",
    "metadata": {},
}
SPOOFED_ARABIC_ALIAS_COMPANY = {
    "id": uuid4(),
    "slug": "acme-fmcg-jo",
    "name": "شركة الفردوس التجارية",
    "metadata": {},
}
def _configure_jannat_company_id(monkeypatch: pytest.MonkeyPatch, company_id: object) -> None:
    """R2-F1: settings is a frozen dataclass, so JANNAT_COMPANY_ID cannot be
    set via monkeypatch.setenv (it's read once at import time) or via
    monkeypatch.setattr on an individual frozen field. Replace the
    operational_truth_context module's ``settings`` reference with a new
    frozen instance carrying the override - monkeypatch restores the
    original reference after the test."""
    monkeypatch.setattr(otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID=str(company_id)))

NON_CONFLICTED_FACT = {
    "fact_key": "growth_stage",
    "fact_value": "early expansion phase",
    "has_conflict": False,
}
CONFLICTED_FACT = {
    "fact_key": "target_market",
    "fact_value": "regional expansion",
    "has_conflict": True,
    "residual_uncertainty": "conflicting statements recorded across sessions",
}


# ---------------------------------------------------------------------------
# Memory facts -> INSTITUTIONAL_MEMORY (T1, T8, Scenario D)
# ---------------------------------------------------------------------------


def test_memory_fact_classified_as_institutional_memory() -> None:
    result = cbc.assemble_company_brain_context(
        company=OTHER_COMPANY, aimx_department=None, memory_facts=[NON_CONFLICTED_FACT]
    )
    assert result.status == "ok"
    assert len(result.items) == 1
    item = result.items[0]
    assert item["type"] == "INSTITUTIONAL_MEMORY"
    assert item["authority"] == "institutional"
    assert item["conflict_state"] is None


def test_conflicted_memory_fact_marked_unresolved_not_uncontested() -> None:
    """T8 / Scenario D: a conflicted fact must not be presented as settled
    institutional truth - M5 never picks a winner."""
    result = cbc.assemble_company_brain_context(
        company=OTHER_COMPANY, aimx_department=None, memory_facts=[CONFLICTED_FACT]
    )
    item = result.items[0]
    assert item["type"] == "INSTITUTIONAL_MEMORY"
    assert item["authority"] == "unresolved"
    assert item["conflict_state"] == "conflicted"
    assert item["provenance_note"]


# ---------------------------------------------------------------------------
# Tenant isolation (T9, Scenario F)
# ---------------------------------------------------------------------------


def test_other_tenant_never_receives_dairtna_knowledge() -> None:
    result = cbc.assemble_company_brain_context(
        company=OTHER_COMPANY, aimx_department=None, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False
    assert not any(item["source_type"] == "company_knowledge_document" for item in result.items)


def test_missing_company_never_receives_dairtna_knowledge() -> None:
    result = cbc.assemble_company_brain_context(
        company=None, aimx_department=None, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False
    assert result.status == "no_evidence"


# ---------------------------------------------------------------------------
# R2-F1 fix verification: fail-closed, authoritative tenant entitlement
# (Codex M5 re-review Blocker 1). Every fixture below pairs the company
# under test with the poultry department scope, so a failure can only be
# explained by the entitlement check itself (not by the F2 applicability
# gate also being closed).
# ---------------------------------------------------------------------------


def test_real_pilot_tenant_not_entitled_without_configured_id() -> None:
    """F1-T1/F1-T2: fail closed by default. With JANNAT_COMPANY_ID unset
    (no monkeypatch applied), even the real pilot tenant's exact canonical
    slug is NOT sufficient - there is no slug fallback anymore."""
    assert otc.settings.JANNAT_COMPANY_ID == ""
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False
    assert not any(item["source_type"] == "company_knowledge_document" for item in result.items)


def test_real_pilot_tenant_entitled_when_id_configured(monkeypatch) -> None:
    """F1-T3: with JANNAT_COMPANY_ID configured to match the authenticated
    company's id exactly, the real pilot tenant is entitled."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is True


def test_configured_id_does_not_grant_entitlement_to_a_different_company_with_canonical_slug(
    monkeypatch,
) -> None:
    """F1-T4: configuring the real pilot id does not entitle some OTHER
    company just because it happens to carry the canonical slug."""
    spoofed_with_canonical_slug = {
        "id": uuid4(),
        "slug": "jannat-al-firdaws",
        "name": "Jannat Al-Firdaws",
        "metadata": {},
    }
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=spoofed_with_canonical_slug, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False


def test_malformed_configured_id_fails_closed(monkeypatch) -> None:
    """F1-T5."""
    monkeypatch.setattr(otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID="not-a-uuid"))
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False


def test_wrong_configured_id_fails_closed(monkeypatch) -> None:
    """F1-T6."""
    _configure_jannat_company_id(monkeypatch, uuid4())
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False


def test_spoofed_name_containing_jannat_and_firdaws_is_not_entitled(monkeypatch) -> None:
    """F1-T8: a company whose NAME contains both "Jannat" and "Firdaws" as
    substrings is rejected even with JANNAT_COMPANY_ID configured to the
    real pilot id - name/slug text is never part of the entitlement
    decision. The old fuzzy all-terms-in-haystack rule would have matched
    this."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=SPOOFED_NAME_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False
    assert not any(item["source_type"] == "company_knowledge_document" for item in result.items)


def test_spoofed_slug_with_extra_suffix_is_not_entitled(monkeypatch) -> None:
    """F1-T8: a slug that merely contains the canonical pilot slug as a
    substring (e.g. a "-holdings" suffix) is irrelevant to entitlement -
    only id equality matters."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=SPOOFED_SLUG_SUFFIX_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False


def test_spoofed_arabic_alias_in_name_is_not_entitled(monkeypatch) -> None:
    """F1-T8: a company whose name contains the Arabic alias "الفردوس" must
    not match - Arabic/English alias matching is an explicitly forbidden
    solution shape, not just the English fuzzy terms."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=SPOOFED_ARABIC_ALIAS_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False


# ---------------------------------------------------------------------------
# Department scope (T10, Scenario G)
# ---------------------------------------------------------------------------


def test_non_poultry_department_excludes_dairtna_knowledge_but_keeps_memory_facts() -> None:
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=SALES_DEPARTMENT, memory_facts=[NON_CONFLICTED_FACT]
    )
    assert result.dairtna_knowledge_included is False
    assert not any(item["source_type"] == "company_knowledge_document" for item in result.items)
    # Company-wide generic memory (not Dairtna-specific) still applies.
    assert any(item["type"] == "INSTITUTIONAL_MEMORY" for item in result.items)


def test_poultry_department_scope_includes_dairtna_knowledge(monkeypatch) -> None:
    """T-I: Dairtna Poultry scope (Codex F2 required behavior A). Entitlement
    is configured explicitly so this isolates the applicability axis."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is True
    assert any(item["source_type"] == "company_knowledge_document" for item in result.items)


def test_caesar_beverage_scope_excludes_dairtna_knowledge(monkeypatch) -> None:
    """T-J: Caesar Beverage scope must be excluded (Codex F2 required
    behavior B) - Dairtna is one business unit, not company-wide policy.
    Entitlement is configured explicitly so exclusion is proven to be an
    applicability decision, not a (separately fail-closed) entitlement
    decision."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=CAESAR_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False
    assert not any(item["source_type"] == "company_knowledge_document" for item in result.items)


def test_shared_corporate_scope_excludes_dairtna_knowledge(monkeypatch) -> None:
    """T-K: Shared Corporate scope must be excluded by default (Codex F2
    required behavior C) - no Company Brain item is currently marked
    holding-company/shared-safe, so nothing overrides the exclusion."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=SHARED_CORPORATE_DEPARTMENT, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False


def test_unresolved_company_wide_ceo_scope_excludes_dairtna_knowledge_by_default(monkeypatch) -> None:
    """T-L: an unresolved/company-wide scope (no department selected, e.g.
    the CEO workspace) must NOT auto-inject Dairtna-specific docs by
    default (Codex F2 required behavior D) - this is the exact case the
    pre-fix code got backwards (aimx_department is None used to mean
    "include everywhere"). Entitlement is configured explicitly so this
    isolates the applicability axis from the (separately fail-closed)
    entitlement axis."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=None, memory_facts=[]
    )
    assert result.dairtna_knowledge_included is False
    assert not any(item["source_type"] == "company_knowledge_document" for item in result.items)


# ---------------------------------------------------------------------------
# Semantic classification (T5, T6, T7, Scenario A/B/I)
# ---------------------------------------------------------------------------


def test_decision_rules_retain_decision_rule_type(monkeypatch) -> None:
    """T5 / Scenario A: an authoritative decision rule reaches Company
    Brain as DECISION_RULE, never as a Truth claim."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    decision_rules = [item for item in result.items if item["type"] == "DECISION_RULE"]
    assert decision_rules
    assert all(item["source"] == "DAIRTNA_DECISION_RULES" for item in decision_rules)
    assert all(item["authority"] == "authoritative" for item in decision_rules)


def test_company_preferences_retain_preference_type_not_observed(monkeypatch) -> None:
    """T6 / T4 / Scenario B: a management preference reaches Company Brain
    with PREFERENCE semantics and can never be classified OBSERVED."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    preferences = [item for item in result.items if item["type"] == "PREFERENCE"]
    assert preferences
    for item in preferences:
        assert item["type"] != "OBSERVED"
        assert "epistemic_origin" not in item


def test_no_company_brain_item_is_ever_classified_observed(monkeypatch) -> None:
    """T4: sweep every item type produced from real sources - none is ever
    an operational-truth classification."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY,
        aimx_department=POULTRY_DEPARTMENT,
        memory_facts=[NON_CONFLICTED_FACT, CONFLICTED_FACT],
    )
    truth_origins = {"observed", "derived", "inferred"}
    for item in result.items:
        assert item["type"] not in truth_origins
        assert item["type"] in {
            "POLICY",
            "PREFERENCE",
            "DECISION_RULE",
            "OPERATING_PRINCIPLE",
            "GOAL",
            "RISK_POSTURE",
            "MANAGEMENT_STANDARD",
            "INSTITUTIONAL_MEMORY",
        }


def test_operational_semantics_kept_separate_from_policy_items(monkeypatch) -> None:
    """T7 / Scenario I: Operational Semantics is terminology/meaning
    context, never folded into the policy/preference item list."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    result = cbc.assemble_company_brain_context(
        company=JANNAT_COMPANY, aimx_department=POULTRY_DEPARTMENT, memory_facts=[]
    )
    assert result.operational_semantics_topics
    # None of the classified items originate from the semantics document.
    assert not any(
        item.get("source") == "DAIRTNA_OPERATIONAL_SEMANTICS" for item in result.items
    )


def test_unrecognized_heading_is_skipped_not_guessed(monkeypatch) -> None:
    """Defensive: a heading with no entry in the classification map is
    never force-fit into a category (Founder instruction: do not invent
    policy)."""
    monkeypatch.setattr(
        cbc,
        "_read_document_cached",
        lambda path_str: "## مفهوم غير معروف\nنص تجريبي.\n" if "COMPANY_BRAIN" in path_str else "",
    )
    items = cbc._company_brain_document_items()
    assert items == []


# ---------------------------------------------------------------------------
# No evidence (T12, Scenario E)
# ---------------------------------------------------------------------------


def test_no_evidence_when_nothing_applicable() -> None:
    result = cbc.assemble_company_brain_context(
        company=OTHER_COMPANY, aimx_department=None, memory_facts=[]
    )
    assert result.status == "no_evidence"
    assert result.items == []
    assert result.operational_semantics_topics == []


# ---------------------------------------------------------------------------
# T13 - unexpected failure is visible/testable (never silently swallowed)
# ---------------------------------------------------------------------------


def test_unexpected_classification_failure_propagates(monkeypatch) -> None:
    def _boom(memory_facts):
        raise RuntimeError("synthetic unexpected Company Brain failure")

    monkeypatch.setattr(cbc, "_memory_fact_items", _boom)
    with pytest.raises(RuntimeError):
        cbc.assemble_company_brain_context(
            company=JANNAT_COMPANY, aimx_department=None, memory_facts=[]
        )


# ---------------------------------------------------------------------------
# decision_context.py wiring (T1, T2, T3, T4, T5, T6, T7, T8, T17)
# ---------------------------------------------------------------------------


SYNTHETIC_TRUTH_ITEMS = [
    {
        "type": "bird_balance",
        "status": "available",
        "epistemic_origin": "observed",
        "canonical_field": "bird_balance",
        "normalized_value": 12345,
        "entity_type": "production_hall",
        "entity_reference": "2",
        "source_time": "2026-06-01",
        "source_time_status": "authoritative",
    }
]
SYNTHETIC_BRAIN_ITEMS = [
    {
        "type": "DECISION_RULE",
        "key": "Production Reduction",
        "statement": "IF profitability declines THEN evaluate production reduction.",
        "scope": "company",
        "authority": "authoritative",
        "source": "DAIRTNA_DECISION_RULES",
        "source_type": "company_knowledge_document",
        "conflict_state": None,
        "provenance_note": None,
    },
    {
        "type": "PREFERENCE",
        "key": "فلسفة التوسع",
        "statement": "Gradual expansion based on actual results and clear profitability.",
        "scope": "company",
        "authority": "authoritative",
        "source": "DAIRTNA_COMPANY_BRAIN",
        "source_type": "company_knowledge_document",
        "conflict_state": None,
        "provenance_note": None,
    },
    {
        "type": "INSTITUTIONAL_MEMORY",
        "key": "target_market",
        "statement": "regional expansion",
        "scope": "company",
        "authority": "unresolved",
        "source": "memory_facts",
        "source_type": "memory_fact",
        "conflict_state": "conflicted",
        "provenance_note": "conflicting statements recorded across sessions",
    },
]
SYNTHETIC_SEMANTICS_TOPICS = ["الإنتاج", "الهلاكات والنفوق"]


def test_build_decision_context_carries_company_brain_context_key() -> None:
    decision_context = build_decision_context(
        context={},
        response_language="en",
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
        operational_semantics_topics=SYNTHETIC_SEMANTICS_TOPICS,
    )
    assert decision_context["company_brain_context"] == SYNTHETIC_BRAIN_ITEMS
    assert decision_context["operational_semantics_topics"] == SYNTHETIC_SEMANTICS_TOPICS


def test_company_brain_context_distinct_from_other_decision_context_keys() -> None:
    """T3 / T10: Company Brain never gets merged into Truth Context,
    memory_events, operational_events, or trends."""
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
    )
    assert decision_context["company_brain_context"] is not decision_context["operational_truth_context"]
    assert decision_context["company_brain_context"] != decision_context["operational_truth_context"]
    assert decision_context["company_brain_context"] is not decision_context["memory_events"]
    assert decision_context["company_brain_context"] is not decision_context["operational_events"]
    assert decision_context["company_brain_context"] is not decision_context["trends"]


def test_decision_context_backward_compatible_without_company_brain() -> None:
    """T17: the pre-M5 call signature still works and defaults cleanly."""
    decision_context = build_decision_context(context={}, response_language="en")
    assert decision_context["company_brain_context"] == []
    assert decision_context["operational_semantics_topics"] == []


def test_prompt_block_separates_truth_and_company_brain_sections() -> None:
    """T2 / T3 / Scenario C: both sections reach the prompt, distinctly."""
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
        operational_semantics_topics=SYNTHETIC_SEMANTICS_TOPICS,
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "[Operational Truth Context]" in block
    assert "[Company Brain Context]" in block
    truth_index = block.index("[Operational Truth Context]")
    brain_index = block.index("[Company Brain Context]")
    assert truth_index != brain_index


def test_prompt_block_never_labels_company_brain_item_as_observed() -> None:
    """T4."""
    decision_context = build_decision_context(
        context={}, response_language="en", company_brain_context=SYNTHETIC_BRAIN_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    brain_section = block[block.index("[Company Brain Context]") :]
    assert "Origin: OBSERVED" not in brain_section
    assert "epistemic_origin" not in brain_section.split("MANDATORY")[0]


def test_prompt_block_shows_decision_rule_and_preference_distinctly() -> None:
    """T5 / T6."""
    decision_context = build_decision_context(
        context={}, response_language="en", company_brain_context=SYNTHETIC_BRAIN_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "Type: DECISION_RULE" in block
    assert "Type: PREFERENCE" in block
    assert "Type: INSTITUTIONAL_MEMORY" in block


def test_prompt_block_shows_conflict_state_for_memory_fact() -> None:
    """T8 / Scenario D: a conflicted fact is not presented as uncontested."""
    decision_context = build_decision_context(
        context={}, response_language="en", company_brain_context=SYNTHETIC_BRAIN_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "Conflict: conflicted" in block
    assert "conflicting statements recorded across sessions" in block


def test_prompt_block_shows_operational_semantics_labeled_not_policy() -> None:
    """T7 / Scenario I."""
    decision_context = build_decision_context(
        context={},
        response_language="en",
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
        operational_semantics_topics=SYNTHETIC_SEMANTICS_TOPICS,
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "Operational Semantics topics (terminology/meaning context only, NOT policy/preference)" in block


def test_prompt_block_includes_company_brain_reasoning_rules() -> None:
    decision_context = build_decision_context(
        context={}, response_language="en", company_brain_context=SYNTHETIC_BRAIN_ITEMS
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "answer different questions and are never the same kind of statement" in block
    assert "must never override contradictory operational evidence" in block
    assert "state both and name the tension" in block
    assert "Do not invent Company Brain policy" in block


def test_prompt_block_empty_when_no_company_brain_items() -> None:
    decision_context = build_decision_context(context={}, response_language="en")
    block = build_decision_context_prompt_block(decision_context)
    assert "[Company Brain Context]" not in block


# ---------------------------------------------------------------------------
# AIService.chat() integration (T2, T9, T10, T13, T18)
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
    def __init__(self, company_row: dict | None) -> None:
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


def _service_with_fake_db(company_row: dict | None) -> tuple[AIService, _FakeOpenAIClient]:
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeDbPool(company_row)
    return service, fake_client


def test_chat_company_brain_not_configured_without_db_pool(monkeypatch) -> None:
    """T17 / T18: pre-M5 behavior (no db pool) is unaffected."""
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = False
    service.db_pool = None
    service.repo = None
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(session_id="cb1", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["status"] == "not_configured"
    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}


def test_chat_company_brain_ok_for_jannat_poultry_scope(monkeypatch) -> None:
    """T2 / T-I: real Company Brain content reaches the actual prompt text
    when the reasoning scope is explicitly Dairtna Poultry and
    JANNAT_COMPANY_ID matches the authenticated company."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb2",
            message="Status?",
            context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["status"] == "ok"
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is True
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "[Company Brain Context]" in prompt_text
    assert "Type: DECISION_RULE" in prompt_text


def test_chat_company_brain_excludes_dairtna_when_jannat_company_id_not_configured(monkeypatch) -> None:
    """F1-T1/F1-T7 (M5 live chat proof point): with JANNAT_COMPANY_ID
    unconfigured (the default), the real pilot tenant in its real Dairtna
    Poultry scope still gets NO Company Brain document content - fail
    closed, proven end to end through AIService.chat()."""
    assert otc.settings.JANNAT_COMPANY_ID == ""
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb2a",
            message="Status?",
            context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "Type: DECISION_RULE" not in prompt_text
    assert "Type: PREFERENCE" not in prompt_text


def test_chat_company_brain_excludes_dairtna_for_unresolved_ceo_scope(monkeypatch) -> None:
    """T-L (live chat proof point): a CEO/company-wide chat with no
    department selected must NOT receive Dairtna-specific docs by default,
    proven through the real AIService.chat() path, not just the assembler.
    Entitlement is configured explicitly so this isolates the applicability
    axis."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(session_id="cb2b", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    # Note: raw substrings "DAIRTNA_DECISION_RULES"/"DAIRTNA_COMPANY_BRAIN"
    # are not checked here - Truth Context (M4 Slice 2, unrelated to this
    # fix, correctly applicable for aimx_department=None) legitimately
    # surfaces a presence-only evidence item referencing that file path.
    # "Type: DECISION_RULE"/"Type: PREFERENCE" only ever render from the
    # Company Brain section (_build_company_brain_section), so their
    # absence is the precise signal that no Company Brain document content
    # reached the prompt.
    assert "Type: DECISION_RULE" not in prompt_text
    assert "Type: PREFERENCE" not in prompt_text


def test_chat_company_brain_excludes_dairtna_for_spoofed_tenant_name(monkeypatch) -> None:
    """F1-T8 (live chat proof point): a company whose name/slug merely
    contains "Jannat"/"Firdaws" text must not receive Dairtna knowledge
    through the real AIService.chat() path, even with JANNAT_COMPANY_ID
    configured to the real pilot id (its own id still won't match)."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(SPOOFED_NAME_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb2c",
            message="Status?",
            context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "DAIRTNA_DECISION_RULES" not in prompt_text
    assert "DAIRTNA_COMPANY_BRAIN" not in prompt_text


def test_chat_company_brain_excludes_dairtna_for_other_tenant(monkeypatch) -> None:
    """T9 / Scenario F: tenant isolation holds through the live chat path,
    even with JANNAT_COMPANY_ID configured to the real pilot id (a
    different company's id still won't match)."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(OTHER_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(session_id="cb3", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "DAIRTNA_DECISION_RULES" not in prompt_text
    assert "DAIRTNA_COMPANY_BRAIN" not in prompt_text


def test_chat_company_brain_department_scoped_non_poultry_excludes_dairtna(monkeypatch) -> None:
    """T10 / Scenario G."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb4",
            message="Status?",
            context={"aimx_department": SALES_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False


def test_chat_company_brain_excludes_dairtna_for_caesar_beverage_scope(monkeypatch) -> None:
    """T-J (live chat proof point)."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb4b",
            message="Status?",
            context={"aimx_department": CAESAR_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False


def test_chat_company_brain_excludes_dairtna_for_shared_corporate_scope(monkeypatch) -> None:
    """T-K (live chat proof point)."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb4c",
            message="Status?",
            context={"aimx_department": SHARED_CORPORATE_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False


def test_chat_company_brain_unexpected_failure_degrades_gracefully(monkeypatch) -> None:
    """T13."""
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    def _boom(**kwargs):
        raise RuntimeError("synthetic unexpected Company Brain failure")

    monkeypatch.setattr("app.services.openai_client.assemble_company_brain_context", _boom)

    result = asyncio.run(
        service.chat(session_id="cb5", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["status"] == "error"
    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}


def test_chat_truth_and_company_brain_both_reach_prompt_together(monkeypatch) -> None:
    """Scenario C: both sections present simultaneously for the pilot tenant
    in its Dairtna Poultry scope."""
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    service, fake_client = _service_with_fake_db(JANNAT_COMPANY)
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    result = asyncio.run(
        service.chat(
            session_id="cb6",
            message="Status?",
            context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "ok"
    assert result["meta"]["context"]["company_brain_bridge"]["status"] == "ok"
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "[Operational Truth Context]" in prompt_text
    assert "[Company Brain Context]" in prompt_text
