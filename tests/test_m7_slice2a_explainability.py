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
# B2B-01..12, B2B-15 (M7 Slice 2B): safe executive-provenance passthrough
# fields and the structured missing_evidence resolver. Unit-level tests
# against build_public_explainability() directly - B2B-13/14 (final-
# candidate/no-new-model-call proof) live below, after the real-chat()
# fixtures they need.
# ---------------------------------------------------------------------------


def test_b2b_01_reasoning_state_field_comes_from_final_accepted_candidate() -> None:
    decision_context = _decision_context()
    assessment = _assessment(reasoning_state="tension")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["reasoning_state"] == "tension"


def test_b2b_02_operational_assessment_field_comes_from_final_accepted_candidate() -> None:
    decision_context = _decision_context()
    assessment = _assessment(operational_assessment="Hall 2 production trend is stable given current evidence.")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["operational_assessment"] == "Hall 2 production trend is stable given current evidence."


def test_b2b_03_company_brain_alignment_field_comes_from_final_accepted_candidate() -> None:
    decision_context = _decision_context()
    assessment = _assessment(company_brain_alignment="partially supported")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["company_brain_alignment"] == "partially supported"


def test_b2b_04_tensions_field_comes_from_final_accepted_candidate() -> None:
    decision_context = _decision_context()
    assessment = _assessment(tensions=["Evidence suggests a stable trend while company policy expects growth."])
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["tensions"] == ["Evidence suggests a stable trend while company policy expects growth."]


def test_b2b_05_evidence_gaps_field_comes_from_final_accepted_candidate() -> None:
    decision_context = _decision_context()
    assessment = _assessment(evidence_gaps=["Water consumption reading is missing for Hall 2."])
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["evidence_gaps"] == ["Water consumption reading is missing for Hall 2."]


def test_b2b_06_risk_assessment_field_comes_from_final_accepted_candidate() -> None:
    decision_context = _decision_context()
    assessment = _assessment(risk_assessment="Moderate risk of supply disruption if the trend continues.")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["risk_assessment"] == "Moderate risk of supply disruption if the trend continues."


def test_b2b_07_structured_missing_evidence_resolves_only_final_accepted_gap_refs() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T3"]}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert len(result["missing_evidence"]) == 1
    item = result["missing_evidence"][0]
    assert item["id"] == "m1"
    assert item["label"] == "water_consumption"  # T3: canonical_field is None, falls back to type
    assert set(item.keys()) == {
        "id", "label", "filename", "report_date", "entity", "epistemic_origin", "source_time_status",
    }


def test_b2b_08_non_gap_t_ref_cannot_appear_as_missing_evidence() -> None:
    """T1 is usable, resolved, non-gap evidence - citing it as a "gap" is
    invalid and must be skipped, never fabricated (mirrors is_gap_reference,
    not is_usable_evidence)."""
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T1"]}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["missing_evidence"] == []


def test_b2b_09_invalid_missing_evidence_refs_fail_closed() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T99"]}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["missing_evidence"] == []


def test_b2b_10_truth_list_reordering_cannot_change_gap_reference_meaning() -> None:
    truth_items = [dict(item) for item in TRUTH_ITEMS]
    decision_context = _decision_context(truth_items=truth_items)
    catalog = decision_context["reasoning_reference_catalog"]
    assert catalog["truth"]["T3"]["internal_source_item"]["type"] == "water_consumption"

    # Adversarially reorder AFTER catalog creation.
    truth_items.reverse()
    assert decision_context["operational_truth_context"][0]["type"] != "water_consumption"

    assessment = _assessment(
        recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": ["T3"]}
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    assert len(result["missing_evidence"]) == 1
    assert result["missing_evidence"][0]["label"] == "water_consumption"


def test_b2b_11_no_t_or_cb_ref_appears_in_new_public_fields() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": ["T3"]},
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    for item in result["missing_evidence"]:
        assert item["id"].startswith("m") and item["id"][1:].isdigit()
        assert "ref" not in item

    serialized = json.dumps(result)
    assert '"T1"' not in serialized
    assert '"T3"' not in serialized
    assert '"CB1"' not in serialized


def test_b2b_12_no_internal_source_item_or_catalog_metadata_appears_publicly() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": ["T3"]},
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)

    serialized = json.dumps(result)
    assert "internal_source_item" not in serialized
    assert "is_gap_reference" not in serialized
    assert "is_usable_evidence" not in serialized
    assert "is_settled" not in serialized
    assert "reasoning_reference_catalog" not in serialized


