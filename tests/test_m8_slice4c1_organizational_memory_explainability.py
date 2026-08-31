"""M8 Slice 4C-1: Organizational Memory Public Explainability Backend.

Proves: `cited_organizational_memory` is a fourth, always-present, additive
public explainability field, resolved ONLY from the FINAL accepted
citations against the SAME turn's organizational_memory_reference_catalog
(never a second DB read, never uncited context); every text value derives
exclusively from the Slice 4B model-visible rendered_snapshot, then passes
through the existing public-safety sanitization boundary (Founder
Correction 1); internal `OM#` labels and every durable UUID
(decision_memory_id/outcome_memory_id/reasoning_receipt_id) never reach
the public contract; fresh opaque `h1`/`h2`/... presentation ids are
generated from cited iteration order; Truth/Company-Brain/Organizational-
Memory stay three separate arrays; an unresolvable citation degrades
per-item, never failing the whole explainability object (Founder
Correction 2: one canonical snapshot, no drift between prompt and
explainability).
"""
from __future__ import annotations

import dataclasses
import logging
import pathlib

from app.services.decision_context import (
    MAX_DECISION_TEXT_CHARS,
    MAX_OUTCOME_SUMMARY_CHARS,
    MAX_RATIONALE_CHARS,
    _build_organizational_memory_reference_catalog,
    _build_organizational_memory_rendered_snapshot,
    build_decision_context,
)
from app.services.explainability import (
    PUBLIC_EXPLAINABILITY_FIELDS,
    _resolve_cited_organizational_memory,
    _sanitize_organizational_memory_item,
    build_public_explainability,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sample_item(**overrides) -> dict:
    base = {
        "decision_memory_id": "did-1",
        "situation_id": None,
        "decision_text": "Approve the focused expansion plan.",
        "rationale": "Cash coverage supports it.",
        "decided_at": "2020-01-01T00:00:00Z",
        "outcomes": [
            {
                "outcome_memory_id": "oid-1",
                "outcome_summary": "Delivered a real lift.",
                "result_state": "positive",
                "observed_at": "2020-02-01T00:00:00Z",
            }
        ],
    }
    base.update(overrides)
    return base


def _outcomes(n: int, *, result_state: str = "positive") -> list[dict]:
    return [
        {
            "outcome_memory_id": f"oid-{i}",
            "outcome_summary": f"Summary {i}",
            "result_state": result_state,
            "observed_at": f"2020-02-{i + 1:02d}T00:00:00Z",
        }
        for i in range(n)
    ]


def _decision_context(items: list[dict]) -> dict:
    return build_decision_context(context={}, response_language="en", organizational_memory_context=items)


def _assessment(om_refs: list[str], **overrides) -> dict:
    base = {
        "reasoning_state": "aligned",
        "operational_assessment": "Evidence reviewed.",
        "company_brain_alignment": "cannot determine",
        "tensions": [],
        "evidence_gaps": [],
        "risk_assessment": "Low.",
        "confidence": 70,
        "recommendation_basis": {
            "evidence_basis": [],
            "company_basis": [],
            "missing_evidence": [],
            "organizational_memory_basis": om_refs,
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Field presence / empty / uncited behavior (items 1-3)
# ---------------------------------------------------------------------------

def test_cited_organizational_memory_always_present() -> None:
    dc = _decision_context([])
    result = build_public_explainability(reasoning_assessment=_assessment([]), decision_context=dc)
    assert result is not None
    assert "cited_organizational_memory" in result


def test_no_cited_om_returns_empty_list() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment([]), decision_context=dc)
    assert result["cited_organizational_memory"] == []


def test_om_context_present_but_uncited_returns_empty_list() -> None:
    """Item present in the prompt (via decision_context) but never cited
    in organizational_memory_basis -> zero public items, never all
    available history."""
    dc = _decision_context([_sample_item(), _sample_item(decision_memory_id="did-2")])
    result = build_public_explainability(reasoning_assessment=_assessment([]), decision_context=dc)
    assert result["cited_organizational_memory"] == []


# ---------------------------------------------------------------------------
# Basic citation resolution + presentation ids (items 4, 9-11)
# ---------------------------------------------------------------------------

def test_cited_om1_produces_exactly_one_public_item() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert len(result["cited_organizational_memory"]) == 1


def test_presentation_id_is_h1() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["id"] == "h1"


def test_multiple_cited_items_produce_deterministic_h1_h2() -> None:
    items = [_sample_item(decision_memory_id="did-1"), _sample_item(decision_memory_id="did-2")]
    dc = _decision_context(items)
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1", "OM2"]), decision_context=dc)
    ids = [item["id"] for item in result["cited_organizational_memory"]]
    assert ids == ["h1", "h2"]


def test_presentation_ids_follow_cited_order_not_durable_ids() -> None:
    """Citing OM2 before OM1 must assign h1 to OM2's content, h2 to OM1's
    content - presentation ids depend on CITATION order, never on the
    internal catalog's own OM# numbering or any durable id."""
    items = [
        _sample_item(decision_memory_id="did-1", decision_text="First decision."),
        _sample_item(decision_memory_id="did-2", decision_text="Second decision."),
    ]
    dc = _decision_context(items)
    result = build_public_explainability(reasoning_assessment=_assessment(["OM2", "OM1"]), decision_context=dc)
    cited = result["cited_organizational_memory"]
    assert cited[0]["id"] == "h1"
    assert cited[0]["decision"] == "Second decision."
    assert cited[1]["id"] == "h2"
    assert cited[1]["decision"] == "First decision."


# ---------------------------------------------------------------------------
# No internal/durable identifiers leak (items 5-8, 42-43)
# ---------------------------------------------------------------------------

def test_internal_om1_label_absent_from_public_item() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    serialized = str(result["cited_organizational_memory"])
    assert "OM1" not in serialized


def test_decision_memory_id_absent_from_public_item() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert "did-1" not in str(result["cited_organizational_memory"])


def test_outcome_memory_id_absent_from_public_item() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert "oid-1" not in str(result["cited_organizational_memory"])


def test_reasoning_receipt_id_absent_from_public_item() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert "reasoning_receipt_id" not in str(result["cited_organizational_memory"])


def test_no_uuid_like_value_leaks_through_public_om_object() -> None:
    dc = _decision_context([_sample_item(decision_memory_id="11111111-2222-3333-4444-555555555555")])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert "11111111-2222-3333-4444-555555555555" not in str(result["cited_organizational_memory"])


# ---------------------------------------------------------------------------
# Model-visible text derivation (items 12-19)
# ---------------------------------------------------------------------------

def test_public_decision_derives_from_canonical_snapshot() -> None:
    dc = _decision_context([_sample_item(decision_text="Approve expansion for 14 accounts.")])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["decision"] == "Approve expansion for 14 accounts."


def test_long_decision_matches_model_visible_truncated_form() -> None:
    long_text = "x" * (MAX_DECISION_TEXT_CHARS + 200)
    item = _sample_item(decision_text=long_text)
    dc = _decision_context([item])
    expected_snapshot = _build_organizational_memory_rendered_snapshot(item)
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["decision"] == expected_snapshot["decision"]
    assert "[truncated for prompt budget]" in result["cited_organizational_memory"][0]["decision"]
    assert result["cited_organizational_memory"][0]["decision"] != long_text


def test_public_rationale_derives_from_canonical_snapshot() -> None:
    dc = _decision_context([_sample_item(rationale="Cash coverage supports it.")])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["rationale"] == "Cash coverage supports it."


def test_long_rationale_matches_model_visible_truncated_form() -> None:
    long_text = "y" * (MAX_RATIONALE_CHARS + 200)
    item = _sample_item(rationale=long_text)
    dc = _decision_context([item])
    expected_snapshot = _build_organizational_memory_rendered_snapshot(item)
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["rationale"] == expected_snapshot["rationale"]
    assert "[truncated for prompt budget]" in result["cited_organizational_memory"][0]["rationale"]


def test_public_outcome_summary_derives_from_canonical_snapshot() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["outcomes"][0]["summary"] == "Delivered a real lift."


def test_long_outcome_summary_matches_model_visible_truncated_form() -> None:
    long_summary = "z" * (MAX_OUTCOME_SUMMARY_CHARS + 200)
    item = _sample_item(outcomes=[{**_sample_item()["outcomes"][0], "outcome_summary": long_summary}])
    dc = _decision_context([item])
    expected_snapshot = _build_organizational_memory_rendered_snapshot(item)
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    public_summary = result["cited_organizational_memory"][0]["outcomes"][0]["summary"]
    assert public_summary == expected_snapshot["outcomes"][0]["summary"]
    assert "[truncated for prompt budget]" in public_summary


def test_public_safety_sanitizer_applied_after_snapshot_construction() -> None:
    """A UUID embedded in the (already model-visible) rationale must be
    redacted by the existing _safe_public_prose boundary - proving
    sanitization is a step AFTER model-visible snapshot construction, not
    a replacement for it."""
    item = _sample_item(rationale="See 11111111-2222-3333-4444-555555555555 for detail.")
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["rationale"] is None


def test_sanitizer_never_falls_back_to_full_persisted_text() -> None:
    """A decision text containing an internal marker within the
    model-visible (truncated) portion must drop the WHOLE item - never
    fall back to substituting the full, untruncated persisted text as a
    workaround."""
    item = _sample_item(decision_text="Internal note: T5 was cited incorrectly here.")
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"] == []


# ---------------------------------------------------------------------------
# Atomic OM-item sanitization (fix round: one unsafe Outcome drops the
# WHOLE item, never just that Outcome - otherwise a public
# "N outcomes shown" + "omitted_outcomes_count" pair could be misread as
# N + omitted_outcomes_count = total historical outcomes, when the AI
# actually only ever saw the fixed model-visible subset.)
# ---------------------------------------------------------------------------

def _outcomes_with_one_unsafe(n: int, *, unsafe_index: int) -> list[dict]:
    outcomes = _outcomes(n)
    outcomes[unsafe_index] = {
        **outcomes[unsafe_index],
        "outcome_summary": "Contains 11111111-2222-3333-4444-555555555555 leaked id.",
    }
    return outcomes


def test_one_unsafe_model_visible_outcome_drops_entire_om_item() -> None:
    """8 active outcomes -> AI/prompt saw latest 5 (omitted_outcomes_count
    == 3). One of those 5 model-visible summaries is unsafe. The whole
    cited item must disappear - never 4-of-5 shown alongside
    omitted_outcomes_count=3, which would misrepresent the aggregate as
    4 + 3 = 7 historical outcomes instead of the true 8 (5 seen, 3
    context-budgeted)."""
    item = _sample_item(outcomes=_outcomes_with_one_unsafe(8, unsafe_index=4))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"] == []


def test_response_still_builds_normally_when_om_item_dropped() -> None:
    item = _sample_item(outcomes=_outcomes_with_one_unsafe(8, unsafe_index=4))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result is not None
    assert result["reasoning_state"] == "aligned"
    assert "cited_organizational_memory" in result


def test_no_partial_om_item_returned_when_one_outcome_unsafe() -> None:
    item = _sample_item(outcomes=_outcomes_with_one_unsafe(8, unsafe_index=4))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert len(result["cited_organizational_memory"]) == 0


def test_omitted_outcomes_count_not_exposed_for_dropped_item() -> None:
    item = _sample_item(outcomes=_outcomes_with_one_unsafe(8, unsafe_index=4))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert "omitted_outcomes_count" not in str(result["cited_organizational_memory"])


def test_sibling_safe_outcomes_not_exposed_alone_when_one_unsafe() -> None:
    item = _sample_item(outcomes=_outcomes_with_one_unsafe(8, unsafe_index=4))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    serialized = str(result["cited_organizational_memory"])
    for i in (3, 5, 6, 7):
        assert f"Summary {i}" not in serialized


def test_unsafe_outcome_at_edge_of_selection_still_drops_whole_item() -> None:
    item = _sample_item(outcomes=_outcomes_with_one_unsafe(8, unsafe_index=7))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"] == []


def test_unsafe_rationale_still_preserves_item_with_none_rationale_regression() -> None:
    """Regression (must remain unchanged by the fix round): an unsafe
    rationale degrades to None but the item, including all its safe
    outcomes, still survives - only an unsafe OUTCOME summary is atomic
    enough to drop the whole item."""
    item = _sample_item(rationale="See 11111111-2222-3333-4444-555555555555 for detail.", outcomes=_outcomes(3))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert len(result["cited_organizational_memory"]) == 1
    assert result["cited_organizational_memory"][0]["rationale"] is None
    assert len(result["cited_organizational_memory"][0]["outcomes"]) == 3


def test_all_safe_outcomes_return_full_model_visible_set_and_original_omitted_count() -> None:
    """Case A of the fix round's semantic example: 8 active outcomes, AI
    saw latest 5, all 5 safe -> public shows exactly those 5 plus the
    original context-budget omitted_outcomes_count of 3 (never altered by
    the sanitization step)."""
    item = _sample_item(outcomes=_outcomes(8))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    public_item = result["cited_organizational_memory"][0]
    assert len(public_item["outcomes"]) == 5
    assert public_item["omitted_outcomes_count"] == 3


# ---------------------------------------------------------------------------
# Outcome subset / chronology / omitted count (items 20-23)
# ---------------------------------------------------------------------------

def test_more_than_five_outcomes_exposes_same_latest_five() -> None:
    item = _sample_item(outcomes=_outcomes(8))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    outcomes = result["cited_organizational_memory"][0]["outcomes"]
    assert len(outcomes) == 5
    assert [o["summary"] for o in outcomes] == [f"Summary {i}" for i in range(3, 8)]


def test_selected_five_remain_oldest_to_newest() -> None:
    item = _sample_item(outcomes=_outcomes(8))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    observed_ats = [o["observed_at"] for o in result["cited_organizational_memory"][0]["outcomes"]]
    assert observed_ats == sorted(observed_ats)


def test_omitted_outcomes_count_matches_canonical_snapshot() -> None:
    item = _sample_item(outcomes=_outcomes(8))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["omitted_outcomes_count"] == 3


def test_five_or_fewer_outcomes_omitted_count_zero() -> None:
    item = _sample_item(outcomes=_outcomes(3))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["omitted_outcomes_count"] == 0


# ---------------------------------------------------------------------------
# Result-state fidelity, multiple outcomes (items 24-28)
# ---------------------------------------------------------------------------

def test_explicit_unknown_remains_unknown() -> None:
    item = _sample_item(outcomes=[{**_sample_item()["outcomes"][0], "result_state": "unknown"}])
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["outcomes"][0]["result_state"] == "unknown"


def test_positive_preserved() -> None:
    item = _sample_item(outcomes=[{**_sample_item()["outcomes"][0], "result_state": "positive"}])
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["outcomes"][0]["result_state"] == "positive"


def test_negative_preserved() -> None:
    item = _sample_item(outcomes=[{**_sample_item()["outcomes"][0], "result_state": "negative"}])
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["outcomes"][0]["result_state"] == "negative"


def test_mixed_preserved() -> None:
    item = _sample_item(outcomes=[{**_sample_item()["outcomes"][0], "result_state": "mixed"}])
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert result["cited_organizational_memory"][0]["outcomes"][0]["result_state"] == "mixed"


def test_multiple_outcomes_remain_separate_never_collapsed() -> None:
    item = _sample_item(outcomes=_outcomes(3, result_state="mixed"))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert len(result["cited_organizational_memory"][0]["outcomes"]) == 3


# ---------------------------------------------------------------------------
# No final-outcome / no causal wording (items 29-30)
# ---------------------------------------------------------------------------

def test_no_final_outcome_field_exists() -> None:
    item = _sample_item(outcomes=_outcomes(3))
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    public_item = result["cited_organizational_memory"][0]
    assert set(public_item.keys()) == {"id", "decision", "rationale", "decided_at", "outcomes", "omitted_outcomes_count"}
    for key in public_item:
        assert "final" not in key.lower()


def test_no_causal_statement_field_exists() -> None:
    item = _sample_item()
    dc = _decision_context([item])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    public_item = result["cited_organizational_memory"][0]
    for key in public_item:
        assert "cause" not in key.lower() and "causal" not in key.lower()


# ---------------------------------------------------------------------------
# Failure behavior: unresolved citation (items 31-33)
# ---------------------------------------------------------------------------

def test_unresolved_om_citation_is_skipped() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM99"]), decision_context=dc)
    assert result["cited_organizational_memory"] == []


def test_unresolved_om_citation_produces_warning_log(caplog) -> None:
    dc = _decision_context([_sample_item()])
    with caplog.at_level(logging.WARNING, logger="app.services.explainability"):
        build_public_explainability(reasoning_assessment=_assessment(["OM99"]), decision_context=dc)
    assert any("cited_organizational_memory" in record.message for record in caplog.records)


def test_unresolved_om_citation_does_not_fail_whole_explainability() -> None:
    dc = _decision_context([_sample_item()])
    result = build_public_explainability(reasoning_assessment=_assessment(["OM99"]), decision_context=dc)
    assert result is not None
    assert result["reasoning_state"] == "aligned"
    assert result["cited_organizational_memory"] == []


# ---------------------------------------------------------------------------
# Truth / Company Brain regression + three-category separation (items 34-40)
# ---------------------------------------------------------------------------

def test_no_second_db_query_introduced() -> None:
    """Structural: explainability.py imports no DB/pool/repository
    machinery at all - it is a pure function of already-in-memory data."""
    text = pathlib.Path("app/services/explainability.py").read_text(encoding="utf-8")
    assert "asyncpg" not in text
    assert "import asyncio" not in text
    assert "Repository(" not in text


def test_truth_cited_evidence_unchanged() -> None:
    dc = {
        "reasoning_reference_catalog": {
            "truth": {
                "T1": {
                    "is_usable_evidence": True,
                    "internal_source_item": {"canonical_field": "bird_balance", "source_filename": "x.xlsx"},
                }
            },
            "company_brain": {},
        },
        "organizational_memory_reference_catalog": {},
    }
    assessment = _assessment([])
    assessment["recommendation_basis"]["evidence_basis"] = ["T1"]
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=dc)
    assert len(result["cited_evidence"]) == 1
    assert result["cited_evidence"][0]["id"] == "e1"


def test_company_brain_cited_company_basis_unchanged() -> None:
    dc = {
        "reasoning_reference_catalog": {
            "truth": {},
            "company_brain": {
                "CB1": {"is_settled": True, "internal_source_item": {"key": "policy", "type": "POLICY", "statement": "x"}}
            },
        },
        "organizational_memory_reference_catalog": {},
    }
    assessment = _assessment([])
    assessment["recommendation_basis"]["company_basis"] = ["CB1"]
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=dc)
    assert len(result["cited_company_basis"]) == 1
    assert result["cited_company_basis"][0]["id"] == "c1"


