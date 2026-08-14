"""M7 Slice 2A: public explainability contract + meta.context privacy
allowlist + Arabic/English reasoning-prose contract tests.

Backend explainability tests (E1-E15) exercise app/services/
explainability.py both as a direct unit (deterministic, fast, full control
over the reference catalog) and, for the final-candidate placement/leak
-prevention guarantee specifically (E10/E11), through the REAL
AIService.chat() candidate lifecycle - only the LLM call itself is faked
(matching tests/test_m6_reasoning_layer.py's established convention), no
validator is ever bypassed.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
from types import SimpleNamespace
from uuid import uuid4

from app.services import operational_truth_context as otc
from app.services.decision_context import (
    build_decision_context,
    public_context_allowlist,
    reasoning_language_contract,
)
from app.services.explainability import (
    CONFIDENCE_BAND_HIGH,
    CONFIDENCE_BAND_LOW,
    CONFIDENCE_BAND_MODERATE,
    DRIVER_CONFLICTED_COMPANY_BASIS,
    DRIVER_MISSING_EVIDENCE,
    DRIVER_UNRESOLVED_SOURCE_TIME,
    build_public_explainability,
)
from app.services.openai_client import AIService, _build_operational_regeneration_instruction
from app.services.operational_truth_context import TruthContextResult
from app.services.company_brain_context import CompanyBrainResult
from app.services.reasoning_validation import build_reasoning_assessment_repair_instruction

JANNAT_COMPANY_ID = uuid4()
JANNAT_COMPANY = {"id": JANNAT_COMPANY_ID, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}
POULTRY_DEPARTMENT = {"name": "Dairtna Poultry", "department_type": "poultry_ai", "slug": "dairtna-poultry"}

# T1 usable OBSERVED, full provenance; T2 usable DERIVED, unresolved source
# time; T3 missing (gap, never cited below); T4 INFERRED-only (never usable,
# never cited below).
TRUTH_ITEMS = [
    {
        "type": "bird_balance", "status": "available", "epistemic_origin": "observed",
        "canonical_field": "bird_balance", "normalized_value": 998,
        "entity_type": "production_hall", "entity_reference": "2",
        "source_time": "2026-06-01", "source_time_status": "authoritative",
        "source_filename": "hall2_daily_report.xlsx",
        "source_file_id": "b6e6b8f0-1111-2222-3333-444455556666",
        "source_company_id": "aaaa0000-1111-2222-3333-444455556666",
        "source_department_id": "cccc0000-1111-2222-3333-444455556666",
    },
    {
        "type": "production_trend", "status": "available", "epistemic_origin": "derived",
        "canonical_field": "daily_production_rate", "normalized_value": 74.2,
        "entity_type": "production_hall", "entity_reference": "2",
        "source_time": None, "source_time_status": "unresolved",
        "source_filename": "hall2_daily_report.xlsx",
    },
    {
        "type": "water_consumption", "status": "missing", "epistemic_origin": None,
        "canonical_field": None, "normalized_value": None, "entity_type": None,
        "source_time": None, "source_time_status": None,
    },
    {
        "type": "possible_cause_hypothesis", "status": "available", "epistemic_origin": "inferred",
        "canonical_field": None, "normalized_value": None, "entity_type": "production_hall",
        "entity_reference": "2", "source_time": None, "source_time_status": "unresolved",
    },
]

# CB1 settled POLICY (citable); CB2 conflicted PREFERENCE (never settled,
# never citable).
BRAIN_ITEMS = [
    {
        "type": "POLICY", "key": "Feed sourcing priority",
        "statement": "Prefer local feed suppliers to reduce lead time.",
        "scope": "company", "authority": "authoritative", "source": "DAIRTNA_COMPANY_BRAIN",
        "source_type": "company_knowledge_document", "conflict_state": None, "provenance_note": None,
    },
    {
        "type": "PREFERENCE", "key": "target_market", "statement": "regional expansion",
        "scope": "company", "authority": "unresolved", "source": "memory_facts",
        "source_type": "memory_fact", "conflict_state": "conflicted", "provenance_note": "conflicting records",
    },
]


def _decision_context(*, truth_items=None, brain_items=None) -> dict:
    return build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=TRUTH_ITEMS if truth_items is None else truth_items,
        company_brain_context=BRAIN_ITEMS if brain_items is None else brain_items,
    )


def _assessment(**overrides) -> dict:
    base = {
        "reasoning_state": "aligned",
        "operational_assessment": "Hall 2 readings reviewed.",
        "company_brain_alignment": "supported by current evidence",
        "tensions": [],
        "evidence_gaps": [],
        "risk_assessment": "Low.",
        "confidence": 70,
        "recommendation_basis": {"evidence_basis": [], "company_basis": [], "missing_evidence": []},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# E1-E9: build_public_explainability unit tests (deterministic reference
# catalog, full control over cited vs. uncited items)
# ---------------------------------------------------------------------------


def test_e1_cited_valid_t_ref_produces_exactly_one_safe_evidence_summary() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert len(result["cited_evidence"]) == 1
    item = result["cited_evidence"][0]
    assert item["id"] == "e1"
    assert item["label"] == "bird_balance"
    assert item["filename"] == "hall2_daily_report.xlsx"
    assert item["report_date"] == "2026-06-01"
    assert item["entity"] == {"type": "production_hall", "reference": "2"}
    assert item["epistemic_origin"] == "observed"
    assert item["source_time_status"] == "authoritative"
    assert set(item.keys()) == {"id", "label", "filename", "report_date", "entity", "epistemic_origin", "source_time_status"}


def test_e2_uncited_truth_items_do_not_appear() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    labels = [item["label"] for item in result["cited_evidence"]]
    assert "daily_production_rate" not in labels  # T2 not cited
    assert "water_consumption" not in labels  # T3 not cited
    assert len(result["cited_evidence"]) == 1


def test_e3_cited_valid_cb_ref_produces_exactly_one_safe_company_basis_summary() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert len(result["cited_company_basis"]) == 1
    item = result["cited_company_basis"][0]
    assert item["id"] == "c1"
    assert item["label"] == "Feed sourcing priority"
    assert item["type"] == "POLICY"
    assert item["statement"] == "Prefer local feed suppliers to reduce lead time."
    assert set(item.keys()) == {"id", "label", "type", "statement"}


def test_e4_uncited_company_brain_items_do_not_appear() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    statements = [item["statement"] for item in result["cited_company_basis"]]
    assert "regional expansion" not in statements  # CB2 (conflicted) never appears
    assert len(result["cited_company_basis"]) == 1


def test_e5_invalid_nonexistent_refs_do_not_fabricate_summaries() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T99"], "company_basis": ["CB99"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert result["cited_evidence"] == []
    assert result["cited_company_basis"] == []


def test_e5b_uncited_but_existing_unusable_refs_never_summarized() -> None:
    """T3 (missing) and T4 (inferred-only) exist in the catalog but are
    never usable evidence - even if a malformed candidate somehow cited
    them, they must not produce a summary (fail-closed, Section 7)."""
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T3", "T4"], "company_basis": ["CB2"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert result["cited_evidence"] == []
    assert result["cited_company_basis"] == []


def test_e6_internal_uuid_path_provenance_does_not_leak() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    serialized = json.dumps(result)
    assert "source_file_id" not in serialized
    assert "source_company_id" not in serialized
    assert "source_department_id" not in serialized
    assert "b6e6b8f0-1111-2222-3333-444455556666" not in serialized
    assert "aaaa0000-1111-2222-3333-444455556666" not in serialized
    assert "cccc0000-1111-2222-3333-444455556666" not in serialized


def test_e7_unresolved_source_time_remains_unresolved() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T2"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert len(result["cited_evidence"]) == 1
    item = result["cited_evidence"][0]
    assert item["source_time_status"] == "unresolved"
    assert item["report_date"] is None  # never substituted with "now"/ingestion time


def test_e8_safe_display_values_derived_from_real_provenance_not_fabricated() -> None:
    truth_items = [dict(TRUTH_ITEMS[0])]
    del truth_items[0]["source_filename"]  # simulate no filename available
    decision_context = _decision_context(truth_items=truth_items)
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert result["cited_evidence"][0]["filename"] is None  # omitted, never invented


def test_e9_no_t_or_cb_refs_emitted_in_public_explainability() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    for item in result["cited_evidence"]:
        assert item["id"].startswith("e") and item["id"][1:].isdigit()
        assert "ref" not in item
    for item in result["cited_company_basis"]:
        assert item["id"].startswith("c") and item["id"][1:].isdigit()
        assert "ref" not in item
    serialized = json.dumps(result)
    assert '"T1"' not in serialized
    assert '"CB1"' not in serialized


# ---------------------------------------------------------------------------
# F4-A..E (Correction Round 1, 2A-F4): authoritative reference resolution.
# Proves T#/CB# resolve through reasoning_reference_catalog's own
# internal_source_item snapshot - captured at catalog-creation time - and
# NEVER by re-indexing operational_truth_context/company_brain_context by
# the ref's numeric suffix. Adversarially reorders those lists AFTER the
# catalog already exists to prove resolution is immune to it.
# ---------------------------------------------------------------------------


def test_f4a_truth_list_reordering_after_catalog_creation_does_not_misattribute() -> None:
    truth_items = [dict(item) for item in TRUTH_ITEMS]
    decision_context = _decision_context(truth_items=truth_items)
    catalog = decision_context["reasoning_reference_catalog"]
    assert catalog["truth"]["T1"]["internal_source_item"]["canonical_field"] == "bird_balance"

    # Adversarially reverse the SAME list object the catalog was built from,
    # after catalog creation - simulates a caller reordering/rebuilding
    # operational_truth_context later in the turn.
    truth_items.reverse()
    assert decision_context["operational_truth_context"][0]["canonical_field"] != "bird_balance"

    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    # T1 still means the item that ORIGINALLY earned T1 - not whatever now
    # sits at index 0 after the reorder (that would be T4's item, inferred-
    # only and never usable evidence in the first place).
    assert len(result["cited_evidence"]) == 1
    assert result["cited_evidence"][0]["label"] == "bird_balance"
    # F4-D: still no T#/CB# in the public payload.
    serialized = json.dumps(result)
    assert '"T1"' not in serialized
    # F4-E: still no UUID/path provenance.
    assert "source_file_id" not in serialized
    assert "b6e6b8f0-1111-2222-3333-444455556666" not in serialized


def test_f4b_company_brain_list_reordering_after_catalog_creation_does_not_misattribute() -> None:
    brain_items = [dict(item) for item in BRAIN_ITEMS]
    decision_context = _decision_context(brain_items=brain_items)
    catalog = decision_context["reasoning_reference_catalog"]
    assert catalog["company_brain"]["CB1"]["internal_source_item"]["key"] == "Feed sourcing priority"

    brain_items.reverse()
    assert decision_context["company_brain_context"][0]["key"] != "Feed sourcing priority"

    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert len(result["cited_company_basis"]) == 1
    assert result["cited_company_basis"][0]["label"] == "Feed sourcing priority"
    serialized = json.dumps(result)
    assert '"CB1"' not in serialized


def test_f4c_missing_internal_snapshot_fails_closed_never_falls_back_to_list_position() -> None:
    """If a catalog entry somehow lacks a usable internal_source_item, the
    citation must be dropped - never resolved by falling back to indexing
    into operational_truth_context/company_brain_context by position."""
    decision_context = _decision_context()
    del decision_context["reasoning_reference_catalog"]["truth"]["T1"]["internal_source_item"]
    del decision_context["reasoning_reference_catalog"]["company_brain"]["CB1"]["internal_source_item"]

    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert result["cited_evidence"] == []
    assert result["cited_company_basis"] == []


def test_f4e_no_internal_snapshot_or_uuid_path_leaks_in_reordered_scenario() -> None:
    truth_items = [dict(item) for item in TRUTH_ITEMS]
    brain_items = [dict(item) for item in BRAIN_ITEMS]
    decision_context = _decision_context(truth_items=truth_items, brain_items=brain_items)
    truth_items.reverse()
    brain_items.reverse()

    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    serialized = json.dumps(result)
    assert "internal_source_item" not in serialized
    assert "source_file_id" not in serialized
    assert "source_company_id" not in serialized
    assert "source_department_id" not in serialized
    assert "b6e6b8f0-1111-2222-3333-444455556666" not in serialized
    assert "aaaa0000-1111-2222-3333-444455556666" not in serialized
    assert "cccc0000-1111-2222-3333-444455556666" not in serialized


# ---------------------------------------------------------------------------
# E12-E15: confidence derivation
# ---------------------------------------------------------------------------


def test_e12_confidence_value_matches_final_m6_confidence() -> None:
    decision_context = _decision_context()
    assessment = _assessment(confidence=83)
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["confidence"]["value"] == 83


def test_e13_confidence_band_is_deterministic() -> None:
    decision_context = _decision_context()
    cases = [(0, CONFIDENCE_BAND_LOW), (39, CONFIDENCE_BAND_LOW), (40, CONFIDENCE_BAND_MODERATE),
             (69, CONFIDENCE_BAND_MODERATE), (70, CONFIDENCE_BAND_HIGH), (100, CONFIDENCE_BAND_HIGH)]
    for value, expected_band in cases:
        assessment = _assessment(confidence=value)
        result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
        assert result["confidence"]["band"] == expected_band, f"value={value}"


def test_e14_confidence_drivers_are_deterministic_closed_enum_codes() -> None:
    decision_context = _decision_context()

    # missing_evidence driver: recommendation_basis.missing_evidence non-empty.
    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T3"]}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert DRIVER_MISSING_EVIDENCE in result["confidence"]["drivers"]

    # unresolved_source_time driver: a cited evidence ref has unresolved source time (T2).
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T2"], "company_basis": [], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert DRIVER_UNRESOLVED_SOURCE_TIME in result["confidence"]["drivers"]

    # conflicted_company_basis driver: this turn's Company Brain catalog has
    # a conflicted item (CB2), regardless of citation.
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert DRIVER_CONFLICTED_COMPANY_BASIS in result["confidence"]["drivers"]

    # No drivers when nothing warrants one.
    decision_context_clean = _decision_context(
        truth_items=[TRUTH_ITEMS[0]], brain_items=[BRAIN_ITEMS[0]]
    )
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context_clean)
    assert result["confidence"]["drivers"] == []


def test_e15_no_confidence_driver_is_invented_from_prose() -> None:
    decision_context = _decision_context(truth_items=[TRUTH_ITEMS[0]], brain_items=[BRAIN_ITEMS[0]])
    assessment = _assessment(
        operational_assessment="This is definitely certain and there is absolutely no risk whatsoever.",
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []},
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    allowed_drivers = {DRIVER_MISSING_EVIDENCE, DRIVER_UNRESOLVED_SOURCE_TIME, DRIVER_CONFLICTED_COMPANY_BASIS}
    assert set(result["confidence"]["drivers"]).issubset(allowed_drivers)
    assert result["confidence"]["drivers"] == []  # prose never adds a driver


# ---------------------------------------------------------------------------
# E10/E11: final-candidate placement guarantee, through the REAL
# AIService.chat() candidate lifecycle. Only the LLM call is faked -
# matching tests/test_m6_reasoning_layer.py's established convention.
# ---------------------------------------------------------------------------


class _FakeChatCompletions:
    def __init__(self, responses: list[str]) -> None:
        self.messages: list = []
        self._responses = list(responses)

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        content = self._responses.pop(0) if self._responses else "{}"
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class _FakeOpenAIClient:
    def __init__(self, responses: list[str]) -> None:
        self.chat_completions = _FakeChatCompletions(responses)
        self.chat = SimpleNamespace(completions=self.chat_completions)


class _FakeDbPool:
    def __init__(self, company_row: dict | None) -> None:
        self._company_row = company_row

    async def fetchrow(self, query, *args):
        return self._company_row


def _raw_decision(reasoning_assessment: dict | None) -> dict:
    payload: dict = {
        "context_lock": {"missing_fields": [], "is_locked": False, "confidence": 0, "why": ""},
        "problem_classification": {"type": "", "confidence": 0, "why": ""},
        "truth_validation": {"contradictions": [], "trust_score": 0, "notes": ""},
        "root_cause_engine": {"root_causes": [], "why_chain": []},
        "solution_generator": {"urgent_30_days": [], "mid_term_90_days": [], "long_term_6_12_months": []},
        "execution_engine": {"priority_order": [], "quick_wins": [], "high_impact_moves": [], "dependencies": [], "risks": []},
    }
    if reasoning_assessment is not None:
        payload["reasoning_assessment"] = reasoning_assessment
    return payload


def _chat_json(*, reasoning_assessment: dict | None) -> str:
    return json.dumps({
        "executive_summary": "Executive Summary\n- Reviewed.\n\nRecommended Actions\n- Monitor.\n\nPriority Level\n- Medium.",
        "raw_decision": _raw_decision(reasoning_assessment),
    })


def _service_with_synthetic_m4_m5(monkeypatch, responses: list[str]) -> tuple[AIService, _FakeOpenAIClient]:
    def _fake_assemble_truth_context(*, company, aimx_department, uploaded_records=None):
        return TruthContextResult(status="ok", evidence_count=len(TRUTH_ITEMS), items=TRUTH_ITEMS)

    def _fake_assemble_company_brain_context(*, company, aimx_department, memory_facts):
        return CompanyBrainResult(
            status="ok", item_count=len(BRAIN_ITEMS), items=BRAIN_ITEMS,
            operational_semantics_topics=[], dairtna_knowledge_included=True,
        )

    monkeypatch.setattr("app.services.openai_client.assemble_truth_context", _fake_assemble_truth_context)
    monkeypatch.setattr("app.services.openai_client.assemble_company_brain_context", _fake_assemble_company_brain_context)

    service = AIService()
    fake_client = _FakeOpenAIClient(responses)
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeDbPool(JANNAT_COMPANY)
    return service, fake_client


def _configure_jannat_company_id(monkeypatch, company_id: object) -> None:
    monkeypatch.setattr(otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID=str(company_id)))


def test_e10_only_final_accepted_candidate_refs_appear(monkeypatch) -> None:
    """A fully valid first response: explainability reflects exactly its
    own citations."""
    valid_response = _chat_json(
        reasoning_assessment=_assessment(
            recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
        )
    )
    service, _fake_client = _service_with_synthetic_m4_m5(monkeypatch, [valid_response])

    result = asyncio.run(
        service.chat(
            session_id="e10", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    explainability = result["meta"]["context"]["explainability"]
    assert len(explainability["cited_evidence"]) == 1
    assert explainability["cited_evidence"][0]["label"] == "bird_balance"
    assert len(explainability["cited_company_basis"]) == 1
    assert explainability["cited_company_basis"][0]["label"] == "Feed sourcing priority"


def test_e11_rejected_repaired_candidate_refs_never_leak(monkeypatch) -> None:
    """First candidate is M6-invalid (cites a nonexistent T#); the repair
    candidate cites something different (T2 instead of the invalid ref).
    Public explainability must reflect ONLY the final, repaired candidate -
    never anything from the rejected first attempt."""
    invalid_first_response = _chat_json(
        reasoning_assessment=_assessment(
            recommendation_basis={"evidence_basis": ["T99"], "company_basis": [], "missing_evidence": []}
        )
    )
    repaired_response = _chat_json(
        reasoning_assessment=_assessment(
            recommendation_basis={"evidence_basis": ["T2"], "company_basis": [], "missing_evidence": []}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [invalid_first_response, repaired_response]
    )

    result = asyncio.run(
        service.chat(
            session_id="e11", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    # Two real model calls happened: the rejected first attempt, then the repair.
    assert len(fake_client.chat_completions.messages) == 2

    explainability = result["meta"]["context"]["explainability"]
    labels = [item["label"] for item in explainability["cited_evidence"]]
    assert labels == ["daily_production_rate"]  # T2's label - the REPAIRED candidate's citation
    assert result["logic_json"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] == ["T2"]


# ---------------------------------------------------------------------------
# F1-A..G (Correction Round 1, 2A-F1): the reasoning-language contract
# (prose language + company_brain_alignment controlled vocabulary) must be
# present in EVERY candidate-generation path - initial prompt, legacy
# retry, operational regeneration, and M6 repair - not only the initial
# prompt. F1-D uses the REAL chat() runtime (only the LLM call faked) to
# prove the actual messages sent on a legacy-retry, not just a standalone
# builder function.
# ---------------------------------------------------------------------------


def _joined_content(messages: list[dict]) -> str:
    return "\n".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))


def _invalid_legacy_chat_json(*, reasoning_assessment: dict) -> str:
    """A candidate that fails _validate_execution_structure (an execution
    item far too short/generic) - forces the legacy retry path to fire."""
    raw_decision = _raw_decision(reasoning_assessment)
    raw_decision["solution_generator"] = {
        "urgent_30_days": ["Fix it"], "mid_term_90_days": [], "long_term_6_12_months": [],
    }
    raw_decision["execution_engine"] = {
        "priority_order": [], "quick_wins": [], "high_impact_moves": [], "dependencies": [], "risks": [],
    }
    return json.dumps({
        "executive_summary": "Executive Summary\n- x\n\nRecommended Actions\n- x\n\nPriority Level\n- Medium.",
        "raw_decision": raw_decision,
    })


def test_f1a_initial_prompt_contains_the_shared_reasoning_language_contract() -> None:
    from app.services.decision_context import (
        build_decision_context_prompt_block,
        company_brain_alignment_vocabulary_instruction,
        reasoning_prose_language_instruction,
    )

    decision_context = build_decision_context(context={"response_language": "ar"}, response_language="ar")
    block = build_decision_context_prompt_block(decision_context)
    # The initial prompt keeps its two pieces at their original, separated
    # positions (unrelated content sits between them - see
    # build_decision_context_prompt_block) - each piece must still be the
    # SAME shared-helper output the repair/regeneration/retry paths use.
    assert reasoning_prose_language_instruction("ar") in block
    assert company_brain_alignment_vocabulary_instruction("ar") in block


def test_f1b_m6_repair_prompt_contains_arabic_reasoning_binding() -> None:
    instruction = build_reasoning_assessment_repair_instruction(
        errors=["recommendation_basis.evidence_basis: 'T99' was not supplied"], response_language="ar"
    )
    assert reasoning_language_contract("ar") in instruction


def test_f1c_operational_regeneration_prompt_contains_arabic_reasoning_binding() -> None:
    instruction = _build_operational_regeneration_instruction(
        missing_elements=["operational_events"], response_language="ar"
    )
    assert reasoning_language_contract("ar") in instruction


def test_f1d_legacy_retry_path_repeats_full_reasoning_language_contract(monkeypatch) -> None:
    """The legacy execution-structure retry can become the final candidate
    - the ACTUAL retry_messages sent to the model (not just the initial
    prompt this list was built from) must carry the full contract."""
    invalid_first_response = _invalid_legacy_chat_json(reasoning_assessment=_assessment())
    valid_retry_response = _chat_json(reasoning_assessment=_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [invalid_first_response, valid_retry_response]
    )

    asyncio.run(
        service.chat(
            session_id="f1d", message="Status?",
            context={"aimx_department": POULTRY_DEPARTMENT, "response_language": "ar"},
            company_id=str(uuid4()),
        )
    )

    # Two real model calls: the legacy-invalid first attempt, then the retry.
    assert len(fake_client.chat_completions.messages) == 2
    retry_text = _joined_content(fake_client.chat_completions.messages[1])
    assert reasoning_language_contract("ar") in retry_text


def test_f1e_arabic_controlled_vocabulary_appears_in_every_candidate_path() -> None:
    from app.services.decision_context import build_decision_context_prompt_block

    arabic_phrases = ["مدعوم بالأدلة الحالية", "غير مدعوم بالأدلة الحالية", "مدعوم جزئيًا", "لا يمكن التحديد"]

    decision_context = build_decision_context(context={"response_language": "ar"}, response_language="ar")
    initial_block = build_decision_context_prompt_block(decision_context)
    repair_instruction = build_reasoning_assessment_repair_instruction(errors=["x"], response_language="ar")
    regeneration_instruction = _build_operational_regeneration_instruction(
        missing_elements=["y"], response_language="ar"
    )

    for phrase in arabic_phrases:
        assert phrase in initial_block
        assert phrase in repair_instruction
        assert phrase in regeneration_instruction


def test_f1f_english_controlled_vocabulary_unchanged_and_arabic_absent_from_english_paths() -> None:
    english_phrases = [
        "'supported by current evidence'", "'not supported by current evidence'",
        "'partially supported'", "'cannot determine'",
    ]
    repair_instruction = build_reasoning_assessment_repair_instruction(errors=["x"], response_language="en")
    regeneration_instruction = _build_operational_regeneration_instruction(
        missing_elements=["y"], response_language="en"
    )
    for phrase in english_phrases:
        assert phrase in repair_instruction
        assert phrase in regeneration_instruction
    assert "مدعوم بالأدلة الحالية" not in repair_instruction
    assert "مدعوم بالأدلة الحالية" not in regeneration_instruction


def test_f1g_reasoning_state_enum_stays_english_and_is_never_translated() -> None:
    contract_ar = reasoning_language_contract("ar")
    assert "reasoning_state stays the exact English enum value" in contract_ar
    assert "aligned" in contract_ar and "tension" in contract_ar and "insufficient_evidence" in contract_ar

    from app.services.decision_context import (
        REASONING_STATE_ALIGNED,
        REASONING_STATE_INSUFFICIENT_EVIDENCE,
        REASONING_STATE_TENSION,
    )

    assert REASONING_STATE_ALIGNED == "aligned"
    assert REASONING_STATE_TENSION == "tension"
    assert REASONING_STATE_INSUFFICIENT_EVIDENCE == "insufficient_evidence"


# ---------------------------------------------------------------------------
# Section 19: meta.context public allowlist
# ---------------------------------------------------------------------------


def test_allowlist_keeps_only_the_six_approved_groups_plus_explainability() -> None:
    context = {
        "operational_events_bridge": {"status": "ok"},
        "truth_context_bridge": {"status": "ok"},
        "company_brain_bridge": {"status": "ok"},
        "company_intelligence_profile": {"company_name": "Acme"},
        "decision_context": {
            "department": {"key": "ceo", "name": "CEO", "scope": "company_wide"},
            "operational_events": [{"summary": "x"}],
            "operational_truth_context": [{"leaked": True}],
            "company_brain_context": [{"leaked": True}],
            "reasoning_reference_catalog": {"truth": {}},
            "reasoning_signals": {"truth_available": True},
            "organizational_intelligence": {"leaked": True},
            "key_kpis": {"leaked": True},
        },
        "explainability": {"cited_evidence": [], "cited_company_basis": [], "confidence": None},
        # Everything below must be dropped entirely.
        "nawa_role": {"slug": "ceo"},
        "rag_knowledge_available": True,
        "latest_raw_input_id": "raw-123",
        "aimx_department": {"id": "dept-1"},
        "stage": "Enterprise expansion",
    }

    public = public_context_allowlist(context)

    assert set(public.keys()) == {
        "operational_events_bridge", "truth_context_bridge", "company_brain_bridge",
        "company_intelligence_profile", "decision_context", "explainability",
    }
    assert set(public["decision_context"].keys()) == {"department", "operational_events"}
    serialized = json.dumps(public)
    assert "reasoning_reference_catalog" not in serialized
    assert "reasoning_signals" not in serialized
    assert "operational_truth_context" not in serialized
    assert "company_brain_context" not in serialized
    assert "organizational_intelligence" not in serialized
    assert "key_kpis" not in serialized
    assert "nawa_role" not in serialized
    assert "rag_knowledge_available" not in serialized
    assert "latest_raw_input_id" not in serialized
    assert "stage" not in serialized


def test_allowlist_omits_absent_keys_rather_than_inventing_null_values() -> None:
    public = public_context_allowlist({"truth_context_bridge": {"status": "ok"}})
    assert public == {"truth_context_bridge": {"status": "ok"}}


def test_allowlist_handles_non_dict_input_safely() -> None:
    assert public_context_allowlist(None) == {}  # type: ignore[arg-type]
    assert public_context_allowlist({}) == {}


def test_full_chat_response_meta_context_matches_allowlist(monkeypatch) -> None:
    """End-to-end proof through the real chat() path: no internal UUID/path
    provenance, no full Truth/Company Brain catalogs, no reasoning_reference_
    catalog/reasoning_signals reach the public response."""
    response = _chat_json(
        reasoning_assessment=_assessment(
            recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []}
        )
    )
    service, _fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(
            session_id="allowlist-e2e", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    public_context = result["meta"]["context"]
    assert set(public_context.keys()).issubset(
        {"operational_events_bridge", "truth_context_bridge", "company_brain_bridge",
         "company_intelligence_profile", "decision_context", "explainability"}
    )
    serialized = json.dumps(public_context)
    assert "reasoning_reference_catalog" not in serialized
    assert "reasoning_signals" not in serialized
    assert "b6e6b8f0-1111-2222-3333-444455556666" not in serialized
    assert "source_file_id" not in serialized
    assert "operational_truth_context" not in public_context.get("decision_context", {})
    assert "company_brain_context" not in public_context.get("decision_context", {})


# ---------------------------------------------------------------------------
# Section 20 (AR1-AR5): Arabic/English prompt contract - proves the
# INSTRUCTION is present in the real prompt text; cannot prove a real
# external model always obeys it (documented as a Golden Pilot runtime QA
# item, not a deterministic guarantee - see decision_context.py's own
# comment at the same lines).
# ---------------------------------------------------------------------------


def test_ar1_arabic_response_language_instructs_reasoning_prose_in_arabic() -> None:
    decision_context = build_decision_context(context={"response_language": "ar"}, response_language="ar")
    from app.services.decision_context import build_decision_context_prompt_block

    block = build_decision_context_prompt_block(decision_context)
    assert "response_language for this turn is 'ar'" in block
    assert "write operational_assessment, tensions, evidence_gaps" in block
    assert "in Arabic" in block


def test_ar2_arabic_company_brain_alignment_controlled_vocabulary_is_exact() -> None:
    decision_context = build_decision_context(context={"response_language": "ar"}, response_language="ar")
    from app.services.decision_context import build_decision_context_prompt_block

    block = build_decision_context_prompt_block(decision_context)
    assert "مدعوم بالأدلة الحالية" in block
    assert "غير مدعوم بالأدلة الحالية" in block
    assert "مدعوم جزئيًا" in block
    assert "لا يمكن التحديد" in block


def test_ar3_english_response_language_preserves_exact_english_vocabulary() -> None:
    decision_context = build_decision_context(context={"response_language": "en"}, response_language="en")
    from app.services.decision_context import build_decision_context_prompt_block

    block = build_decision_context_prompt_block(decision_context)
    assert "'supported by current evidence'" in block
    assert "'not supported by current evidence'" in block
    assert "'partially supported'" in block
    assert "'cannot determine'" in block
    # Arabic controlled vocabulary must NOT appear when response_language=en.
    assert "مدعوم بالأدلة الحالية" not in block
    assert "response_language for this turn is 'ar'" not in block
    assert "response_language for this turn is 'en'" in block


def test_ar4_reasoning_state_enum_names_unchanged() -> None:
    from app.services.decision_context import (
        REASONING_STATE_ALIGNED,
        REASONING_STATE_INSUFFICIENT_EVIDENCE,
        REASONING_STATE_TENSION,
    )

    assert REASONING_STATE_ALIGNED == "aligned"
    assert REASONING_STATE_TENSION == "tension"
    assert REASONING_STATE_INSUFFICIENT_EVIDENCE == "insufficient_evidence"


def test_ar5_reference_id_and_confidence_semantics_unchanged() -> None:
    from app.services.reasoning_validation import ReasoningAssessment

    fields = ReasoningAssessment.model_fields
    assert "confidence" in fields
    assert "recommendation_basis" in fields
    # StrictInt behavior (no coercion) is already covered by
    # tests/test_m6_reasoning_layer.py's L14/L15 - this only reconfirms the
    # field still exists and evidence_basis/company_basis/missing_evidence
    # remain the exact recommendation_basis sub-fields.
    from app.services.reasoning_validation import RecommendationBasis

    basis_fields = RecommendationBasis.model_fields
    assert set(basis_fields.keys()) == {"evidence_basis", "company_basis", "missing_evidence"}