def test_b2b_15_m6_schema_and_validators_unchanged() -> None:
    from app.services.reasoning_validation import (
        ReasoningAssessment,
        RecommendationBasis,
        validate_reasoning_assessment,
    )

    assert set(ReasoningAssessment.model_fields.keys()) == {
        "reasoning_state", "operational_assessment", "company_brain_alignment",
        "tensions", "evidence_gaps", "risk_assessment", "confidence", "recommendation_basis",
    }
    assert set(RecommendationBasis.model_fields.keys()) == {"evidence_basis", "company_basis", "missing_evidence"}

    decision_context = _decision_context()
    # M3 not usable as evidence_basis - the SAME validator behavior as
    # before Slice 2B; the new missing_evidence resolver never weakens this.
    assessment = _assessment(
        recommendation_basis={"evidence_basis": ["T3"], "company_basis": [], "missing_evidence": []}
    )
    is_valid, errors = validate_reasoning_assessment(
        {"raw_decision": {"reasoning_assessment": assessment}}, decision_context
    )
    assert is_valid is False
    assert any("not usable supporting evidence" in error for error in errors)


# ---------------------------------------------------------------------------
# H01-A..N (Correction Round 1, H-01): the PUBLIC PRESENTATION boundary
# fails closed when an approved, structurally M6-valid prose field's own
# CONTENT contains an internal reference token, UUID, internal path, or
# explicit internal/debug marker - independent of decision-provenance
# validation, which stays untouched. Unit-level tests against
# build_public_explainability() directly, matching the established E/B2B
# test style; the real end-to-end AIService.chat() proof lives further
# below (Section 15) next to the E10/E11/B2B-13/14 real-chat fixtures.
# ---------------------------------------------------------------------------


def test_h01_a_safe_operational_assessment_survives_byte_for_byte() -> None:
    decision_context = _decision_context()
    safe_text = "Hall 2 production decreased by 4% this week."
    assessment = _assessment(operational_assessment=safe_text)
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["operational_assessment"] == safe_text


def test_h01_b_operational_assessment_containing_standalone_t_ref_fails_closed() -> None:
    decision_context = _decision_context()
    assessment = _assessment(operational_assessment="Current evidence is based on T3")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["operational_assessment"] is None


def test_h01_c_risk_assessment_containing_standalone_cb_ref_fails_closed() -> None:
    decision_context = _decision_context()
    assessment = _assessment(risk_assessment="CB2 is unresolved and creates exposure")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["risk_assessment"] is None


def test_h01_d_risk_assessment_containing_a_uuid_fails_closed() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        risk_assessment="See source b6e6b8f0-1111-2222-3333-444455556666 for detail"
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["risk_assessment"] is None


def test_h01_e_risk_assessment_containing_internal_windows_path_fails_closed() -> None:
    decision_context = _decision_context()
    assessment = _assessment(risk_assessment=r"See C:\internal\pilot\secret.xlsx for the source data")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["risk_assessment"] is None


def test_h01_f_risk_assessment_containing_internal_posix_or_storage_path_fails_closed() -> None:
    decision_context = _decision_context()
    for unsafe_text in (
        "The source file lives at /var/data/hall2_report.xlsx internally",
        "Check /mnt/pilot/hall2.csv for the raw export",
        r"Raw file at storage\hall2_report.xlsx",
        "Raw file at storage/hall2_report.xlsx",
    ):
        assessment = _assessment(risk_assessment=unsafe_text)
        result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
        assert result["risk_assessment"] is None, unsafe_text

    # Sanity: a normal business phrase using "storage/" as a plain word
    # (no file extension) must NOT be treated as an internal path.
    safe_text = "Confirm storage/warehouse capacity before increasing production."
    assessment = _assessment(risk_assessment=safe_text)
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["risk_assessment"] == safe_text


# ---------------------------------------------------------------------------
# R1-A..L (Correction Round 2, H-01-R1): Codex found that the original
# forward-slash "storage/" rule only detected a SINGLE file-like segment
# (storage/secret.xlsx) and missed NESTED paths (storage/files/abc,
# storage/uploads/company/report.xlsx). _INTERNAL_PATH_PATTERN now also
# matches storage/<segment>/<segment>[...] - two or more slash-separated
# segments - while continuing to preserve ordinary business prose that
# merely contains one "storage/word" token before normal text continues.
# ---------------------------------------------------------------------------


def test_r1_a_nested_storage_path_two_segments_fails_closed() -> None:
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("storage/files/abc") is None