def test_three_categories_remain_separate_arrays() -> None:
    dc = {
        "reasoning_reference_catalog": {
            "truth": {
                "T1": {
                    "is_usable_evidence": True,
                    "internal_source_item": {"canonical_field": "x", "source_filename": "x.xlsx"},
                }
            },
            "company_brain": {
                "CB1": {"is_settled": True, "internal_source_item": {"key": "k", "type": "POLICY", "statement": "s"}}
            },
        },
        "organizational_memory_reference_catalog": _build_organizational_memory_reference_catalog(
            [_sample_item()]
        ),
    }
    assessment = _assessment(["OM1"])
    assessment["recommendation_basis"]["evidence_basis"] = ["T1"]
    assessment["recommendation_basis"]["company_basis"] = ["CB1"]
    result = build_public_explainability(reasoning_assessment=assessment, decision_context=dc)
    assert len(result["cited_evidence"]) == 1
    assert len(result["cited_company_basis"]) == 1
    assert len(result["cited_organizational_memory"]) == 1
    # Never merged into one generic list.
    assert "cited_evidence" != "cited_organizational_memory"
    assert result["cited_evidence"][0] not in result["cited_organizational_memory"]


def test_existing_confidence_behavior_unchanged() -> None:
    dc = _decision_context([])
    result = build_public_explainability(reasoning_assessment=_assessment([], confidence=85), decision_context=dc)
    assert result["confidence"]["value"] == 85
    assert result["confidence"]["band"] == "high"


