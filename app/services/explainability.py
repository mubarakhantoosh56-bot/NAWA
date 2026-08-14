"""M7 Slice 2A: public explainability contract.

Builds a small, sanitized, human-readable summary of the FINAL accepted M6
reasoning_assessment for the public API response. Resolved ONLY from the
already-built, already-tenant/department-scoped decision_context's
reasoning_reference_catalog for THIS turn - never a second independent
Truth/Company Brain lookup, never a new database read.

Frozen boundary (Founder/CTO ruling, M7 Slice 2A): T#/CB# are internal
backend reference IDs and must never reach the public contract. Only
already-cited, already-validated evidence/company-basis items are
summarized here, through an explicit field allowlist. Uncited material,
internal UUIDs, filesystem/storage paths, and internal row IDs are never
included. This module never fabricates a value: an unresolved/missing
field stays unresolved/missing (None), never guessed.

Must be called ONLY after every legacy/operational/M6 validator has already
accepted the candidate as final - see app/services/openai_client.py's
placement immediately before log_decision_event, after the M6 repair
branch (if any) has fully settled `parsed`.
"""

from __future__ import annotations

from typing import Any

CONFIDENCE_BAND_LOW = "low"
CONFIDENCE_BAND_MODERATE = "moderate"
CONFIDENCE_BAND_HIGH = "high"
CONFIDENCE_BANDS = (CONFIDENCE_BAND_LOW, CONFIDENCE_BAND_MODERATE, CONFIDENCE_BAND_HIGH)

# Closed enum - deterministic backend facts only, never LLM-invented prose.
# These are the three driver classes already implied by M6's own prompt
# rules (see decision_context.py's "Confidence must go down..." rule) -
# not new reasoning, just a structured surface for facts M6 already tracks.
DRIVER_MISSING_EVIDENCE = "missing_evidence"
DRIVER_UNRESOLVED_SOURCE_TIME = "unresolved_source_time"
DRIVER_CONFLICTED_COMPANY_BASIS = "conflicted_company_basis"
CONFIDENCE_DRIVERS = (
    DRIVER_MISSING_EVIDENCE,
    DRIVER_UNRESOLVED_SOURCE_TIME,
    DRIVER_CONFLICTED_COMPANY_BASIS,
)

# Section 5/6's explicit allowlists - the ONLY fields that may ever appear
# in public cited_evidence / cited_company_basis entries. Documented here so
# the allowlist is auditable in one place rather than implied by scattered
# dict-building code.
EVIDENCE_PUBLIC_FIELDS = ("id", "label", "filename", "report_date", "entity", "epistemic_origin", "source_time_status")
COMPANY_BASIS_PUBLIC_FIELDS = ("id", "label", "type", "statement")


def _confidence_band(value: int) -> str:
    """Deterministic, documented three-band mapping. No canonical
    confidence-threshold convention existed elsewhere in this codebase at
    the time this was introduced (M7 Slice 2A) - this is the smallest
    explicit deterministic split: 0-39 low, 40-69 moderate, 70-100 high.
    Never described as a probability of correctness - see the confidence
    field's own docstring in reasoning_validation.py for why (StrictInt
    0..100 is a model self-report, not a calibrated probability)."""
    if value < 40:
        return CONFIDENCE_BAND_LOW
    if value < 70:
        return CONFIDENCE_BAND_MODERATE
    return CONFIDENCE_BAND_HIGH


def _confidence_drivers(
    *,
    recommendation_basis: dict[str, Any],
    reasoning_reference_catalog: dict[str, Any],
) -> list[str]:
    """Every driver here is read directly off structural facts the
    reference catalog / recommendation_basis already carry this turn -
    never derived from reasoning_assessment prose text."""
    drivers: list[str] = []
    truth_refs = reasoning_reference_catalog.get("truth") or {}
    company_refs = reasoning_reference_catalog.get("company_brain") or {}

    if recommendation_basis.get("missing_evidence"):
        drivers.append(DRIVER_MISSING_EVIDENCE)

    cited_evidence_refs = recommendation_basis.get("evidence_basis") or []
    if any((truth_refs.get(ref) or {}).get("is_unresolved_time") for ref in cited_evidence_refs):
        drivers.append(DRIVER_UNRESOLVED_SOURCE_TIME)

    # Scoped to this turn's own bounded Company Brain catalog (never a
    # fresh/global lookup) - true when ANY company-brain item relevant to
    # this turn is internally conflicted, matching decision_context.py's
    # own prompt rule that a conflicted item must degrade confidence,
    # regardless of whether that specific item happened to be cited (a
    # conflicted item can never itself be validly cited - see is_settled).
    if any((entry or {}).get("is_conflicted") for entry in company_refs.values()):
        drivers.append(DRIVER_CONFLICTED_COMPANY_BASIS)

    return drivers


