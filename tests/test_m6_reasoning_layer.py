"""M6 (AI Reasoning Layer) acceptance tests - Correction Round 1.

M6 reasons ACROSS Operational Truth Context (M4, "what is happening") and
Company Brain Context (M5, "what the company believes/prefers/requires").
This round makes that a RUNTIME-ENFORCED contract, not prompt-only
guidance:

- raw_decision.reasoning_assessment is validated structurally (Pydantic:
  required fields, exact reasoning_state enum, confidence bounds) AND
  against decision provenance (every recommendation_basis reference must
  be a real T#/CB# id actually supplied this turn - see
  app/services/reasoning_validation.py and
  app/services/decision_context.py's reasoning_reference_catalog).
- reasoning_signals now mean USABLE evidence / SETTLED company policy,
  never mere row presence (M6-F2).
- Live chat tests use the REAL legacy validator, the REAL M6 validator,
  and the REAL formatter - only the LLM call itself is faked (M6-F3).
- Internal reasoning_signals/reasoning_reference_catalog never reach the
  public API response; only the model-generated logic_json.reasoning_
  assessment does (M6-F5/Part 6).

No external LLM is called anywhere in this file.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.decision_prompt import AIMX_DECISION_PROMPT
from app.services import company_brain_context as cbc
from app.services import decision_context as dc
from app.services import operational_truth_context as otc
from app.services.company_brain_context import CompanyBrainResult
from app.services.decision_context import (
    REASONING_STATE_ALIGNED,
    REASONING_STATE_INSUFFICIENT_EVIDENCE,
    REASONING_STATE_TENSION,
    build_decision_context,
    build_decision_context_prompt_block,
    public_decision_context,
)
from app.services.openai_client import (
    AIService,
    _operational_response_missing_elements,
    _validate_execution_structure,
)
from app.services.operational_truth_context import TruthContextResult
from app.services.reasoning_validation import validate_reasoning_assessment

JANNAT_COMPANY_ID = uuid4()
JANNAT_COMPANY = {
    "id": JANNAT_COMPANY_ID,
    "slug": "jannat-al-firdaws",
    "name": "Jannat Al-Firdaws",
    "metadata": {},
}
OTHER_COMPANY = {"id": uuid4(), "slug": "acme-fmcg", "name": "Acme FMCG", "metadata": {}}
POULTRY_DEPARTMENT = {"name": "Dairtna Poultry", "department_type": "poultry_ai", "slug": "dairtna-poultry"}
CAESAR_DEPARTMENT = {"name": "Caesar Beverage", "department_type": "production_ai", "slug": "caesar-beverage"}


def _configure_jannat_company_id(monkeypatch: pytest.MonkeyPatch, company_id: object) -> None:
    monkeypatch.setattr(otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID=str(company_id)))


# ---------------------------------------------------------------------------
# Synthetic M4/M5 fixtures with deterministic T#/CB# indices:
#   T1 usable OBSERVED   T2 usable DERIVED   T3 missing (gap)
#   T4 unresolved source time (gap, still AVAILABLE/OBSERVED - Feed Mill case)
#   T5 INFERRED-only (not usable evidence)
#   CB1 settled PREFERENCE   CB2 conflicted INSTITUTIONAL_MEMORY (not settled)
#   CB3 settled RISK_POSTURE
# ---------------------------------------------------------------------------

SYNTHETIC_TRUTH_ITEMS = [
    {
        "type": "bird_balance", "status": "available", "epistemic_origin": "observed",
        "canonical_field": "bird_balance", "normalized_value": 12345,
        "entity_type": "production_hall", "entity_reference": "2",
        "source_time": "2026-06-01", "source_time_status": "authoritative",
    },
    {
        "type": "production_trend", "status": "available", "epistemic_origin": "derived",
        "canonical_field": "daily_production_rate", "normalized_value": None,
        "entity_type": "production_hall", "entity_reference": "2",
        "source_time": "2026-06-03", "source_time_status": "authoritative",
    },
    {
        "type": "water_consumption", "status": "missing", "epistemic_origin": None,
        "canonical_field": None, "normalized_value": None, "entity_type": None,
        "source_time": None, "source_time_status": None,
    },
    {
        "type": "raw_material_inventory", "status": "available", "epistemic_origin": "observed",
        "canonical_field": None, "normalized_value": None, "entity_type": "feed_mill",
        "entity_reference": None, "source_time": None, "source_time_status": "unresolved",
    },
    {
        "type": "possible_cause_hypothesis", "status": "available", "epistemic_origin": "inferred",
        "canonical_field": None, "normalized_value": None, "entity_type": "production_hall",
        "entity_reference": "2", "source_time": None, "source_time_status": "unresolved",
    },
]

SYNTHETIC_BRAIN_ITEMS = [
    {
        "type": "PREFERENCE", "key": "فلسفة التوسع",
        "statement": "Gradual expansion based on actual results and clear profitability.",
        "scope": "company", "authority": "authoritative", "source": "DAIRTNA_COMPANY_BRAIN",
        "source_type": "company_knowledge_document", "conflict_state": None, "provenance_note": None,
    },
    {
        "type": "INSTITUTIONAL_MEMORY", "key": "target_market", "statement": "regional expansion",
        "scope": "company", "authority": "unresolved", "source": "memory_facts",
        "source_type": "memory_fact", "conflict_state": "conflicted",
        "provenance_note": "conflicting statements recorded across sessions",
    },
    {
        "type": "RISK_POSTURE", "key": "فلسفة المخاطرة",
        "statement": "Accept calculated risks that do not threaten liquidity or continuity.",
        "scope": "company", "authority": "authoritative", "source": "DAIRTNA_COMPANY_BRAIN",
        "source_type": "company_knowledge_document", "conflict_state": None, "provenance_note": None,
    },
]


# ---------------------------------------------------------------------------
# PART 3 - reasoning_signals semantics (S1-S10)
# ---------------------------------------------------------------------------


def _signals_for(truth_items, brain_items):
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=truth_items,
        company_brain_context=brain_items,
    )
    return decision_context["reasoning_signals"]


def test_s1_only_missing_truth_not_available() -> None:
    signals = _signals_for([SYNTHETIC_TRUTH_ITEMS[2]], [])  # T3 missing
    assert signals["truth_available"] is False


def test_s2_only_invalid_unavailable_truth_not_available() -> None:
    signals = _signals_for([{"type": "x", "status": "unrecognized_status", "epistemic_origin": "observed"}], [])
    assert signals["truth_available"] is False


def test_s3_only_inferred_truth_not_available() -> None:
    signals = _signals_for([SYNTHETIC_TRUTH_ITEMS[4]], [])  # T5 inferred-only
    assert signals["truth_available"] is False
    assert signals["inferred_context_count"] == 1


def test_s4_observed_truth_available() -> None:
    signals = _signals_for([SYNTHETIC_TRUTH_ITEMS[0]], [])  # T1 observed
    assert signals["truth_available"] is True


def test_s5_derived_truth_available() -> None:
    signals = _signals_for([SYNTHETIC_TRUTH_ITEMS[1]], [])  # T2 derived
    assert signals["truth_available"] is True


def test_s6_only_institutional_memory_policy_unavailable() -> None:
    non_conflicted_memory = {**SYNTHETIC_BRAIN_ITEMS[1], "conflict_state": None, "authority": "institutional"}
    signals = _signals_for([], [non_conflicted_memory])
    assert signals["company_brain_policy_available"] is False


def test_s7_only_conflicted_policy_unavailable() -> None:
    conflicted_policy = {**SYNTHETIC_BRAIN_ITEMS[0], "conflict_state": "conflicted"}
    signals = _signals_for([], [conflicted_policy])
    assert signals["company_brain_policy_available"] is False
    assert signals["conflicted_company_brain_policy_count"] == 1


def test_s8_only_unresolved_authority_preference_unavailable() -> None:
    unresolved_authority_preference = {**SYNTHETIC_BRAIN_ITEMS[0], "authority": "unresolved"}
    signals = _signals_for([], [unresolved_authority_preference])
    assert signals["company_brain_policy_available"] is False


def test_s9_settled_preference_available() -> None:
    signals = _signals_for([], [SYNTHETIC_BRAIN_ITEMS[0]])  # CB1 settled
    assert signals["company_brain_policy_available"] is True


def test_s10_settled_plus_conflicted_available_with_conflict_count() -> None:
    signals = _signals_for([], [SYNTHETIC_BRAIN_ITEMS[0], SYNTHETIC_BRAIN_ITEMS[1]])  # CB1 settled + CB2 conflicted
    assert signals["company_brain_policy_available"] is True
    assert signals["conflicted_company_brain_policy_count"] == 1
    assert signals["settled_company_brain_policy_count"] == 1


def test_full_synthetic_fixture_signal_counts() -> None:
    signals = _signals_for(SYNTHETIC_TRUTH_ITEMS, SYNTHETIC_BRAIN_ITEMS)
    assert signals["truth_context_item_count"] == 5
    # T1 (observed), T2 (derived), T4 (observed, Feed Mill - unresolved
    # source time does not disqualify it as usable evidence, Part 11).
    assert signals["usable_truth_evidence_count"] == 3
    assert signals["inferred_context_count"] == 1
    assert signals["missing_evidence_count"] == 1
    # T5 (inferred hypothesis) also carries source_time_status=unresolved in
    # this fixture, but must NOT be counted here: unresolved_source_time_count
    # is a freshness-claim risk about USABLE evidence (T4, Feed Mill) - an
    # inferred hypothesis was never asserted as current fact, so its own
    # timestamp state is a separate, unrelated concern (see
    # test_inferred_item_unresolved_time_not_counted_as_freshness_risk).
    assert signals["unresolved_source_time_count"] == 1
    assert signals["truth_available"] is True
    assert signals["company_brain_context_item_count"] == 3
    assert signals["settled_company_brain_policy_count"] == 2
    assert signals["conflicted_company_brain_policy_count"] == 1
    assert signals["company_brain_policy_available"] is True
    assert signals["both_layers_present"] is True


# ---------------------------------------------------------------------------
# Reference catalog + prompt rendering (Part 1.1 / Part 4 / Part 5)
# ---------------------------------------------------------------------------


def test_reference_catalog_indices_match_render_order() -> None:
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
    )
    catalog = decision_context["reasoning_reference_catalog"]
    assert catalog["truth"]["T1"]["is_usable_evidence"] is True
    assert catalog["truth"]["T3"]["is_missing"] is True
    assert catalog["truth"]["T3"]["is_gap_reference"] is True
    assert catalog["truth"]["T4"]["is_unresolved_time"] is True
    assert catalog["truth"]["T4"]["is_gap_reference"] is True
    assert catalog["truth"]["T5"]["is_inferred"] is True
    assert catalog["truth"]["T5"]["is_usable_evidence"] is False
    assert catalog["company_brain"]["CB1"]["is_settled"] is True
    assert catalog["company_brain"]["CB2"]["is_settled"] is False
    assert catalog["company_brain"]["CB2"]["is_conflicted"] is True
    assert catalog["company_brain"]["CB3"]["is_settled"] is True


def test_inferred_item_unresolved_time_not_counted_as_freshness_risk() -> None:
    """T5 is INFERRED with source_time_status=unresolved, but it was never
    asserted as current evidence in the first place - unresolved_source_time
    tracking (and missing_evidence gap-eligibility) must stay scoped to
    USABLE evidence (the Feed Mill Golden Case), not to a hypothesis merely
    lacking a timestamp."""
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=SYNTHETIC_TRUTH_ITEMS
    )
    catalog = decision_context["reasoning_reference_catalog"]
    assert catalog["truth"]["T5"]["is_unresolved_time"] is False
    assert catalog["truth"]["T5"]["is_gap_reference"] is False
    # T5 cannot be cited as missing_evidence - it is neither missing nor a
    # freshness-risk on usable evidence, just an unconfirmed hypothesis.
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T5"]})
        ),
        decision_context,
    )
    assert ok is False


def test_prompt_sections_label_each_item_with_its_reference_id() -> None:
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
    )
    block = build_decision_context_prompt_block(decision_context)
    assert "[T1] Claim: bird_balance" in block
    assert "[T3] Claim: water_consumption" in block
    assert "[CB1] Type: PREFERENCE" in block
    assert "[CB2] Type: INSTITUTIONAL_MEMORY" in block


def test_rules_require_reference_ids_not_prose_citations() -> None:
    decision_context = build_decision_context(context={}, response_language="en")
    block = build_decision_context_prompt_block(decision_context)
    assert "recommendation_basis.evidence_basis may ONLY cite a T# that is USABLE evidence" in block
    assert "recommendation_basis.company_basis may ONLY cite a CB# that is AUTHORITATIVE settled company doctrine" in block
    assert "never cite a prose source" in block


def test_decision_prompt_forbids_inventing_references() -> None:
    assert "NEVER invent a reference ID" in AIMX_DECISION_PROMPT
    assert "evidence_basis: ONLY T# reference IDs" in AIMX_DECISION_PROMPT
    assert "company_basis: ONLY CB# reference IDs" in AIMX_DECISION_PROMPT


# ---------------------------------------------------------------------------
# PART 6 - internal metadata must not leak by default (M6-F5)
# ---------------------------------------------------------------------------


def test_public_decision_context_strips_internal_m6_keys() -> None:
    decision_context = build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
    )
    public = public_decision_context(decision_context)
    assert "reasoning_signals" not in public
    assert "reasoning_reference_catalog" not in public
    # Everything else (including operational_truth_context/company_brain_context
    # themselves, already public since M4/M5) is preserved unchanged.
    assert public["operational_truth_context"] == SYNTHETIC_TRUTH_ITEMS
    assert public["company_brain_context"] == SYNTHETIC_BRAIN_ITEMS


# ---------------------------------------------------------------------------
# PART 1 / PART 7 - real validator: V1-V8 (structural)
# ---------------------------------------------------------------------------


def _decision_context_with_refs() -> dict:
    return build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
    )


def _valid_assessment(**overrides) -> dict:
    base = {
        "reasoning_state": "aligned",
        "operational_assessment": "Evidence reviewed.",
        "company_brain_alignment": "supported by current evidence",
        "tensions": [],
        "evidence_gaps": [],
        "risk_assessment": "Low.",
        "confidence": 70,
        # M8 Slice 4B: organizational_memory_basis is now a required
        # RecommendationBasis field (empty by default - no live Slice 4B
        # scenario is under test in this M6-focused file).
        "recommendation_basis": {
            "evidence_basis": ["T1"],
            "company_basis": ["CB1"],
            "missing_evidence": [],
            "organizational_memory_basis": [],
        },
    }
    base.update(overrides)
    # M8 Slice 4B: organizational_memory_basis is a required
    # RecommendationBasis field. Many call sites in this file override
    # recommendation_basis wholesale (e.g.
    # _valid_assessment(recommendation_basis={"evidence_basis": [...], ...}))
    # without knowing about the new field - back-fill it here, in the one
    # shared helper, rather than editing every individual call site.
    if "organizational_memory_basis" not in base["recommendation_basis"]:
        base["recommendation_basis"] = {**base["recommendation_basis"], "organizational_memory_basis": []}
    return base


def _parsed_with_assessment(assessment) -> dict:
    return {"raw_decision": {"reasoning_assessment": assessment}}


def test_v1_old_response_no_reasoning_assessment_fails() -> None:
    ok, errors = validate_reasoning_assessment({"raw_decision": {}}, _decision_context_with_refs())
    assert ok is False
    assert errors


def test_v2_reasoning_assessment_null_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        {"raw_decision": {"reasoning_assessment": None}}, _decision_context_with_refs()
    )
    assert ok is False


def test_v3_reasoning_assessment_empty_object_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        {"raw_decision": {"reasoning_assessment": {}}}, _decision_context_with_refs()
    )
    assert ok is False


def test_v4_invalid_reasoning_state_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment(reasoning_state="banana")), _decision_context_with_refs()
    )
    assert ok is False
    assert any("reasoning_state" in e for e in errors)


def test_v5_confidence_out_of_bounds_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment(confidence=999)), _decision_context_with_refs()
    )
    assert ok is False
    assert any("confidence" in e for e in errors)


def test_v6_confidence_wrong_type_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment(confidence="high")), _decision_context_with_refs()
    )
    assert ok is False
    assert any("confidence" in e for e in errors)


def test_v7_recommendation_basis_missing_fails() -> None:
    assessment = _valid_assessment()
    del assessment["recommendation_basis"]
    ok, errors = validate_reasoning_assessment(_parsed_with_assessment(assessment), _decision_context_with_refs())
    assert ok is False
    assert any("recommendation_basis" in e for e in errors)


def test_v8_evidence_basis_string_instead_of_list_fails() -> None:
    assessment = _valid_assessment()
    assessment["recommendation_basis"] = {"evidence_basis": "T1", "company_basis": [], "missing_evidence": []}
    ok, errors = validate_reasoning_assessment(_parsed_with_assessment(assessment), _decision_context_with_refs())
    assert ok is False


# ---------------------------------------------------------------------------
# M6-R3 (Correction Round 2) - strict confidence type: V9-V21
# ---------------------------------------------------------------------------


def _confidence_check(confidence) -> bool:
    ok, _ = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment(confidence=confidence)), _decision_context_with_refs()
    )
    return ok


def test_v9_confidence_string_fails() -> None:
    assert _confidence_check("50") is False


def test_v10_confidence_true_fails() -> None:
    assert _confidence_check(True) is False


def test_v11_confidence_false_fails() -> None:
    assert _confidence_check(False) is False


def test_v17_confidence_non_integer_float_fails() -> None:
    assert _confidence_check(50.5) is False


def test_v18_confidence_zero_passes() -> None:
    assert _confidence_check(0) is True


def test_v19_confidence_hundred_passes() -> None:
    assert _confidence_check(100) is True


def test_v20_confidence_negative_fails() -> None:
    assert _confidence_check(-1) is False


def test_v21_confidence_above_hundred_fails() -> None:
    assert _confidence_check(101) is False


def test_v1_v8_not_weakened_reasoning_state_numeric_fails() -> None:
    ok, _ = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment(reasoning_state=1)), _decision_context_with_refs()
    )
    assert ok is False


def test_v1_v8_not_weakened_tensions_wrong_element_type_fails() -> None:
    assessment = _valid_assessment()
    assessment["tensions"] = [123]
    ok, _ = validate_reasoning_assessment(_parsed_with_assessment(assessment), _decision_context_with_refs())
    assert ok is False


def test_v1_v8_not_weakened_evidence_basis_element_wrong_type_fails() -> None:
    assessment = _valid_assessment()
    assessment["recommendation_basis"] = {"evidence_basis": [1], "company_basis": [], "missing_evidence": []}
    ok, _ = validate_reasoning_assessment(_parsed_with_assessment(assessment), _decision_context_with_refs())
    assert ok is False


def test_v1_v8_not_weakened_operational_assessment_none_fails() -> None:
    ok, _ = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment(operational_assessment=None)), _decision_context_with_refs()
    )
    assert ok is False


def test_v1_v8_not_weakened_unexpected_nested_field_fails() -> None:
    assessment = _valid_assessment()
    assessment["chain_of_thought"] = "step 1, step 2"
    ok, _ = validate_reasoning_assessment(_parsed_with_assessment(assessment), _decision_context_with_refs())
    assert ok is False


def test_valid_reasoning_assessment_passes() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(_valid_assessment()), _decision_context_with_refs()
    )
    assert ok is True
    assert errors == []


# ---------------------------------------------------------------------------
# PART 7.2 - provenance validation P1-P7
# ---------------------------------------------------------------------------


def test_p1_valid_existing_refs_pass() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(
                recommendation_basis={"evidence_basis": ["T1", "T2"], "company_basis": ["CB1"], "missing_evidence": ["T3"]}
            )
        ),
        _decision_context_with_refs(),
    )
    assert ok is True


def test_p2_nonexistent_truth_ref_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": ["T999"], "company_basis": [], "missing_evidence": []})
        ),
        _decision_context_with_refs(),
    )
    assert ok is False
    assert any("T999" in e for e in errors)


def test_p3_evidence_basis_wrong_namespace_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": ["CB1"], "company_basis": [], "missing_evidence": []})
        ),
        _decision_context_with_refs(),
    )
    assert ok is False


def test_p4_company_basis_wrong_namespace_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": ["T1"], "missing_evidence": []})
        ),
        _decision_context_with_refs(),
    )
    assert ok is False


def test_p5_missing_evidence_references_available_non_gap_fails() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T1"]})
        ),
        _decision_context_with_refs(),
    )
    assert ok is False


def test_p6_missing_evidence_references_real_gap_passes() -> None:
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T3"]})
        ),
        _decision_context_with_refs(),
    )
    assert ok is True
    ok2, _ = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T4"]})
        ),
        _decision_context_with_refs(),
    )
    assert ok2 is True


def test_p7_company_basis_conflicted_ref_fails_safer_behavior() -> None:
    """CB2 structurally exists but is conflicted/unresolved - the safer
    bounded behavior (spec-directed) is to reject its use as settled
    company_basis outright, not attempt semantic proof of how the model
    used it."""
    ok, errors = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": ["CB2"], "missing_evidence": []})
        ),
        _decision_context_with_refs(),
    )
    assert ok is False


# ---------------------------------------------------------------------------
# M6-R1/M6-R2 (Correction Round 2) - P8-P21
# ---------------------------------------------------------------------------


def _dc_for(*, truth_items=None, brain_items=None) -> dict:
    return build_decision_context(
        context={},
        response_language="en",
        operational_truth_context=truth_items or [],
        company_brain_context=brain_items or [],
    )


UNAVAILABLE_TRUTH_ITEM = {
    "type": "some_reading", "status": "unavailable", "epistemic_origin": "observed",
    "canonical_field": None, "normalized_value": None, "entity_type": None,
    "source_time": None, "source_time_status": None,
}


def _evidence_basis_check(truth_items, ref: str) -> bool:
    ok, _ = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [ref], "company_basis": [], "missing_evidence": []})
        ),
        _dc_for(truth_items=truth_items),
    )
    return ok


def test_p8_missing_t_in_evidence_basis_fails() -> None:
    assert _evidence_basis_check([SYNTHETIC_TRUTH_ITEMS[2]], "T1") is False  # T3 (missing) is index-1 T1 here


def test_p9_inferred_only_t_in_evidence_basis_fails() -> None:
    assert _evidence_basis_check([SYNTHETIC_TRUTH_ITEMS[4]], "T1") is False  # T5 (inferred) is index-1 T1 here


def test_p10_invalid_unavailable_t_in_evidence_basis_fails() -> None:
    assert _evidence_basis_check([UNAVAILABLE_TRUTH_ITEM], "T1") is False


def test_p11_usable_observed_t_in_evidence_basis_passes() -> None:
    assert _evidence_basis_check([SYNTHETIC_TRUTH_ITEMS[0]], "T1") is True  # T1 observed


def test_p12_usable_derived_t_in_evidence_basis_passes() -> None:
    assert _evidence_basis_check([SYNTHETIC_TRUTH_ITEMS[1]], "T1") is True  # T2 derived


def test_p13_usable_observed_with_unresolved_source_time_passes() -> None:
    """Feed Mill Golden Case: unresolved freshness does not disqualify
    otherwise-usable evidence from evidence_basis (Part 11 / R1)."""
    assert _evidence_basis_check([SYNTHETIC_TRUTH_ITEMS[3]], "T1") is True  # T4 feed mill


def _company_basis_check(brain_item: dict) -> bool:
    ok, _ = validate_reasoning_assessment(
        _parsed_with_assessment(
            _valid_assessment(recommendation_basis={"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []})
        ),
        _dc_for(brain_items=[brain_item]),
    )
    return ok


def test_p14_institutional_memory_fails_as_company_basis() -> None:
    item = {**SYNTHETIC_BRAIN_ITEMS[1], "authority": "authoritative", "conflict_state": None}
    assert _company_basis_check(item) is False


def test_p15_policy_with_authority_none_fails() -> None:
    item = {**SYNTHETIC_BRAIN_ITEMS[0], "authority": None}
    assert _company_basis_check(item) is False


def test_p16_policy_with_authority_unknown_fails() -> None:
    item = {**SYNTHETIC_BRAIN_ITEMS[0], "authority": "unknown"}
    assert _company_basis_check(item) is False


def test_p17_policy_with_authority_institutional_fails() -> None:
    item = {**SYNTHETIC_BRAIN_ITEMS[0], "authority": "institutional"}
    assert _company_basis_check(item) is False


def test_p18_policy_authority_unresolved_fails() -> None:
    item = {**SYNTHETIC_BRAIN_ITEMS[0], "authority": "unresolved"}
    assert _company_basis_check(item) is False


def test_p19_conflicted_authoritative_policy_fails() -> None:
    item = {**SYNTHETIC_BRAIN_ITEMS[0], "authority": "authoritative", "conflict_state": "conflicted"}
    assert _company_basis_check(item) is False


def test_p20_authoritative_settled_policy_passes() -> None:
    assert _company_basis_check(SYNTHETIC_BRAIN_ITEMS[0]) is True  # PREFERENCE, authoritative, unconflicted


def test_p21_authoritative_settled_risk_posture_passes() -> None:
    assert _company_basis_check(SYNTHETIC_BRAIN_ITEMS[2]) is True  # RISK_POSTURE, authoritative, unconflicted


# ---------------------------------------------------------------------------
# PART 8 - live fake-LLM tests with REAL validation (L1-L8)
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
    payload = {
        "context_lock": {"missing_fields": [], "is_locked": False, "confidence": 0, "why": ""},
        "problem_classification": {"type": "", "confidence": 0, "why": ""},
        "truth_validation": {"contradictions": [], "trust_score": 0, "notes": ""},
        "root_cause_engine": {"root_causes": [], "why_chain": []},
        "solution_generator": {"urgent_30_days": [], "mid_term_90_days": [], "long_term_6_12_months": []},
        "execution_engine": {
            "priority_order": [], "quick_wins": [], "high_impact_moves": [], "dependencies": [], "risks": []
        },
    }
    if reasoning_assessment is not None:
        payload["reasoning_assessment"] = reasoning_assessment
    return payload


def _chat_json(*, executive_summary: str = "Executive Summary\n- Reviewed.\n\nRecommended Actions\n- Monitor.\n\nPriority Level\n- Medium.", reasoning_assessment: dict | None) -> str:
    return json.dumps({"executive_summary": executive_summary, "raw_decision": _raw_decision(reasoning_assessment)})


def _service_with_synthetic_m4_m5(monkeypatch, responses: list[str], *, truth_items=None, brain_items=None) -> tuple[AIService, _FakeOpenAIClient]:
    """Real AIService.chat(), real legacy validator, real M6 validator, real
    formatter - only the LLM call and the M4/M5 assembly functions are
    faked, so reference IDs are fully deterministic (T1.. from truth_items,
    CB1.. from brain_items) without depending on real pilot file content."""
    truth_items = SYNTHETIC_TRUTH_ITEMS if truth_items is None else truth_items
    brain_items = SYNTHETIC_BRAIN_ITEMS if brain_items is None else brain_items

    def _fake_assemble_truth_context(*, company, aimx_department, uploaded_records=None):
        return TruthContextResult(
            status="ok" if truth_items else "no_evidence",
            evidence_count=len(truth_items),
            items=truth_items,
        )

    def _fake_assemble_company_brain_context(*, company, aimx_department, memory_facts):
        return CompanyBrainResult(
            status="ok" if brain_items else "no_evidence",
            item_count=len(brain_items),
            items=brain_items,
            operational_semantics_topics=[],
            dairtna_knowledge_included=bool(brain_items),
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


def test_l1_fully_valid_response_accepted_and_reasoning_assessment_preserved(monkeypatch) -> None:
    valid_response = _chat_json(
        reasoning_assessment=_valid_assessment(
            reasoning_state="aligned",
            recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": []},
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [valid_response])

    result = asyncio.run(
        service.chat(
            session_id="l1", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"
    assert result["logic_json"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] == ["T1"]
    assert len(fake_client.chat_completions.messages) == 1  # no repair needed


def test_l2_missing_reasoning_assessment_then_valid_repair_accepted(monkeypatch) -> None:
    pre_m6_response = _chat_json(reasoning_assessment=None)
    valid_repair = _chat_json(reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [pre_m6_response, valid_repair])

    result = asyncio.run(
        service.chat(
            session_id="l2", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"
    assert len(fake_client.chat_completions.messages) == 2  # initial + repair


def test_l3_invalid_state_first_then_valid_repair_accepted(monkeypatch) -> None:
    invalid_state_response = _chat_json(reasoning_assessment=_valid_assessment(reasoning_state="banana"))
    valid_repair = _chat_json(reasoning_assessment=_valid_assessment(reasoning_state="tension"))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [invalid_state_response, valid_repair])

    result = asyncio.run(
        service.chat(
            session_id="l3", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "tension"


def test_l4_invalid_both_attempts_fails_closed_not_malformed_decision(monkeypatch) -> None:
    invalid_response = _chat_json(reasoning_assessment=None)
    still_invalid_repair = _chat_json(reasoning_assessment=_valid_assessment(confidence=999))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [invalid_response, still_invalid_repair])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.chat(
                session_id="l4", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
            )
        )
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2  # initial + one repair attempt, then fail closed


def test_l5_insufficient_evidence_with_root_cause_not_established_accepted(monkeypatch) -> None:
    """Part 2: a CEO-scope response declaring insufficient_evidence and
    stating the root cause is not established must NOT be forced into
    inventing a confident bottleneck - it should be accepted as-is."""
    response = _chat_json(
        executive_summary=(
            "Executive Summary\n"
            "- Root cause not established; evidence required to determine cause. "
            "Production and inventory impact under review.\n\n"
            "Recommended Actions\n- Collect missing water and veterinary evidence.\n\n"
            "Priority Level\n- Medium."
        ),
        reasoning_assessment=_valid_assessment(
            reasoning_state="insufficient_evidence",
            recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T3", "T4"]},
        ),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(session_id="l5", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "insufficient_evidence"
    # No regeneration was forced - the insufficient-evidence carve-out held.
    assert len(fake_client.chat_completions.messages) == 1


# ---------------------------------------------------------------------------
# M6-R4 (Correction Round 2) - Arabic-first / structured-state insufficient
# evidence carve-out: A1-A5. The carve-out is driven ONLY by the raw
# reasoning_state field (language-independent) - never by matching an
# English phrase dictionary - and only exempts "root operational
# bottleneck"/"cause/effect chain"; "affected departments"/"operational
# impact" (unrelated, untouched requirements) still apply, so A1/A2/A5
# include department/impact-bearing text to isolate the root-cause fix
# specifically.
# ---------------------------------------------------------------------------


def test_a1_english_insufficient_evidence_no_operational_regeneration(monkeypatch) -> None:
    response = _chat_json(
        executive_summary=(
            "Executive Summary\n"
            "- Root cause not established; evidence required to determine cause. "
            "Production and inventory impact under review.\n\n"
            "Recommended Actions\n- Collect missing evidence.\n\nPriority Level\n- Medium."
        ),
        reasoning_assessment=_valid_assessment(reasoning_state="insufficient_evidence"),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])
    asyncio.run(service.chat(session_id="a1", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 1


def test_a2_arabic_insufficient_evidence_no_operational_regeneration(monkeypatch) -> None:
    """M6-R4: the carve-out must be language-independent. This Arabic
    executive_summary contains NONE of the old English insufficient-
    evidence phrase list ("root cause not established", "hypothes", etc.) -
    if the carve-out still depended on matching those phrases, this would
    incorrectly trigger operational regeneration."""
    response = _chat_json(
        executive_summary=(
            "الملخص التنفيذي\n"
            "- لا توجد أدلة كافية لتحديد السبب الجذري حاليًا في قسم production، "
            "ونحتاج بيانات إضافية عن inventory قبل تأكيد السبب.\n\n"
            "الإجراءات الموصى بها\n- جمع البيانات الناقصة.\n\nمستوى الأولوية\n- متوسط."
        ),
        reasoning_assessment=_valid_assessment(reasoning_state="insufficient_evidence"),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])
    asyncio.run(service.chat(session_id="a2", message="ما الوضع؟", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 1


def test_a3_insufficient_evidence_with_empty_root_causes_accepted(monkeypatch) -> None:
    response = _chat_json(reasoning_assessment=_valid_assessment(reasoning_state="insufficient_evidence"))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])
    result = asyncio.run(
        service.chat(
            session_id="a3", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    # root_cause_engine.root_causes is empty in _raw_decision() by construction - accepted regardless.
    assert result["logic_json"]["root_cause_engine"]["root_causes"] == []
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "insufficient_evidence"


def test_a4_insufficient_evidence_hypotheses_only_accepted(monkeypatch) -> None:
    response = _chat_json(
        reasoning_assessment=_valid_assessment(
            reasoning_state="insufficient_evidence",
            evidence_gaps=["feed quality data", "veterinary records"],
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])
    result = asyncio.run(
        service.chat(
            session_id="a4", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["evidence_gaps"] == ["feed quality data", "veterinary records"]


def test_a5_aligned_state_still_requires_root_cause_language(monkeypatch) -> None:
    """The R4 fix must not disable root-cause quality checks for
    aligned/tension - only insufficient_evidence gets the carve-out. A CEO
    response with a generic, non-operational executive_summary and
    reasoning_state=aligned must still be forced through legacy operational
    regeneration."""
    generic_first = _chat_json(
        executive_summary=(
            "Executive Summary\n- There are challenges and performance should improve.\n\n"
            "Recommended Actions\n- Focus on efficiency.\n\nPriority Level\n- Medium."
        ),
        reasoning_assessment=_valid_assessment(reasoning_state="aligned"),
    )
    operational_repair = _chat_json(
        executive_summary=(
            "Executive Summary\n- Root operational bottleneck: production capacity is constraining "
            "output.\n- Cause/effect chain: reduced line speed drives lower throughput.\n"
            "- Affected departments: Production, Sales.\n- Operational impact: fulfillment and inventory "
            "are at risk.\n\nRecommended Actions\n- Production: restore line speed within 48 hours.\n\n"
            "Priority Level\n- High."
        ),
        reasoning_assessment=_valid_assessment(reasoning_state="aligned"),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [generic_first, operational_repair])
    asyncio.run(service.chat(session_id="a5", message="Status?", context={}, company_id=str(uuid4())))
    # Legacy operational-response enforcement still fired (2 calls) even
    # though reasoning_state=aligned was structurally valid both times -
    # the carve-out never applies outside insufficient_evidence.
    assert len(fake_client.chat_completions.messages) == 2


def test_l6_tension_state_accepted(monkeypatch) -> None:
    response = _chat_json(reasoning_assessment=_valid_assessment(reasoning_state="tension"))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(
            session_id="l6", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "tension"


def test_l7_aligned_state_accepted(monkeypatch) -> None:
    response = _chat_json(reasoning_assessment=_valid_assessment(reasoning_state="aligned"))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(
            session_id="l7", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"


def test_l8_fake_nonexistent_provenance_repaired_to_valid(monkeypatch) -> None:
    fabricated_reference_response = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T999"], "company_basis": [], "missing_evidence": []}
        )
    )
    valid_repair = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [fabricated_reference_response, valid_repair])

    result = asyncio.run(
        service.chat(
            session_id="l8", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] == ["T1"]


def test_l8b_fake_provenance_fails_closed_when_repair_also_fabricates(monkeypatch) -> None:
    fabricated_reference_response = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T999"], "company_basis": [], "missing_evidence": []}
        )
    )
    still_fabricated_repair = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T888"], "company_basis": [], "missing_evidence": []}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [fabricated_reference_response, still_fabricated_repair])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.chat(
                session_id="l8b", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
            )
        )
    assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# Correction Round 2 live runtime tests: L9-L15
# ---------------------------------------------------------------------------


def test_l9_missing_t_as_evidence_basis_triggers_repair(monkeypatch) -> None:
    missing_as_evidence = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T3"], "company_basis": [], "missing_evidence": []}
        )
    )
    valid_repair = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": ["T3"]}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [missing_as_evidence, valid_repair])

    result = asyncio.run(
        service.chat(
            session_id="l9", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] == ["T1"]


def test_l10_repair_also_uses_missing_t_fails_closed(monkeypatch) -> None:
    missing_as_evidence = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T3"], "company_basis": [], "missing_evidence": []}
        )
    )
    still_missing_as_evidence = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": ["T3"], "company_basis": [], "missing_evidence": []}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [missing_as_evidence, still_missing_as_evidence])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.chat(
                session_id="l10", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
            )
        )
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2


def test_l11_non_authoritative_company_basis_triggers_repair(monkeypatch) -> None:
    non_authoritative_brain_items = [{**SYNTHETIC_BRAIN_ITEMS[0], "authority": "institutional"}]
    non_authoritative_response = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []}
        )
    )
    valid_repair = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": []}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [non_authoritative_response, valid_repair], brain_items=non_authoritative_brain_items
    )

    result = asyncio.run(
        service.chat(
            session_id="l11", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["recommendation_basis"]["company_basis"] == []


def test_l12_repair_uses_authoritative_settled_company_basis_accepted(monkeypatch) -> None:
    non_authoritative_brain_items = [{**SYNTHETIC_BRAIN_ITEMS[0], "authority": "institutional"}, SYNTHETIC_BRAIN_ITEMS[2]]
    non_authoritative_response = _chat_json(
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []}
        )
    )
    valid_repair = _chat_json(
        # CB2 in this fixture is SYNTHETIC_BRAIN_ITEMS[2] (RISK_POSTURE, authoritative, unconflicted).
        reasoning_assessment=_valid_assessment(
            recommendation_basis={"evidence_basis": [], "company_basis": ["CB2"], "missing_evidence": []}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [non_authoritative_response, valid_repair], brain_items=non_authoritative_brain_items
    )

    result = asyncio.run(
        service.chat(
            session_id="l12", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["logic_json"]["reasoning_assessment"]["recommendation_basis"]["company_basis"] == ["CB2"]


def test_l13_arabic_insufficient_evidence_exactly_one_model_call(monkeypatch) -> None:
    response = _chat_json(
        executive_summary=(
            "الملخص التنفيذي\n"
            "- لا توجد أدلة كافية لتحديد السبب الجذري حاليًا في قسم production، "
            "ونحتاج بيانات إضافية عن inventory قبل تأكيد السبب.\n\n"
            "الإجراءات الموصى بها\n- جمع البيانات الناقصة.\n\nمستوى الأولوية\n- متوسط."
        ),
        reasoning_assessment=_valid_assessment(reasoning_state="insufficient_evidence"),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(session_id="l13", message="ما الوضع؟", context={}, company_id=str(uuid4()))
    )
    assert len(fake_client.chat_completions.messages) == 1
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "insufficient_evidence"


def test_l14_strict_confidence_string_triggers_repair(monkeypatch) -> None:
    string_confidence_response = _chat_json(reasoning_assessment=_valid_assessment(confidence="50"))
    valid_repair = _chat_json(reasoning_assessment=_valid_assessment(confidence=50))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [string_confidence_response, valid_repair])

    result = asyncio.run(
        service.chat(
            session_id="l14", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["confidence"] == 50


def test_l15_strict_confidence_bool_triggers_repair(monkeypatch) -> None:
    bool_confidence_response = _chat_json(reasoning_assessment=_valid_assessment(confidence=True))
    valid_repair = _chat_json(reasoning_assessment=_valid_assessment(confidence=80))
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [bool_confidence_response, valid_repair])

    result = asyncio.run(
        service.chat(
            session_id="l15", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["confidence"] == 80


def test_repair_instruction_does_not_ask_for_chain_of_thought(monkeypatch) -> None:
    invalid_response = _chat_json(reasoning_assessment=None)
    valid_repair = _chat_json(reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [invalid_response, valid_repair])

    asyncio.run(
        service.chat(
            session_id="l-repair", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    repair_prompt = fake_client.chat_completions.messages[1][-1]["content"]
    assert "chain-of-thought" not in repair_prompt.lower() or "do not" in repair_prompt.lower()
    assert "Do NOT explain your reasoning process outside the JSON fields" in repair_prompt
    assert "Do NOT invent a reference ID" in repair_prompt


# ---------------------------------------------------------------------------
# Correction Round 3: M6-F01 cross-validator bypass fix - X1-X7.
# A model-generated M6-repair candidate must satisfy legacy execution
# structure AND operational response enforcement (evaluated under the
# candidate's OWN final reasoning_state) AND M6 validation, all together,
# before it may be accepted - no earlier validation success carries over.
# ---------------------------------------------------------------------------

# Operational-compliant text for CEO scope under insufficient_evidence
# (root-cause/cause-effect carved out; departments/impact still required).
_INSUFFICIENT_EVIDENCE_OPERATIONAL_SUMMARY = (
    "Executive Summary\n- Root cause not established. Production and inventory impact under "
    "review.\n\nRecommended Actions\n- Collect missing evidence.\n\nPriority Level\n- Medium."
)
# Departments/impact present, but deliberately NO bottleneck or cause/effect
# language - valid only under insufficient_evidence's carve-out, invalid
# under aligned/tension (which require both).
_NO_ROOT_CAUSE_OPERATIONAL_SUMMARY = (
    "Executive Summary\n- Production and inventory impact under review.\n\n"
    "Recommended Actions\n- Monitor closely.\n\nPriority Level\n- Medium."
)
# Fully compliant CEO-scope operational text (bottleneck + cause/effect +
# departments + impact) - valid under any reasoning_state.
_FULL_OPERATIONAL_SUMMARY = (
    "Executive Summary\n- Root operational bottleneck: production capacity is constraining "
    "fulfillment.\n- Cause/effect chain: reduced line speed drives lower throughput and inventory "
    "pressure.\n- Affected departments: Production, Sales.\n- Operational impact: fulfillment and "
    "inventory are at risk.\n\nRecommended Actions\n- Production: restore line speed within 48 "
    "hours.\n\nPriority Level\n- High."
)
_GENERIC_SUMMARY = (
    "Executive Summary\n- There are challenges and performance should improve.\n\n"
    "Recommended Actions\n- Focus on efficiency.\n\nPriority Level\n- Medium."
)


def _chat_json_custom(*, executive_summary: str, raw_decision: dict) -> str:
    return json.dumps({"executive_summary": executive_summary, "raw_decision": raw_decision})


def _valid_raw_decision(reasoning_assessment: dict) -> dict:
    return _raw_decision(reasoning_assessment)


def test_x1_repair_flips_to_aligned_but_misses_operational_requirements_fails_closed(monkeypatch) -> None:
    initial = _chat_json(
        executive_summary=_INSUFFICIENT_EVIDENCE_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="insufficient_evidence", confidence="50"),
    )
    repair = _chat_json(
        executive_summary=_NO_ROOT_CAUSE_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="aligned", confidence=50),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="x1", message="Status?", context={}, company_id=str(uuid4())))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2  # initial + M6 repair, NO third call
    assert log_calls == []  # no persistence


def test_x2_repair_flips_to_insufficient_evidence_valid_under_final_state_accepted(monkeypatch) -> None:
    initial = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="aligned", confidence=999),  # M6-invalid (out of bounds)
    )
    repair = _chat_json(
        executive_summary=_INSUFFICIENT_EVIDENCE_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="insufficient_evidence", confidence=50),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])

    result = asyncio.run(service.chat(session_id="x2", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "insufficient_evidence"


def test_x3_repair_breaks_legacy_execution_structure_fails_closed(monkeypatch) -> None:
    initial = _chat_json(
        reasoning_assessment=_valid_assessment(confidence=999)  # M6-invalid, legacy still fine
    )
    broken_raw_decision = _valid_raw_decision(_valid_assessment(confidence=50))
    broken_raw_decision["execution_engine"] = "not a dict"  # top-level legacy type violation
    repair = _chat_json_custom(
        executive_summary="Executive Summary\n- Reviewed.\n\nRecommended Actions\n- Monitor.\n\nPriority Level\n- Medium.",
        raw_decision=broken_raw_decision,
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.chat(
                session_id="x3", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
            )
        )
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2
    assert log_calls == []


def test_x4_repair_removes_raw_decision_entirely_fails_closed(monkeypatch) -> None:
    initial = _chat_json(reasoning_assessment=_valid_assessment(confidence=999))
    # reasoning_assessment misplaced outside raw_decision - raw_decision
    # object itself is gone.
    repair = json.dumps(
        {
            "executive_summary": "Executive Summary\n- Reviewed.\n\nRecommended Actions\n- Monitor.\n\nPriority Level\n- Medium.",
            "reasoning_assessment": _valid_assessment(confidence=50),
        }
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.chat(
                session_id="x4", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
            )
        )
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2
    assert log_calls == []


def test_x5_repair_malformed_execution_arrays_fails_closed(monkeypatch) -> None:
    initial = _chat_json(reasoning_assessment=_valid_assessment(confidence=999))
    malformed_raw_decision = _valid_raw_decision(_valid_assessment(confidence=50))
    # Present dict, but a required array item fails the legacy validator's
    # own per-item strictness rules (too short / not a real execution item).
    malformed_raw_decision["execution_engine"]["priority_order"] = ["fix it"]
    repair = _chat_json_custom(
        executive_summary="Executive Summary\n- Reviewed.\n\nRecommended Actions\n- Monitor.\n\nPriority Level\n- Medium.",
        raw_decision=malformed_raw_decision,
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            service.chat(
                session_id="x5", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
            )
        )
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2
    assert log_calls == []


def test_x6_repair_generic_operationally_invalid_ceo_response_fails_closed(monkeypatch) -> None:
    initial = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="aligned", confidence=999),
    )
    repair = _chat_json(
        executive_summary=_GENERIC_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="aligned", confidence=50),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="x6", message="Status?", context={}, company_id=str(uuid4())))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2
    assert log_calls == []


def test_x7_repair_valid_under_all_three_contracts_accepted(monkeypatch) -> None:
    initial = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="aligned", confidence=999),
    )
    repair = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        reasoning_assessment=_valid_assessment(reasoning_state="aligned", confidence=50),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, repair])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    result = asyncio.run(service.chat(session_id="x7", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["confidence"] == 50
    assert len(log_calls) == 1  # accepted candidate IS persisted (file decision log)


# ---------------------------------------------------------------------------
# Correction Round 3: M6-F02 length-heuristic removal - O1-O5.
# ---------------------------------------------------------------------------


def test_o1_o2_operationally_incomplete_regeneration_still_incomplete_fails_closed(monkeypatch) -> None:
    """O1 (regeneration triggered) + O2 (regenerated response is longer but
    still missing required elements -> FAIL CLOSED, no length heuristic)."""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    # Much longer than the original, but still missing bottleneck/cause/
    # department/impact language entirely - length must not matter.
    longer_but_still_incomplete = _chat_json(
        executive_summary=(
            "Executive Summary\n- "
            + ("This is a much longer and more detailed narrative response. " * 10)
            + "\n\nRecommended Actions\n- Continue monitoring the situation closely over time.\n\n"
            "Priority Level\n- Medium."
        ),
        reasoning_assessment=_valid_assessment(),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, longer_but_still_incomplete])
    log_calls = []
    monkeypatch.setattr("app.services.openai_client.log_decision_event", lambda **kw: log_calls.append(kw))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="o1o2", message="Status?", context={}, company_id=str(uuid4())))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2  # initial + one regeneration, no more
    assert log_calls == []


def test_o3_regenerated_response_satisfies_operational_elements_proceeds(monkeypatch) -> None:
    """O3: a regenerated response that genuinely satisfies the required
    operational elements proceeds (here, straight through to acceptance
    since its M6 object is also valid)."""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    compliant_regeneration = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment()
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, compliant_regeneration])

    result = asyncio.run(service.chat(session_id="o3", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 2
    assert result["ceo_text"]  # accepted, formatted


def test_o4_o5_regenerated_operationally_valid_but_m6_invalid_then_repaired(monkeypatch) -> None:
    """O4 (operationally-valid regeneration that is M6-invalid triggers an
    M6 repair) + O5 (the repaired candidate still goes through the full
    final all-contract gate)."""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=None)
    operationally_valid_but_m6_invalid = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=None
    )
    m6_repair = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [initial, operationally_valid_but_m6_invalid, m6_repair]
    )

    result = asyncio.run(service.chat(session_id="o4o5", message="Status?", context={}, company_id=str(uuid4())))
    # 1 initial + 1 operational regeneration + 1 M6 repair = 3 calls total,
    # still within the existing 5-call reasoning-generation budget.
    assert len(fake_client.chat_completions.messages) == 3
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"


# ---------------------------------------------------------------------------
# Correction Round 4: M6-F04 (legacy retry exhaustion fails closed) and
# M6-F03 (operational regeneration revalidates legacy structure) - LR1-LR5,
# OR1-OR6, and a final-candidate invariant test.
#
# No validator is monkeypatched anywhere in this section - only the
# external LLM call is faked.
# ---------------------------------------------------------------------------


def _legacy_invalid_raw_decision(reasoning_assessment: dict | None) -> dict:
    """A raw_decision whose solution_generator contains one short, generic
    item - genuinely fails _validate_execution_structure's own per-item
    strictness rules (real content present, wrong shape), not merely an
    absent/empty array (which the legacy validator treats as fine)."""
    payload = _raw_decision(reasoning_assessment)
    payload["solution_generator"]["urgent_30_days"] = ["fix it"]
    return payload


def _fail_closed_spies(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Spy on every persistence/formatting side effect a fail-closed path
    must never reach. Not a validator - only observes side effects."""
    calls = {"log_decision_event": 0, "format_ai_response": 0}

    def _log_spy(**kwargs):
        calls["log_decision_event"] += 1

    def _format_spy(**kwargs):
        calls["format_ai_response"] += 1
        return {"ceo_text": "", "logic_json": {}, "followup_question": None, "meta": {}}

    monkeypatch.setattr("app.services.openai_client.log_decision_event", _log_spy)
    monkeypatch.setattr("app.services.openai_client.format_ai_response", _format_spy)
    return calls