def test_r1_b_nested_storage_path_two_segments_with_extension_fails_closed() -> None:
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("storage/files/abc.xlsx") is None


def test_r1_c_nested_storage_path_report_json_fails_closed() -> None:
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("storage/private/report.json") is None


def test_r1_d_nested_storage_path_three_segments_fails_closed() -> None:
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("storage/uploads/company/report.xlsx") is None


def test_r1_e_nested_storage_path_with_year_segment_fails_closed() -> None:
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("storage/data/2026/report.json") is None


def test_r1_f_through_j_safe_business_prose_survives_byte_for_byte() -> None:
    from app.services.explainability import _safe_public_prose

    safe_texts = (
        "storage capacity is low",
        "storage/warehouse capacity must be checked",
        "Confirm storage/warehouse capacity before increasing production.",
        "warehouse/storage planning is incomplete",
        "production/warehouse coordination is needed",
    )
    for text in safe_texts:
        assert _safe_public_prose(text) == text, text


def test_r1_k_and_l_public_urls_survive_exactly() -> None:
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("https://example.com/report") == "https://example.com/report"
    assert _safe_public_prose("http://example.org/dashboard") == "http://example.org/dashboard"


def test_r1_existing_path_forms_remain_blocked() -> None:
    from app.services.explainability import _safe_public_prose

    for unsafe_text in (
        r"storage\files\abc.xlsx",
        r"See C:\internal\pilot\secret.xlsx",
        "C:/internal/pilot/secret.xlsx",
        "See /mnt/data/pilot.xlsx",
        "See /home/user/file",
        "See /tmp/file",
        "See /var/app/file",
    ):
        assert _safe_public_prose(unsafe_text) is None, unsafe_text


# ---------------------------------------------------------------------------
# R2URL-A..L (Correction Round 3, M7-2B-R2-URL): Codex found that a real
# public http(s):// URL whose path happens to look like an internal
# storage path (e.g. https://example.com/storage/files/report) was
# incorrectly rejected. _contains_internal_path_outside_public_url now
# exempts an internal-path-shaped match ONLY when it falls entirely
# inside a recognized http(s):// URL span - the nested-storage-path
# blocking from Correction Round 2 (H-01-R1) stays fully intact for
# anything outside a URL, including a second such path elsewhere in the
# same string.
# ---------------------------------------------------------------------------


def test_r2url_a_through_f_safe_urls_survive_exactly() -> None:
    from app.services.explainability import _safe_public_prose

    safe_urls = (
        "https://example.com/storage/files/report",
        "https://example.com/storage/files/report.xlsx",
        "https://example.com/storage/private/report.json",
        "http://example.org/storage/files/report",
        "https://example.com/storage/company/2026/report.xlsx",
        "https://example.com/storage/files/report?version=2#section",
    )
    for url in safe_urls:
        assert _safe_public_prose(url) == url, url


def test_r2url_g_and_h_urls_embedded_in_prose_survive_exactly() -> None:
    from app.services.explainability import _safe_public_prose

    texts = (
        "See https://example.com/storage/files/report for the public report.",
        "Public dashboard: https://example.com/storage/company/2026/report.xlsx",
    )
    for text in texts:
        assert _safe_public_prose(text) == text, text


def test_r2url_i_url_plus_separate_internal_path_fails_closed() -> None:
    """Critical adversarial case: the first storage-shaped fragment is
    inside a public URL and would be exempt on its own, but a SECOND,
    genuinely internal path appears later in the same string, outside
    any URL span - the whole field must still fail closed."""
    from app.services.explainability import _safe_public_prose

    text = "See https://example.com/storage/files/report and inspect storage/private/report.json"
    assert _safe_public_prose(text) is None


def test_r2url_j_and_k_url_plus_separate_windows_or_posix_path_fails_closed() -> None:
    from app.services.explainability import _safe_public_prose

    assert (
        _safe_public_prose(r"https://example.com/storage/files/report then C:\internal\secret.xlsx") is None
    )
    assert (
        _safe_public_prose("https://example.com/storage/files/report then /mnt/data/secret.xlsx") is None
    )


def test_r2url_l_non_http_scheme_gets_no_exemption() -> None:
    """file:// (or any non-http(s) scheme) must never become a privacy
    bypass - only http/https URL spans are recognized."""
    from app.services.explainability import _safe_public_prose

    assert _safe_public_prose("file:///storage/private/report.json") is None