def test_existing_reasoning_state_behavior_unchanged() -> None:
    dc = _decision_context([])
    result = build_public_explainability(
        reasoning_assessment=_assessment([], reasoning_state="tension"), decision_context=dc
    )
    assert result["reasoning_state"] == "tension"


def test_all_original_public_fields_remain() -> None:
    original_fields = {
        "cited_evidence", "cited_company_basis", "confidence", "reasoning_state",
        "operational_assessment", "company_brain_alignment", "tensions", "evidence_gaps",
        "risk_assessment", "missing_evidence",
    }
    assert original_fields.issubset(set(PUBLIC_EXPLAINABILITY_FIELDS))


def test_new_field_included_in_public_fields_tuple() -> None:
    assert "cited_organizational_memory" in PUBLIC_EXPLAINABILITY_FIELDS


# ---------------------------------------------------------------------------
# Canonical snapshot / single-source-of-truth proofs (items 44-48)
# ---------------------------------------------------------------------------

def test_canonical_rendered_snapshot_has_no_durable_ids() -> None:
    snapshot = _build_organizational_memory_rendered_snapshot(_sample_item())
    serialized = str(snapshot)
    assert "did-1" not in serialized
    assert "oid-1" not in serialized
    assert set(snapshot.keys()) == {"decision", "rationale", "decided_at", "outcomes", "omitted_outcomes_count"}


