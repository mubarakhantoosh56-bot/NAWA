"""M7 Slice 2A/2B: public explainability contract.

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

M7 Slice 2B extends this same contract with the FINAL accepted candidate's
own safe executive-provenance fields (reasoning_state,
operational_assessment, company_brain_alignment, tensions, evidence_gaps,
risk_assessment) and a structured, server-resolved missing_evidence list -
never a second model call, never new reasoning, never chain-of-thought.
Every field here is a passthrough of what M6 already validated; nothing is
recomputed, summarized, or inferred here.

Must be called ONLY after every legacy/operational/M6 validator has already
accepted the candidate as final - see app/services/openai_client.py's
placement immediately before log_decision_event, after the M6 repair
branch (if any) has fully settled `parsed`.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.reasoning_validation import REASONING_STATES

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
# dict-building code. missing_evidence entries reuse this exact same shape
# (Slice 2B Section 10: "prefer reusing the existing safe evidence
# sanitizer").
EVIDENCE_PUBLIC_FIELDS = ("id", "label", "filename", "report_date", "entity", "epistemic_origin", "source_time_status")
COMPANY_BASIS_PUBLIC_FIELDS = ("id", "label", "type", "statement")

# M7 Slice 2B: the complete top-level public explainability contract - the
# ONLY keys build_public_explainability() may ever return. Documented here
# for the same auditability reason as the field allowlists above.
PUBLIC_EXPLAINABILITY_FIELDS = (
    "cited_evidence",
    "cited_company_basis",
    "confidence",
    "reasoning_state",
    "operational_assessment",
    "company_brain_alignment",
    "tensions",
    "evidence_gaps",
    "risk_assessment",
    "missing_evidence",
)


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


# M7 Slice 2B Correction Round 1 (H-01): M6 validates only that
# operational_assessment/risk_assessment/tensions/evidence_gaps are
# non-empty strings - it does not and must not police their CONTENT. A
# structurally valid, fully-accepted final candidate can still write an
# internal reference token, a UUID, an internal filesystem/storage path,
# or an explicit internal/debug marker into otherwise-legitimate prose.
# These patterns are the PUBLIC PRESENTATION boundary's own content
# check - independent of and in addition to M6's structural validation.

# Standalone T#/CB# tokens only (word-boundary anchored) - never matches
# a T+digits substring embedded inside a larger identifier (e.g. never
# fires inside "PRODUCT3" or "5T3", since \b requires a transition
# between a word and non-word character immediately before the letter).
_INTERNAL_REF_PATTERN = re.compile(r"\b(?:T|CB)\d+\b")

# Canonical UUID form (8-4-4-4-12 hex).
_UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)

# Internal filesystem/storage path forms actually realistic for this
# platform (Section 7) - deliberately NOT a generic URL filter (a normal
# "https://" URL never matches: the \b before the drive letter fails
# inside "http[s]:" because the preceding character is a word character,
# not a boundary).
#
# The forward-slash "storage/" form is deliberately narrower than a bare
# "storage/word" substring match, because that would false-positive on
# legitimate business phrases like "storage/warehouse capacity" (this
# codebase has no actual bare `storage/word` path convention, only
# provenance fields like source_filename). It fires on either of two
# shapes, both clearly path-like rather than ordinary prose:
#   A. storage/<segment>/<segment>[...]  - TWO OR MORE slash-separated
#      segments (Correction Round 2, H-01-R1: catches nested paths such
#      as "storage/files/abc" or "storage/uploads/company/report.xlsx"
#      even without a file extension on the final segment).
#   B. storage/<segment>.<ext>            - a single segment with a
#      file-extension-like suffix (e.g. "storage/secret.xlsx").
# Ordinary prose like "storage/warehouse capacity" has only one
# slash-separated token before a space, so it matches neither shape.
_INTERNAL_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:[\\/]"
    r"|(?<!\w)/(?:mnt|home|tmp|var)/"
    r"|(?<!\w)storage\\"
    r"|(?<!\w)storage/[\w.-]+/[\w.-]+"
    r"|(?<!\w)storage/[\w.-]+\.[A-Za-z0-9]{1,5}\b"
)

# Correction Round 3 (M7-2B-R2-URL): a public http(s):// URL legitimately
# containing a path segment that happens to look like an internal storage
# path (e.g. https://example.com/storage/files/report) is not itself a
# leak - it is just part of a normal, already-public link. Recognized
# ONLY for http/https (never file://, vscode://, or any other scheme -
# those get no exemption). Bounded at whitespace/quote/angle-bracket
# characters so it can never swallow unrelated prose after a space (see
# _contains_internal_path_outside_public_url's own docstring).
_PUBLIC_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")

# Explicit private-implementation/debug markers (Section 8) - case-
# insensitive substring match, since these are specific multi-word or
# snake_case technical tokens that do not occur in ordinary executive
# business prose. This is NOT semantic chain-of-thought detection (the
# application never has access to a model's actual hidden reasoning) -
# it only catches an explicit, literal internal/debug-artifact string
# that leaked into otherwise-approved prose.
_INTERNAL_MARKER_TERMS = (
    "reasoning_reference_catalog",
    "internal_source_item",
    "reasoning_signals",
    "logic_json",
    "meta.context",
    "source_file_id",
    "source_company_id",
    "source_department_id",
    "evidence_basis",
    "company_basis",
    "chain of thought",
    "chain-of-thought",
    "internal reasoning",
    "scratchpad",
    "system prompt",
    "developer message",
)


def _contains_internal_path_outside_public_url(value: str) -> bool:
    """Correction Round 3 (M7-2B-R2-URL): an _INTERNAL_PATH_PATTERN match
    that falls ENTIRELY inside a recognized public http(s):// URL span is
    not treated as a leaked internal filesystem/storage path - it is
    simply part of an already-public link. Any match OUTSIDE every
    recognized URL span still fails closed, including a second, genuinely
    internal path elsewhere in the same string (e.g. "...see
    https://example.com/storage/files/report and inspect
    storage/private/report.json" still fails closed because of the
    second match). URL spans stop at whitespace/quotes/angle brackets, so
    a path after a space is never accidentally swallowed into the
    "public" span. This is narrowly scoped to path matching only - it
    never exempts T#/CB# refs, UUIDs, or internal/debug markers merely
    because they appear inside a URL (those checks in _safe_public_prose
    run unconditionally on the whole string, unaffected by this
    function)."""
    url_spans = [match.span() for match in _PUBLIC_URL_PATTERN.finditer(value)]
    for path_match in _INTERNAL_PATH_PATTERN.finditer(value):
        match_start, match_end = path_match.span()
        if not any(url_start <= match_start and match_end <= url_end for url_start, url_end in url_spans):
            return True
    return False


def _safe_public_prose(value: Any) -> str | None:
    """The public presentation boundary for FREE-FORM executive prose
    (operational_assessment, risk_assessment, and each tensions/
    evidence_gaps item). Preserves safe prose completely unchanged -
    ordinary numbers, percentages, dates, hall numbers, product names,
    and normal English/Arabic business language all survive verbatim.
    Fails closed at WHOLE-FIELD granularity: if any prohibited pattern is
    detected anywhere in the string, the entire value is dropped rather
    than redacted/rewritten in place, since surgically removing a
    fragment could change the sentence's meaning. M6 stays valid
    internally either way - this never reopens or re-validates the
    candidate, it only decides what the already-accepted candidate's own
    prose is allowed to say publicly."""
    if not isinstance(value, str):
        return None
    if _INTERNAL_REF_PATTERN.search(value):
        return None
    if _UUID_PATTERN.search(value):
        return None
    if _contains_internal_path_outside_public_url(value):
        return None
    lowered = value.lower()
    for marker in _INTERNAL_MARKER_TERMS:
        if marker in lowered:
            return None
    return value


def _safe_public_prose_list(value: Any) -> list[str]:
    """Same rule as _safe_public_prose, applied per item: an unsafe item
    is dropped, safe neighboring items survive unchanged and in order."""
    if not isinstance(value, list):
        return []
    safe_items: list[str] = []
    for item in value:
        safe_item = _safe_public_prose(item)
        if safe_item is not None:
            safe_items.append(safe_item)
    return safe_items


# M7 Slice 2B Correction Round 1 (H-01, Section 10): company_brain_alignment
# is NOT arbitrary prose - it already has a frozen controlled vocabulary
# enforced at the prompt level (see decision_context.py's
# company_brain_alignment_vocabulary_instruction). Public presentation uses
# an EXACT-VALUE allowlist rather than the generic prose filter above: a
# string that merely CONTAINS one of these plus extra text (e.g. "supported
# by current evidence - see T3") is not a match and fails closed to None,
# never a frontend semantic fallback.
COMPANY_BRAIN_ALIGNMENT_ALLOWED_VALUES = (
    "supported by current evidence",
    "not supported by current evidence",
    "partially supported",
    "cannot determine",
    "مدعوم بالأدلة الحالية",
    "غير مدعوم بالأدلة الحالية",
    "مدعوم جزئيًا",
    "لا يمكن التحديد",
)


def _safe_company_brain_alignment(value: Any) -> str | None:
    """Exact-value allowlist only - never altered, never given a
    generic-prose pass, never mapped to a fallback label."""
    return value if isinstance(value, str) and value in COMPANY_BRAIN_ALIGNMENT_ALLOWED_VALUES else None


def _safe_reasoning_state(value: Any) -> str | None:
    """Passthrough of the FINAL accepted reasoning_state - restricted to
    the exact same closed enum M6 validates (aligned/tension/
    insufficient_evidence), never a fourth value, never translated here
    (frontend-only localization of the display label, per Slice 2B
    Section 7)."""
    return value if isinstance(value, str) and value in REASONING_STATES else None


def _resolve_missing_evidence(
    *,
    missing_evidence_refs: Any,
    truth_refs: dict[str, Any],
) -> list[dict[str, Any]]:
    """M7 Slice 2B Section 9: resolve the FINAL accepted candidate's
    recommendation_basis.missing_evidence T# refs against the SAME
    authoritative turn-local reference catalog cited_evidence already uses
    - through each entry's own internal_source_item snapshot, never by
    parsing the ref's numeric suffix and indexing into
    operational_truth_context (the exact positional bug fixed for
    cited_evidence in Correction Round 1, 2A-F4). A valid missing-evidence
    ref must satisfy the catalog's own is_gap_reference (missing OR
    unresolved source time) rather than is_usable_evidence - citing an
    available, resolved item as a "gap" is invalid and skipped
    (fail-closed), never fabricated. Reuses _sanitize_evidence_item so a
    gap item is described with the exact same safe field allowlist as
    cited evidence (Section 10: "prefer reusing the existing safe evidence
    sanitizer")."""
    if not isinstance(missing_evidence_refs, list):
        return []

    resolved: list[dict[str, Any]] = []
    for position, ref in enumerate(missing_evidence_refs, start=1):
        if not isinstance(ref, str):
            continue
        catalog_entry = truth_refs.get(ref)
        if not catalog_entry or not catalog_entry.get("is_gap_reference"):
            continue
        item = catalog_entry.get("internal_source_item")
        if not isinstance(item, dict):
            continue
        resolved.append(_sanitize_evidence_item(item, f"m{position}"))
    return resolved


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
        # M7 Slice 2B: safe executive-provenance passthrough from the SAME
        # final accepted reasoning_assessment - never recomputed, never
        # summarized by another model call, never frontend-inferred.
        # Correction Round 1 (H-01): free-form prose fields pass through
        # the public-prose safety boundary; company_brain_alignment uses
        # its own exact-value allowlist instead (Section 10).
        "reasoning_state": _safe_reasoning_state(reasoning_assessment.get("reasoning_state")),
        "operational_assessment": _safe_public_prose(reasoning_assessment.get("operational_assessment")),
        "company_brain_alignment": _safe_company_brain_alignment(
            reasoning_assessment.get("company_brain_alignment")
        ),
        "tensions": _safe_public_prose_list(reasoning_assessment.get("tensions")),
        "evidence_gaps": _safe_public_prose_list(reasoning_assessment.get("evidence_gaps")),
        "risk_assessment": _safe_public_prose(reasoning_assessment.get("risk_assessment")),
        "missing_evidence": _resolve_missing_evidence(
            missing_evidence_refs=recommendation_basis.get("missing_evidence"),
            truth_refs=truth_refs,
        ),
    }