def _assert_no_session_persisted(service: AIService, company_id: str, session_id: str) -> None:
    key = service._memory_key(company_id, session_id)
    assert service.sessions.get(key, []) == []


# --- LR1-LR5: legacy retry loop ---------------------------------------------


def test_lr1_legacy_retry_exhausted_fails_closed(monkeypatch) -> None:
    """M6-F04: initial + both retries legacy-invalid, despite operationally
    and M6-valid content -> fail closed after exactly 3 model calls
    (initial + 2 retries), no 4th call, zero persistence."""
    invalid = _chat_json_custom(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        raw_decision=_legacy_invalid_raw_decision(_valid_assessment()),
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [invalid, invalid, invalid])
    calls = _fail_closed_spies(monkeypatch)
    company_id = str(uuid4())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="lr1", message="Status?", context={}, company_id=company_id))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 3
    assert calls == {"log_decision_event": 0, "format_ai_response": 0}
    _assert_no_session_persisted(service, company_id, "lr1")


def test_lr2_first_retry_legacy_valid_accepted(monkeypatch) -> None:
    invalid = _chat_json_custom(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        raw_decision=_legacy_invalid_raw_decision(_valid_assessment()),
    )
    valid_retry = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [invalid, valid_retry])

    result = asyncio.run(service.chat(session_id="lr2", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 2
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"


def test_lr3_second_retry_legacy_valid_accepted(monkeypatch) -> None:
    invalid = _chat_json_custom(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        raw_decision=_legacy_invalid_raw_decision(_valid_assessment()),
    )
    valid_retry = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [invalid, invalid, valid_retry])

    result = asyncio.run(service.chat(session_id="lr3", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 3
    assert result["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"


def test_lr4_legacy_valid_retry_still_operationally_incomplete_regenerates(monkeypatch) -> None:
    """LR4: the retry candidate becomes legacy-valid but is operationally
    incomplete - downstream operational enforcement still applies to THAT
    candidate (no inherited validation state)."""
    invalid = _chat_json_custom(
        executive_summary=_GENERIC_SUMMARY,
        raw_decision=_legacy_invalid_raw_decision(_valid_assessment()),
    )
    legacy_valid_but_operationally_incomplete = _chat_json(
        executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment()
    )
    operational_regeneration = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment()
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [invalid, legacy_valid_but_operationally_incomplete, operational_regeneration]
    )

    result = asyncio.run(service.chat(session_id="lr4", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 3  # initial + 1 retry + 1 operational regen
    assert result["ceo_text"]


def test_lr5_legacy_and_operational_valid_retry_still_m6_invalid_repairs(monkeypatch) -> None:
    """LR5: the retry candidate becomes legacy-valid and operationally
    valid but is M6-invalid - the downstream M6 gate applies to THAT
    candidate (no inherited validation state)."""
    invalid = _chat_json_custom(
        executive_summary=_FULL_OPERATIONAL_SUMMARY,
        raw_decision=_legacy_invalid_raw_decision(_valid_assessment()),
    )
    legacy_and_operational_valid_but_m6_invalid = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment(confidence=999)
    )
    m6_repair = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [invalid, legacy_and_operational_valid_but_m6_invalid, m6_repair]
    )

    result = asyncio.run(service.chat(session_id="lr5", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 3  # initial + 1 retry + 1 M6 repair
    assert result["logic_json"]["reasoning_assessment"]["confidence"] == 70  # _valid_assessment()'s default


# --- OR1-OR6: operational regeneration ---------------------------------------


def test_or1_regenerated_malformed_execution_engine_fails_closed(monkeypatch) -> None:
    """M6-F03: the regenerated candidate is operationally complete but has
    a malformed execution_engine (a string, not an object) - must fail
    closed via legacy revalidation, never reach M6 repair or persistence."""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    malformed_raw_decision = _raw_decision(_valid_assessment())
    malformed_raw_decision["execution_engine"] = "not a dict"
    operationally_complete_but_malformed = _chat_json_custom(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, raw_decision=malformed_raw_decision
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [initial, operationally_complete_but_malformed]
    )
    calls = _fail_closed_spies(monkeypatch)
    company_id = str(uuid4())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="or1", message="Status?", context={}, company_id=company_id))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2  # no M6 repair call, no 3rd call
    assert calls == {"log_decision_event": 0, "format_ai_response": 0}
    _assert_no_session_persisted(service, company_id, "or1")


def test_or2_regenerated_raw_decision_not_an_object_fails_closed(monkeypatch) -> None:
    """OR2: operationally-complete text, but raw_decision itself is not a
    usable object (a plain string, not a dict) - fails legacy structure
    validation. (Note: null/None is NOT a valid probe here - both
    _validate_execution_structure's ``parsed.get("raw_decision") or {}``
    and validate_reasoning_assessment treat an absent/null raw_decision as
    "no execution items yet" / a distinct missing-field error respectively,
    not a type violation - a truthy non-dict value is what genuinely fails
    the legacy isinstance(raw_decision, dict) check.)"""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    regenerated = json.dumps({"executive_summary": _FULL_OPERATIONAL_SUMMARY, "raw_decision": "not an object"})
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, regenerated])
    calls = _fail_closed_spies(monkeypatch)
    company_id = str(uuid4())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="or2", message="Status?", context={}, company_id=company_id))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2
    assert calls == {"log_decision_event": 0, "format_ai_response": 0}