def test_public_explainability_reads_rendered_snapshot_field() -> None:
    """Structural: explainability.py's OM resolution reads the catalog
    entry's rendered_snapshot key - the same one decision_context.py's
    prompt renderer reads - never recomputing truncation/selection itself."""
    text = pathlib.Path("app/services/explainability.py").read_text(encoding="utf-8")
    assert 'catalog_entry.get("rendered_snapshot")' in text
    assert "_truncate_for_prompt" not in text
    assert "_select_rendered_outcomes" not in text


def test_source_context_objects_unmutated_by_explainability() -> None:
    item = _sample_item()
    original = dict(item)
    dc = _decision_context([item])
    build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)
    assert item == original


def test_prompt_and_explainability_share_identical_snapshot_values() -> None:
    """End-to-end drift proof: the same decision_context, built once,
    yields prompt text and public explainability that both trace back to
    literally the same rendered_snapshot object - never two independently
    recomputed truncations that could disagree."""
    from app.services.decision_context import build_decision_context_prompt_block

    item = _sample_item(decision_text="x" * (MAX_DECISION_TEXT_CHARS + 50))
    dc = _decision_context([item])
    block = build_decision_context_prompt_block(dc)
    result = build_public_explainability(reasoning_assessment=_assessment(["OM1"]), decision_context=dc)

    public_decision_text = result["cited_organizational_memory"][0]["decision"]
    assert public_decision_text in block
    assert dc["organizational_memory_reference_catalog"]["OM1"]["rendered_snapshot"]["decision"] == public_decision_text


