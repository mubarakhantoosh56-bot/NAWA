"""M6: runtime-enforced validation for raw_decision.reasoning_assessment.

Two independent, required checks:

1. Structural validation (Pydantic) - reasoning_assessment must be present,
   non-null, non-empty, and every field must have the exact required type:
   reasoning_state is exactly one of aligned/tension/insufficient_evidence,
   confidence is numeric in [0, 100], the four string fields are strings,
   tensions/evidence_gaps are list[str], and recommendation_basis is an
   object with three list[str] fields. Nothing about prose STYLE is
   validated beyond this - only safe structure.

2. Decision-provenance validation - every recommendation_basis reference
   must be a real T#/CB# id that was actually supplied to reasoning this
   turn (app/services/decision_context.py's reasoning_reference_catalog,
   itself built only from the M4/M5 contexts already assembled for this
   one request - nothing is reloaded here). company_basis references must
   additionally be settled (not conflicted/unresolved) Company Brain
   context; missing_evidence references must be genuine gaps (missing or
   unresolved source time), never available/resolved evidence.

This module never calls an LLM, never reloads M4/M5 sources, and never
persists anything - it is a pure function of the one turn's parsed model
output and the one turn's already-built decision_context.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.decision_context import reasoning_language_contract

from pydantic import BaseModel, ConfigDict, StrictInt, ValidationError, field_validator

REASONING_STATES = ("aligned", "tension", "insufficient_evidence")

_TRUTH_REF_RE = re.compile(r"^T\d+$")
_COMPANY_BRAIN_REF_RE = re.compile(r"^CB\d+$")


class RecommendationBasis(BaseModel):
    """Decision-provenance references only - never free-text citations."""

    model_config = ConfigDict(extra="forbid")

    evidence_basis: list[str]
    company_basis: list[str]
    missing_evidence: list[str]


class ReasoningAssessment(BaseModel):
    """Structural shape of raw_decision.reasoning_assessment. Auditable
    decision provenance only - never chain-of-thought (no field here asks
    for or accepts step-by-step internal deliberation)."""

    model_config = ConfigDict(extra="forbid")

    reasoning_state: str
    operational_assessment: str
    company_brain_alignment: str
    tensions: list[str]
    evidence_gaps: list[str]
    risk_assessment: str
    # M6-R3: a JSON integer only. StrictInt rejects numeric strings ("50"),
    # non-integer floats (50.5), and - because Pydantic's strict-int check
    # explicitly excludes bool despite bool being an int subclass in raw
    # Python - True/False as well. No implicit coercion of any kind.
    confidence: StrictInt
    recommendation_basis: RecommendationBasis

    @field_validator("reasoning_state")
    @classmethod
    def _valid_reasoning_state(cls, value: str) -> str:
        if value not in REASONING_STATES:
            raise ValueError(f"must be one of {REASONING_STATES}, got {value!r}")
        return value

    @field_validator("confidence")
    @classmethod
    def _confidence_in_bounds(cls, value: int) -> int:
        if not (0 <= value <= 100):
            raise ValueError(f"must be within [0, 100], got {value!r}")
        return value


def validate_reasoning_assessment(
    parsed: dict[str, Any] | None,
    decision_context: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    """Validate raw_decision.reasoning_assessment structurally and against
    this turn's reference catalog. Returns (is_valid, error_messages).
    Never raises - a malformed ``parsed`` is itself a validation failure,
    not an exception.
    """
    if not isinstance(parsed, dict):
        return False, ["reasoning_assessment: response is not a JSON object"]

    raw_decision = parsed.get("raw_decision")
    if not isinstance(raw_decision, dict):
        return False, ["reasoning_assessment: raw_decision is missing or not an object"]

    raw_assessment = raw_decision.get("reasoning_assessment")
    if raw_assessment is None:
        return False, ["reasoning_assessment: field is required and must not be missing or null"]
    if not isinstance(raw_assessment, dict):
        return False, ["reasoning_assessment: field must be an object"]
    if not raw_assessment:
        return False, ["reasoning_assessment: field must not be an empty object"]

    try:
        assessment = ReasoningAssessment.model_validate(raw_assessment)
    except ValidationError as exc:
        return False, [
            f"reasoning_assessment.{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        ]

    reference_catalog = (decision_context or {}).get("reasoning_reference_catalog") or {}
    truth_refs: dict[str, Any] = reference_catalog.get("truth") or {}
    company_brain_refs: dict[str, Any] = reference_catalog.get("company_brain") or {}

    errors: list[str] = []
    basis = assessment.recommendation_basis

    for ref in basis.evidence_basis:
        if not _TRUTH_REF_RE.match(ref):
            errors.append(
                f"recommendation_basis.evidence_basis: '{ref}' is not a valid T# reference"
            )
        elif ref not in truth_refs:
            errors.append(
                f"recommendation_basis.evidence_basis: '{ref}' was not supplied in this turn's "
                "Operational Truth Context"
            )
        elif not truth_refs[ref].get("is_usable_evidence"):
            # M6-R1: "exists this turn" is not "is valid supporting
            # evidence" - MISSING, INFERRED-only, and anything not
            # AVAILABLE+OBSERVED/DERIVED must never be cited as evidence
            # basis. An unresolved source time does NOT disqualify a usable
            # item (Feed Mill Golden Case) - only is_usable_evidence itself
            # (status=available + origin in observed/derived) matters here.
            errors.append(
                f"recommendation_basis.evidence_basis: '{ref}' is not usable supporting evidence "
                "(missing, inferred-only, or unavailable) - only AVAILABLE items with an OBSERVED or "
                "DERIVED origin may be cited as evidence_basis"
            )

    for ref in basis.company_basis:
        if not _COMPANY_BRAIN_REF_RE.match(ref):
            errors.append(
                f"recommendation_basis.company_basis: '{ref}' is not a valid CB# reference"
            )
        elif ref not in company_brain_refs:
            errors.append(
                f"recommendation_basis.company_basis: '{ref}' was not supplied in this turn's "
                "Company Brain Context"
            )
        elif not company_brain_refs[ref].get("is_settled"):
            errors.append(
                f"recommendation_basis.company_basis: '{ref}' is conflicted/unresolved Company "
                "Brain context, not settled policy - it may not be used as company_basis; describe "
                "it in tensions/evidence_gaps instead"
            )

    for ref in basis.missing_evidence:
        if not _TRUTH_REF_RE.match(ref):
            errors.append(
                f"recommendation_basis.missing_evidence: '{ref}' is not a valid T# reference"
            )
        elif ref not in truth_refs:
            errors.append(
                f"recommendation_basis.missing_evidence: '{ref}' was not supplied in this turn's "
                "Operational Truth Context"
            )
        elif not truth_refs[ref].get("is_gap_reference"):
            errors.append(
                f"recommendation_basis.missing_evidence: '{ref}' is available, resolved evidence, "
                "not a gap - missing_evidence may only reference missing or unresolved-source-time items"
            )

    return (not errors, errors)


def build_reasoning_assessment_repair_instruction(
    *, errors: list[str], response_language: str
) -> str:
    """Bounded repair instruction: states only what is invalid and the
    contract rules - never asks the model to expose chain-of-thought or to
    invent a reference to satisfy validation."""
    joined = "\n".join(f"- {error}" for error in errors)
    return (
        "Your previous response failed NAWA's M6 reasoning_assessment runtime validation. "
        "Regenerate the FULL valid JSON response once, fixing ONLY these problems:\n"
        f"{joined}\n"
        "Contract rules:\n"
        "- raw_decision.reasoning_assessment is REQUIRED and must be a non-empty object.\n"
        "- reasoning_state must be exactly one of: aligned, tension, insufficient_evidence.\n"
        "- confidence must be a number between 0 and 100 (not a string, not out of range).\n"
        "- tensions and evidence_gaps must be JSON arrays of strings (never a single string).\n"
        "- recommendation_basis.evidence_basis may ONLY contain T# reference IDs that are USABLE "
        "supporting evidence: AVAILABLE with an OBSERVED or DERIVED origin. A missing, inferred-only, "
        "or unavailable T# may never be used as evidence_basis (an unresolved source time alone does "
        "NOT disqualify an otherwise usable item).\n"
        "- recommendation_basis.company_basis may ONLY contain CB# reference IDs that are AUTHORITATIVE "
        "settled company doctrine: a curated policy-type item (not INSTITUTIONAL_MEMORY) whose authority "
        "is exactly 'authoritative' and which is not conflicted. Any other authority value (missing, "
        "'unresolved', 'institutional', or anything else) may never be used as company_basis.\n"
        "- recommendation_basis.missing_evidence may ONLY reference T# items that are themselves "
        "missing or have unresolved source time.\n"
        "- Do NOT invent a reference ID that was not already supplied to you - if no valid reference "
        "applies, use an empty list for that field instead.\n"
        "- Do NOT explain your reasoning process outside the JSON fields; only populate the structured "
        "fields themselves.\n"
        f"Keep executive_summary in response_language={response_language}. Return only JSON.\n"
        # 2A-F1 (Correction Round 1): re-assert the full reasoning-language
        # contract here too - a repair prompt is the newest, most specific
        # instruction the model sees, so it must not be silent on prose
        # language/vocabulary merely because the initial prompt already
        # stated it.
        f"{reasoning_language_contract(response_language)}"
    )