def _sanitize_evidence_item(item: dict[str, Any], presentation_id: str) -> dict[str, Any]:
    """Deterministic backend label construction from real provenance only
    (Section 5) - never an LLM-generated filename/label when the
    deterministic source field is available. `filename` reads
    source_filename (M7-01's clean, path-free provenance field) - never
    source_file (a raw filesystem/storage path) and never source_file_id/
    source_company_id/source_department_id (internal UUIDs)."""
    entity_type = item.get("entity_type")
    entity_reference = item.get("entity_reference")
    entity = {"type": entity_type, "reference": entity_reference} if (entity_type or entity_reference) else None
    return {
        "id": presentation_id,
        "label": item.get("canonical_field") or item.get("type"),
        "filename": item.get("source_filename"),
        # Preserve unresolved state exactly - source_time is already None
        # whenever the source's own report/snapshot time is unresolved
        # (see app/oce/models/evidence.py); never substituted with
        # ingestion time or "now".
        "report_date": item.get("source_time"),
        "entity": entity,
        "epistemic_origin": item.get("epistemic_origin"),
        "source_time_status": item.get("source_time_status"),
    }


def _sanitize_company_basis_item(item: dict[str, Any], presentation_id: str) -> dict[str, Any]:
    """`statement` is the actual policy/doctrine text (CompanyBrainItem's
    own human-readable field - never a raw document dump); `label` is the
    section/fact heading. Internal authority/source-table metadata is
    intentionally not exposed (Section 6: 'raw internal authority metadata
    unless strictly required' - not required for an executive summary)."""
    return {
        "id": presentation_id,
        "label": item.get("key"),
        "type": item.get("type"),
        "statement": item.get("statement"),
    }


def build_public_explainability(
    *,
    reasoning_assessment: dict[str, Any] | None,
    decision_context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Resolve the FINAL accepted candidate's cited T#/CB# refs against
    the already-built reasoning_reference_catalog for this turn, and
    return a small sanitized public summary - or None if there is nothing
    valid to explain.

    Fail-closed by construction (Section 7): a ref that is missing from
    the catalog, or present but not usable/settled, is silently skipped
    rather than summarized - this never fabricates an explanation for an
    invalid reference. In normal operation every ref here was already
    proven valid+usable/settled by validate_reasoning_assessment before
    this function is ever called; these checks are defensive
    reinforcement of that same boundary, not the primary enforcement.

    M7 Slice 2A-F4: resolution is ALWAYS through the catalog entry's own
    ``internal_source_item`` snapshot (captured by
    decision_context._build_reasoning_reference_catalog at the exact
    moment T#/CB# was assigned) - never by parsing the numeric suffix out
    of the ref string and indexing into operational_truth_context/
    company_brain_context. Those lists may be freely reordered by the
    caller after the catalog was built; the catalog itself is the only
    authoritative mapping from a reference to the item that earned it. If
    a catalog entry has no valid snapshot, that citation is skipped
    (fail-closed) rather than falling back to list-position guessing.
    """
    if not isinstance(reasoning_assessment, dict) or not isinstance(decision_context, dict):
        return None

    recommendation_basis = reasoning_assessment.get("recommendation_basis")
    if not isinstance(recommendation_basis, dict):
        return None

    reasoning_reference_catalog = decision_context.get("reasoning_reference_catalog")
    if not isinstance(reasoning_reference_catalog, dict):
        return None

    truth_refs = reasoning_reference_catalog.get("truth") or {}
    company_refs = reasoning_reference_catalog.get("company_brain") or {}

    cited_evidence: list[dict[str, Any]] = []
    for position, ref in enumerate(recommendation_basis.get("evidence_basis") or [], start=1):
        if not isinstance(ref, str):
            continue
        catalog_entry = truth_refs.get(ref)
        if not catalog_entry or not catalog_entry.get("is_usable_evidence"):
            continue
        item = catalog_entry.get("internal_source_item")
        if not isinstance(item, dict):
            continue
        cited_evidence.append(_sanitize_evidence_item(item, f"e{position}"))

    cited_company_basis: list[dict[str, Any]] = []
    for position, ref in enumerate(recommendation_basis.get("company_basis") or [], start=1):
        if not isinstance(ref, str):
            continue
        catalog_entry = company_refs.get(ref)
        if not catalog_entry or not catalog_entry.get("is_settled"):
            continue
        item = catalog_entry.get("internal_source_item")
        if not isinstance(item, dict):
            continue
        cited_company_basis.append(_sanitize_company_basis_item(item, f"c{position}"))

    confidence: dict[str, Any] | None = None
    raw_confidence = reasoning_assessment.get("confidence")
    if isinstance(raw_confidence, int) and not isinstance(raw_confidence, bool):
        confidence = {
            "value": raw_confidence,
            "band": _confidence_band(raw_confidence),
            "drivers": _confidence_drivers(
                recommendation_basis=recommendation_basis,
                reasoning_reference_catalog=reasoning_reference_catalog,
            ),
        }

    return {
        "cited_evidence": cited_evidence,
        "cited_company_basis": cited_company_basis,
        "confidence": confidence,
    }