def test_sanitize_organizational_memory_item_helper_directly() -> None:
    snapshot = {
        "decision": "Approve expansion.",
        "rationale": None,
        "decided_at": "2020-01-01T00:00:00Z",
        "outcomes": [{"result_state": "positive", "summary": "Delivered.", "observed_at": "2020-02-01T00:00:00Z"}],
        "omitted_outcomes_count": 0,
    }
    sanitized = _sanitize_organizational_memory_item(snapshot, "h1")
    assert sanitized == {
        "id": "h1",
        "decision": "Approve expansion.",
        "rationale": None,
        "decided_at": "2020-01-01T00:00:00Z",
        "outcomes": [{"result_state": "positive", "summary": "Delivered.", "observed_at": "2020-02-01T00:00:00Z"}],
        "omitted_outcomes_count": 0,
    }


def test_resolve_cited_organizational_memory_helper_directly() -> None:
    catalog = _build_organizational_memory_reference_catalog([_sample_item()])
    result = _resolve_cited_organizational_memory(
        organizational_memory_basis=["OM1"], organizational_memory_reference_catalog=catalog
    )
    assert len(result) == 1
    assert result[0]["id"] == "h1"


def test_resolve_cited_organizational_memory_non_list_basis_returns_empty() -> None:
    catalog = _build_organizational_memory_reference_catalog([_sample_item()])
    assert _resolve_cited_organizational_memory(
        organizational_memory_basis=None, organizational_memory_reference_catalog=catalog
    ) == []