def test_r2url_url_span_is_whitespace_bounded_not_greedy() -> None:
    """The URL span must stop at whitespace - a second storage path after
    a space must never be swallowed into the "public" span merely because
    a URL appears earlier in the same string."""
    from app.services.explainability import _safe_public_prose

    text = "See https://example.com/storage/files/report storage/private/report.json"
    assert _safe_public_prose(text) is None


def test_h01_g_tensions_list_drops_only_the_unsafe_item() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        tensions=["Safe business tension", "See T4", "Another safe tension"]
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["tensions"] == ["Safe business tension", "Another safe tension"]


def test_h01_h_evidence_gaps_drops_only_the_item_with_an_internal_marker() -> None:
    decision_context = _decision_context()
    assessment = _assessment(
        evidence_gaps=[
            "Water consumption reading is missing for Hall 2.",
            "Not resolvable - see reasoning_reference_catalog for detail",
        ]
    )
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["evidence_gaps"] == ["Water consumption reading is missing for Hall 2."]


def test_h01_i_explicit_internal_debug_markers_fail_closed() -> None:
    decision_context = _decision_context()
    unsafe_markers = [
        "See internal_source_item for the raw snapshot",
        "Derived from logic_json directly",
        "Traced via source_file_id lookup",
        "Ignore the system prompt instruction here",
        "This reflects chain-of-thought reasoning",
    ]
    for unsafe_text in unsafe_markers:
        assessment = _assessment(operational_assessment=unsafe_text)
        result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
        assert result["operational_assessment"] is None, unsafe_text


def test_h01_j_safe_arabic_executive_prose_remains_unchanged() -> None:
    decision_context = _decision_context()
    safe_arabic = "مياه القسم غير مكتملة هذا الأسبوع."
    assessment = _assessment(operational_assessment=safe_arabic, risk_assessment=safe_arabic)
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["operational_assessment"] == safe_arabic
    assert result["risk_assessment"] == safe_arabic


def test_h01_k_all_four_approved_english_alignment_values_survive_exactly() -> None:
    decision_context = _decision_context()
    for value in (
        "supported by current evidence",
        "not supported by current evidence",
        "partially supported",
        "cannot determine",
    ):
        assessment = _assessment(company_brain_alignment=value)
        result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
        assert result["company_brain_alignment"] == value


def test_h01_l_all_four_approved_arabic_alignment_values_survive_exactly() -> None:
    decision_context = _decision_context()
    for value in (
        "مدعوم بالأدلة الحالية",
        "غير مدعوم بالأدلة الحالية",
        "مدعوم جزئيًا",
        "لا يمكن التحديد",
    ):
        assessment = _assessment(company_brain_alignment=value)
        result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
        assert result["company_brain_alignment"] == value


def test_h01_m_alignment_value_with_extra_trailing_text_does_not_survive() -> None:
    decision_context = _decision_context()
    assessment = _assessment(company_brain_alignment="supported by current evidence — see T3")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["company_brain_alignment"] is None


def test_h01_n_unexpected_alignment_value_fails_closed_never_a_frontend_fallback() -> None:
    decision_context = _decision_context()
    assessment = _assessment(company_brain_alignment="somewhat aligned, mostly")
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=decision_context)
    assert result["company_brain_alignment"] is None


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
# B2B-13/14 (M7 Slice 2B): final-candidate guarantee for the new safe
# executive-provenance fields, and proof no new model call was introduced -
# through the SAME real AIService.chat() lifecycle as E10/E11.
# ---------------------------------------------------------------------------