def test_or3_regenerated_legacy_valid_still_operationally_incomplete_fails_closed(monkeypatch) -> None:
    """OR3: reconfirms M6-F02 - a legacy-valid but still operationally
    incomplete regeneration fails closed (no length heuristic)."""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    still_incomplete = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, still_incomplete])
    calls = _fail_closed_spies(monkeypatch)
    company_id = str(uuid4())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="or3", message="Status?", context={}, company_id=company_id))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 2
    assert calls == {"log_decision_event": 0, "format_ai_response": 0}


def test_or4_regenerated_fully_valid_accepted(monkeypatch) -> None:
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    compliant = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [initial, compliant])

    result = asyncio.run(service.chat(session_id="or4", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 2
    assert result["ceo_text"]


def test_or5_regenerated_operational_valid_m6_invalid_then_repaired(monkeypatch) -> None:
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    operational_valid_m6_invalid = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment(confidence=999)
    )
    m6_repair = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [initial, operational_valid_m6_invalid, m6_repair]
    )

    result = asyncio.run(service.chat(session_id="or5", message="Status?", context={}, company_id=str(uuid4())))
    assert len(fake_client.chat_completions.messages) == 3
    assert result["logic_json"]["reasoning_assessment"]["confidence"] == 70  # _valid_assessment()'s default