# ---------------------------------------------------------------------------
# Migration / non-goal safety (items 55-56)
# ---------------------------------------------------------------------------

def test_migrations_still_001_through_014() -> None:
    """M8 boundary invariant: migration 014 is present, unrenamed.
    (Historical note: this test previously also asserted no migration
    015 existed; that assertion became obsolete once Founder-approved
    M9 Slice 1 added migration 015, and has been removed - it was never
    the real invariant this M8 slice needed, which is that 001-014
    remain intact, not that no future milestone may ever add one.)"""
    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert "014_organizational_memory.sql" in migration_files


def test_migration_014_checksum_unchanged() -> None:
    import hashlib

    digest = hashlib.sha256(pathlib.Path("migrations/014_organizational_memory.sql").read_bytes()).hexdigest()
    assert digest == "8e30a9b8bb7c73f226ac8bf8eb1a751ddb311c82404c5f635fd995c46a378710"


# ---------------------------------------------------------------------------
# Protected-file boundaries (structural)
# ---------------------------------------------------------------------------

def test_no_receipt_or_ome_import_in_explainability() -> None:
    text = pathlib.Path("app/services/explainability.py").read_text(encoding="utf-8")
    assert "app.ome" not in text


def test_no_frontend_files_touched() -> None:
    assert not list(pathlib.Path("frontend/src").rglob("*organizational_memory*"))