def test_b2b_13_rejected_repaired_candidate_new_fields_never_leak(monkeypatch) -> None:
    """Mirrors E11 for the Slice 2B fields: the REJECTED first candidate's
    reasoning_state/operational_assessment/tensions/missing_evidence must
    never appear in the public response - only the repaired (final
    accepted) candidate's."""
    invalid_first_response = _chat_json(
        reasoning_assessment=_assessment(
            reasoning_state="tension",
            operational_assessment="REJECTED-CANDIDATE-TEXT-SHOULD-NEVER-LEAK",
            tensions=["rejected-tension-should-never-leak"],
            recommendation_basis={"evidence_basis": ["T99"], "company_basis": [], "missing_evidence": []},
        )
    )
    repaired_response = _chat_json(
        reasoning_assessment=_assessment(
            reasoning_state="aligned",
            operational_assessment="ACCEPTED-CANDIDATE-TEXT",
            tensions=[],
            recommendation_basis={"evidence_basis": ["T2"], "company_basis": [], "missing_evidence": ["T3"]},
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(
        monkeypatch, [invalid_first_response, repaired_response]
    )

    result = asyncio.run(
        service.chat(
            session_id="b2b13", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    assert len(fake_client.chat_completions.messages) == 2

    explainability = result["meta"]["context"]["explainability"]
    assert explainability["reasoning_state"] == "aligned"
    assert explainability["operational_assessment"] == "ACCEPTED-CANDIDATE-TEXT"
    assert explainability["tensions"] == []
    assert len(explainability["missing_evidence"]) == 1
    assert explainability["missing_evidence"][0]["label"] == "water_consumption"

    serialized = json.dumps(explainability)
    assert "REJECTED-CANDIDATE-TEXT-SHOULD-NEVER-LEAK" not in serialized
    assert "rejected-tension-should-never-leak" not in serialized
    assert explainability["reasoning_state"] != "tension"  # the REJECTED candidate's state never surfaces


def test_b2b_14_no_new_model_call_introduced_for_slice_2b_fields(monkeypatch) -> None:
    """A normal valid-on-first-try turn (like E10) makes exactly ONE model
    call - Slice 2B's new fields are pure passthrough/resolution of data
    already produced by that single call, never a second model call, never
    new reasoning."""
    valid_response = _chat_json(
        reasoning_assessment=_assessment(
            recommendation_basis={"evidence_basis": ["T1"], "company_basis": ["CB1"], "missing_evidence": ["T3"]}
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [valid_response])

    result = asyncio.run(
        service.chat(
            session_id="b2b14", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    assert len(fake_client.chat_completions.messages) == 1
    explainability = result["meta"]["context"]["explainability"]
    assert explainability["reasoning_state"] == "aligned"
    assert len(explainability["missing_evidence"]) == 1


def test_h01_o_real_chat_public_response_fails_closed_for_unsafe_prose_while_m6_stays_valid(monkeypatch) -> None:
    """Section 15: the fake external model returns a structurally
    M6-valid FINAL candidate whose free-form prose fields themselves
    contain internal artifacts (a standalone T3 token, an internal
    Windows path, a CB7 token inside a tensions list item). M6 accepts
    it as-is (no repair, exactly one real model call) - the PUBLIC
    explainability layer is what fails closed for the unsafe fields/
    items, proving the fix at the actual product boundary rather than
    only in a unit test of the helper function."""
    unsafe_response = _chat_json(
        reasoning_assessment=_assessment(
            reasoning_state="aligned",
            operational_assessment="Internal ref T3 should not reach the executive UI",
            risk_assessment=r"See C:\internal\pilot\secret.xlsx",
            tensions=["Safe executive tension", "See CB7"],
            recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": []},
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [unsafe_response])

    result = asyncio.run(
        service.chat(
            session_id="h01o", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    # Exactly one real model call: M6 accepted the candidate unmodified -
    # the public-safety filter never triggers a repair/regeneration cycle.
    assert len(fake_client.chat_completions.messages) == 1

    # M6 stayed valid internally - the raw model-generated fields are
    # still present, byte-for-byte, in logic_json (internal compatibility
    # surface, never the public contract, never scanned by this filter).
    raw_assessment = result["logic_json"]["reasoning_assessment"]
    assert raw_assessment["operational_assessment"] == "Internal ref T3 should not reach the executive UI"
    assert raw_assessment["risk_assessment"] == r"See C:\internal\pilot\secret.xlsx"
    assert raw_assessment["tensions"] == ["Safe executive tension", "See CB7"]

    explainability = result["meta"]["context"]["explainability"]
    assert explainability["reasoning_state"] == "aligned"
    assert explainability["operational_assessment"] is None
    assert explainability["risk_assessment"] is None
    assert explainability["tensions"] == ["Safe executive tension"]

    # No forbidden artifact anywhere in the PUBLIC-facing part of the
    # response (meta.context, which is exactly what the frontend/
    # allowlist boundary exposes) - logic_json is deliberately excluded
    # from this check since it is internal-only, never the public surface.
    public_serialized = json.dumps(result["meta"]["context"])
    for forbidden in ("Internal ref T3", r"C:\internal\pilot\secret.xlsx", "See CB7", "T3", "CB7"):
        assert forbidden not in public_serialized, forbidden


def test_r1_m_real_chat_public_response_fails_closed_for_nested_storage_path(monkeypatch) -> None:
    """Correction Round 2 (H-01-R1): the same real-lifecycle proof as
    test_h01_o, but for the specific nested forward-slash storage-path
    gap Codex found (storage/private/report.json). M6 accepts the
    candidate as-is; the public explainability layer omits only the
    unsafe risk_assessment field, while reasoning_state, the safe
    operational_assessment, the safe tension, and the exact-allowlisted
    company_brain_alignment all survive."""
    unsafe_response = _chat_json(
        reasoning_assessment=_assessment(
            reasoning_state="aligned",
            operational_assessment="Safe operational assessment.",
            company_brain_alignment="supported by current evidence",
            risk_assessment="See storage/private/report.json",
            tensions=["Safe executive tension"],
            recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": []},
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [unsafe_response])

    result = asyncio.run(
        service.chat(
            session_id="r1m", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    # Exactly one real model call - the nested-path fix causes no repair/
    # regeneration cycle; M6 stayed valid internally.
    assert len(fake_client.chat_completions.messages) == 1

    # Private compatibility surface retains the raw accepted model prose
    # unmodified (never scanned by this filter).
    raw_assessment = result["logic_json"]["reasoning_assessment"]
    assert raw_assessment["risk_assessment"] == "See storage/private/report.json"

    explainability = result["meta"]["context"]["explainability"]
    assert explainability["reasoning_state"] == "aligned"
    assert explainability["operational_assessment"] == "Safe operational assessment."
    assert explainability["tensions"] == ["Safe executive tension"]
    assert explainability["company_brain_alignment"] == "supported by current evidence"
    assert explainability["risk_assessment"] is None

    public_serialized = json.dumps(result["meta"]["context"])
    assert "storage/private/report.json" not in public_serialized
    assert "storage/private" not in public_serialized


def test_r2url_real_chat_public_response_survives_safe_url(monkeypatch) -> None:
    """Correction Round 3 (M7-2B-R2-URL), Section 21: a structurally
    M6-valid final candidate whose operational_assessment contains a real
    public http(s) URL (which happens to include a storage/-shaped path)
    must survive EXACTLY, proving the new exemption works at the actual
    public product boundary, not only in a unit test of the helper."""
    safe_response = _chat_json(
        reasoning_assessment=_assessment(
            reasoning_state="aligned",
            operational_assessment="Public report: https://example.com/storage/files/report",
            risk_assessment="Safe operational risk statement.",
            company_brain_alignment="supported by current evidence",
            tensions=["Safe executive tension"],
            recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": []},
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [safe_response])

    result = asyncio.run(
        service.chat(
            session_id="r2url-safe", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    # Normal model-call count - the URL exemption causes no repair/regeneration.
    assert len(fake_client.chat_completions.messages) == 1

    explainability = result["meta"]["context"]["explainability"]
    assert explainability["reasoning_state"] == "aligned"
    assert explainability["operational_assessment"] == "Public report: https://example.com/storage/files/report"
    assert explainability["risk_assessment"] == "Safe operational risk statement."
    assert explainability["tensions"] == ["Safe executive tension"]
    assert explainability["company_brain_alignment"] == "supported by current evidence"


def test_r2url_real_chat_public_response_mixed_url_and_internal_path(monkeypatch) -> None:
    """Section 22: the presence of one safe public HTTP URL in
    operational_assessment must not disable filtering elsewhere in the
    SAME candidate - risk_assessment's genuinely internal storage path
    still fails closed even though operational_assessment's URL survives."""
    mixed_response = _chat_json(
        reasoning_assessment=_assessment(
            reasoning_state="aligned",
            operational_assessment="Public report: https://example.com/storage/files/report",
            risk_assessment="Inspect storage/private/report.json",
            company_brain_alignment="supported by current evidence",
            tensions=[],
            recommendation_basis={"evidence_basis": [], "company_basis": [], "missing_evidence": []},
        )
    )
    service, fake_client = _service_with_synthetic_m4_m5(monkeypatch, [mixed_response])

    result = asyncio.run(
        service.chat(
            session_id="r2url-mixed", message="Status?", context={"aimx_department": POULTRY_DEPARTMENT},
            company_id=str(uuid4()),
        )
    )

    assert len(fake_client.chat_completions.messages) == 1

    explainability = result["meta"]["context"]["explainability"]
    assert explainability["operational_assessment"] == "Public report: https://example.com/storage/files/report"
    assert explainability["risk_assessment"] is None

    public_serialized = json.dumps(result["meta"]["context"])
    assert "storage/private/report.json" not in public_serialized


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