def test_or6_regeneration_then_m6_repair_breaks_legacy_fails_closed(monkeypatch) -> None:
    """OR6: proves stage composition - a candidate that passed operational
    regeneration's legacy check can still be legally rejected later if the
    SUBSEQUENT M6 repair breaks legacy structure (the existing M6-F01 gate
    catches it)."""
    initial = _chat_json(executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment())
    operational_valid_m6_invalid = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment(confidence=999)
    )
    broken_raw_decision = _raw_decision(_valid_assessment())
    broken_raw_decision["execution_engine"] = "not a dict"
    m6_repair_breaks_legacy = _chat_json_custom(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, raw_decision=broken_raw_decision
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [initial, operational_valid_m6_invalid, m6_repair_breaks_legacy]
    )
    calls = _fail_closed_spies(monkeypatch)
    company_id = str(uuid4())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.chat(session_id="or6", message="Status?", context={}, company_id=company_id))
    assert exc_info.value.status_code == 500
    assert len(fake_client.chat_completions.messages) == 3  # initial + operational regen + M6 repair, no 4th
    assert calls == {"log_decision_event": 0, "format_ai_response": 0}


# --- Final accepted-candidate invariant --------------------------------------


def test_final_accepted_candidate_satisfies_all_three_contracts_independently(monkeypatch) -> None:
    """Composed multi-replacement scenario (legacy-invalid -> operationally-
    incomplete retry -> M6-invalid regeneration -> final accepted
    candidate), then independently re-verify the FINAL parsed result
    against all three contracts directly - not merely trusting that chat()
    returned 200-equivalent."""
    invalid = _chat_json_custom(
        executive_summary=_GENERIC_SUMMARY,
        raw_decision=_legacy_invalid_raw_decision(_valid_assessment()),
    )
    legacy_valid_but_operationally_incomplete = _chat_json(
        executive_summary=_GENERIC_SUMMARY, reasoning_assessment=_valid_assessment()
    )
    operationally_valid_but_m6_invalid = _chat_json(
        executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment(confidence=999)
    )
    final_valid = _chat_json(executive_summary=_FULL_OPERATIONAL_SUMMARY, reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch,
        [invalid, legacy_valid_but_operationally_incomplete, operationally_valid_but_m6_invalid, final_valid],
    )

    result = asyncio.run(service.chat(session_id="final-invariant", message="Status?", context={}, company_id=str(uuid4())))
    # initial + 1 legacy retry + 1 operational regen + 1 M6 repair = 4 calls,
    # within the 5-call reasoning-generation budget.
    assert len(fake_client.chat_completions.messages) == 4

    final_parsed = {"executive_summary": result["ceo_text"], "raw_decision": result["logic_json"]}
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=SYNTHETIC_TRUTH_ITEMS,
        company_brain_context=SYNTHETIC_BRAIN_ITEMS,
    )
    assert _validate_execution_structure(final_parsed) is True
    assert _operational_response_missing_elements(parsed=final_parsed, decision_context=decision_context) == []
    m6_ok, m6_errors = validate_reasoning_assessment(final_parsed, decision_context)
    assert m6_ok is True, m6_errors


# ---------------------------------------------------------------------------
# Public API contract - reasoning_signals/reference_catalog do not leak
# ---------------------------------------------------------------------------


def test_debug_snapshot_still_captures_full_internal_reasoning_metadata(monkeypatch) -> None:
    """Part 6.1: DECISION_CONTEXT_DEBUG's existing snapshot path is
    untouched - it must retain the FULL decision_context (including the
    M6-internal reasoning_signals/reasoning_reference_catalog) even though
    the public meta.context no longer does."""
    from app.services import decision_debug as debug_module

    monkeypatch.setattr(
        debug_module, "settings", dataclasses.replace(debug_module.settings, DECISION_CONTEXT_DEBUG=True)
    )
    debug_module._SNAPSHOTS.clear()

    response = _chat_json(reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])
    company_id = str(uuid4())

    asyncio.run(
        service.chat(
            session_id="debug-check",
            message="Status?",
            context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=company_id,
        )
    )

    snapshots = debug_module.list_decision_debug_snapshots(company_id=company_id, session_id="debug-check")
    assert snapshots, "expected a debug snapshot to have been recorded"
    full_decision_context = snapshots[0]["decision_context"]
    assert "reasoning_signals" in full_decision_context
    assert "reasoning_reference_catalog" in full_decision_context


def test_chat_response_meta_context_does_not_expose_internal_m6_signals(monkeypatch) -> None:
    response = _chat_json(reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(
            session_id="leak-check", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    public_decision_ctx = result["meta"]["context"]["decision_context"]
    assert "reasoning_signals" not in public_decision_ctx
    assert "reasoning_reference_catalog" not in public_decision_ctx
    # The model-generated reasoning_assessment DOES remain public, in logic_json.
    assert "reasoning_assessment" in result["logic_json"]


# ---------------------------------------------------------------------------
# Tenant / business-unit isolation - REAL gating functions (not mocked),
# proving M6's runtime validation doesn't bypass or weaken M4/M5 gates.
# Uses an evidence-free, reference-free reasoning_assessment since neither
# layer supplies material this turn for these scopes.
# ---------------------------------------------------------------------------


def _empty_basis_assessment(**overrides) -> dict:
    return _valid_assessment(
        reasoning_state="insufficient_evidence",
        recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": []},
        **overrides,
    )


def test_caesar_scope_gets_no_dairtna_company_brain_refs(monkeypatch) -> None:
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    response = _chat_json(reasoning_assessment=_empty_basis_assessment())
    service = AIService()
    fake_client = _FakeOpenAIClient([response])
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeDbPool(JANNAT_COMPANY)

    result = asyncio.run(
        service.chat(
            session_id="caesar", message="Status?", context={"aimx_department": CAESAR_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "Type: PREFERENCE" not in prompt_text
    assert "Type: DECISION_RULE" not in prompt_text


def test_ceo_no_department_scope_gets_no_dairtna_company_brain_refs(monkeypatch) -> None:
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    # CEO scope requires "affected departments"/"operational impact"
    # keywords regardless of reasoning_state (only root-cause/cause-effect
    # are carved out for insufficient_evidence) - satisfy them directly so
    # this test isolates Company Brain gating, not operational enforcement.
    response = _chat_json(
        executive_summary=(
            "Executive Summary\n- Root cause not established. Production and inventory impact "
            "under review.\n\nRecommended Actions\n- Collect missing evidence.\n\nPriority Level\n- Medium."
        ),
        reasoning_assessment=_empty_basis_assessment(),
    )
    service = AIService()
    fake_client = _FakeOpenAIClient([response])
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeDbPool(JANNAT_COMPANY)

    result = asyncio.run(
        service.chat(session_id="ceo-nodept", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False


def test_non_jannat_tenant_gets_no_pilot_refs(monkeypatch) -> None:
    _configure_jannat_company_id(monkeypatch, JANNAT_COMPANY_ID)
    response = _chat_json(
        executive_summary=(
            "Executive Summary\n- Root cause not established. Production and inventory impact "
            "under review.\n\nRecommended Actions\n- Collect missing evidence.\n\nPriority Level\n- Medium."
        ),
        reasoning_assessment=_empty_basis_assessment(),
    )
    service = AIService()
    fake_client = _FakeOpenAIClient([response])
    service.client = fake_client
    service.db_enabled = False
    service.repo = None
    service.db_pool = _FakeDbPool(OTHER_COMPANY)

    result = asyncio.run(
        service.chat(session_id="other-tenant", message="Status?", context={}, company_id=str(uuid4()))
    )
    assert result["meta"]["context"]["truth_context_bridge"]["status"] == "not_applicable"
    assert result["meta"]["context"]["company_brain_bridge"]["dairtna_knowledge_included"] is False


# ---------------------------------------------------------------------------
# Backward-compatible defaults / existing contract preserved
# ---------------------------------------------------------------------------


def test_reasoning_signals_default_cleanly_without_truth_or_brain_kwargs() -> None:
    decision_context = build_decision_context(context={}, response_language="en")
    signals = decision_context["reasoning_signals"]
    assert signals["truth_available"] is False
    assert signals["company_brain_policy_available"] is False
    assert signals["both_layers_present"] is False


def test_required_output_schema_still_has_all_pre_m6_keys() -> None:
    for key in (
        '"context_lock"', '"problem_classification"', '"truth_validation"',
        '"root_cause_engine"', '"solution_generator"', '"execution_engine"',
    ):
        assert key in AIMX_DECISION_PROMPT


def test_chat_response_top_level_contract_unchanged(monkeypatch) -> None:
    response = _chat_json(reasoning_assessment=_valid_assessment())
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [response])

    result = asyncio.run(
        service.chat(
            session_id="contract", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT}, company_id=str(uuid4())
        )
    )
    assert set(result.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}
