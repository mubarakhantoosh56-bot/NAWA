"""Server-internal provenance extraction for live reasoning receipts (M8
Slice 3A).

Two pure, server-only helpers - one per provenance category persisted in
ome_reasoning_receipts.evidence_refs (see app/ome/types.py):
build_truth_evidence_refs (Truth, category="truth") and
build_company_brain_provenance_refs (Company Brain, category=
"company_brain"). Both resolve ONLY the labels a reasoning turn's FINAL
accepted assessment actually cited
(reasoning_assessment.recommendation_basis.evidence_basis /
.company_basis) against that SAME turn's already-built, server-owned
reasoning_reference_catalog (app/services/decision_context.py) - never
rereads a knowledge file or an uploaded file's content, never queries
current source state, never trusts any client-supplied field.

Wired live from app/services/openai_client.py's AIService.chat() - see
that module's _create_live_reasoning_receipt for the exact call site and
ordering guarantees.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.ome.errors import InvalidMemoryInput
from app.ome.types import CompanyBrainProvenanceRef, EvidenceRef, OrganizationalMemoryProvenanceRef


def build_company_brain_provenance_refs(
    *,
    company_id: UUID,
    cited_company_basis_refs: list[str],
    reasoning_reference_catalog: dict[str, Any],
) -> list[CompanyBrainProvenanceRef]:
    """Resolve every cited CB# label into a durable, self-contained
    CompanyBrainProvenanceRef.

    ``cited_company_basis_refs`` must be exactly the FINAL accepted
    reasoning_assessment.recommendation_basis.company_basis list for this
    turn - order and duplicates are preserved exactly as given, since a
    genuinely repeated citation in the real reasoning result is real data,
    not an error.

    Each ref is resolved ONLY through
    reasoning_reference_catalog["company_brain"][ref]["internal_source_item"]
    - the exact item snapshot captured at the moment this turn's CB# was
    assigned (see decision_context._build_reasoning_reference_catalog) -
    never by rereading a knowledge file, never by parsing the numeric
    suffix out of the ref string and indexing into a separately-supplied
    list. A cited ref that cannot be resolved this way fails closed: a
    receipt must never silently claim to represent fewer citations than
    the reasoning result actually made.
    """
    if not isinstance(reasoning_reference_catalog, dict):
        raise InvalidMemoryInput("reasoning_reference_catalog must be an object")

    company_brain_catalog = reasoning_reference_catalog.get("company_brain")
    if not isinstance(company_brain_catalog, dict):
        raise InvalidMemoryInput("reasoning_reference_catalog.company_brain must be an object")

    refs: list[CompanyBrainProvenanceRef] = []
    for cb_label in cited_company_basis_refs:
        if not isinstance(cb_label, str):
            raise InvalidMemoryInput(
                f"cited company_basis reference must be a string, got {type(cb_label).__name__}"
            )

        catalog_entry = company_brain_catalog.get(cb_label)
        if not isinstance(catalog_entry, dict):
            raise InvalidMemoryInput(
                f"cited company_basis reference {cb_label!r} was not supplied in this turn's "
                "Company Brain Context"
            )

        internal_source_item = catalog_entry.get("internal_source_item")
        if not isinstance(internal_source_item, dict):
            raise InvalidMemoryInput(
                f"cited company_basis reference {cb_label!r} has no resolvable source item"
            )

        refs.append(
            CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=company_id,
                internal_source_item=internal_source_item,
                display_label=cb_label,
            )
        )

    return refs


def build_truth_evidence_refs(
    *,
    cited_evidence_basis_refs: list[str],
    reasoning_reference_catalog: dict[str, Any],
) -> list[EvidenceRef]:
    """Resolve every cited T# label into a durable EvidenceRef(type="file").

    ``cited_evidence_basis_refs`` must be exactly the FINAL accepted
    reasoning_assessment.recommendation_basis.evidence_basis list for this
    turn - order and duplicates are preserved exactly as given, since a
    genuinely repeated citation in the real reasoning result is real data,
    not an error.

    FAIL CLOSED (Founder Correction 1, M8 Slice 3A): EvidenceRef currently
    supports only file-backed Truth provenance (type="file" - see
    app/ome/types.py's EVIDENCE_REF_TYPES). A cited T# that cannot be
    represented this way - missing from the catalog, no
    internal_source_item, no source_file_id, or a malformed
    source_file_id - is NEVER silently skipped. A persisted receipt whose
    response_snapshot.reasoning_assessment.recommendation_basis.
    evidence_basis claims a citation that durable evidence_refs cannot
    prove is silent provenance loss, which OME must never produce -
    receipt creation for that turn fails entirely rather than persisting
    a partial, misleading proof. A future, currently-unsupported Truth
    source type (e.g. an operational-event-derived claim) is explicitly
    deferred, not solved by skipping here.

    If the final reasoning cites no Truth refs at all, an empty
    cited_evidence_basis_refs list returns an empty result - that is
    valid, not an error.
    """
    if not isinstance(reasoning_reference_catalog, dict):
        raise InvalidMemoryInput("reasoning_reference_catalog must be an object")

    truth_catalog = reasoning_reference_catalog.get("truth")
    if not isinstance(truth_catalog, dict):
        raise InvalidMemoryInput("reasoning_reference_catalog.truth must be an object")

    refs: list[EvidenceRef] = []
    for t_label in cited_evidence_basis_refs:
        if not isinstance(t_label, str):
            raise InvalidMemoryInput(
                f"cited evidence_basis reference must be a string, got {type(t_label).__name__}"
            )

        catalog_entry = truth_catalog.get(t_label)
        if not isinstance(catalog_entry, dict):
            raise InvalidMemoryInput(
                f"cited evidence_basis reference {t_label!r} was not supplied in this turn's "
                "Operational Truth Context"
            )

        internal_source_item = catalog_entry.get("internal_source_item")
        if not isinstance(internal_source_item, dict):
            raise InvalidMemoryInput(
                f"cited evidence_basis reference {t_label!r} has no resolvable source item"
            )

        source_file_id = internal_source_item.get("source_file_id")
        if not source_file_id:
            raise InvalidMemoryInput(
                f"cited evidence_basis reference {t_label!r} has no source_file_id - it cannot be "
                "represented by the currently-supported file EvidenceRef, and a receipt must never "
                "silently persist a partial Truth provenance set"
            )
        try:
            file_id = source_file_id if isinstance(source_file_id, UUID) else UUID(str(source_file_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise InvalidMemoryInput(
                f"cited evidence_basis reference {t_label!r} has a malformed source_file_id: "
                f"{source_file_id!r}"
            ) from exc

        refs.append(EvidenceRef(type="file", id=file_id))

    return refs


def build_organizational_memory_provenance_refs(
    *,
    cited_om_refs: list[str],
    organizational_memory_reference_catalog: dict[str, Any],
) -> list[OrganizationalMemoryProvenanceRef]:
    """Resolve every cited OM# label into a durable
    OrganizationalMemoryProvenanceRef (M8 Slice 4B).

    Founder Correction 1: this represents explicit CITED basis only -
    ``cited_om_refs`` must be exactly the FINAL accepted
    reasoning_assessment.recommendation_basis.organizational_memory_basis
    list for this turn. Organizational Memory may be present in the
    prompt without being cited; only cited OM# labels ever become receipt
    provenance. Order and duplicates are preserved exactly as given,
    matching build_truth_evidence_refs/build_company_brain_provenance_refs'
    existing convention (a genuinely repeated citation is real data, not
    an error).

    Each ref is resolved ONLY through
    organizational_memory_reference_catalog[ref] - the exact
    (decision_memory_id, rendered_outcome_memory_ids) pair captured when
    this turn's OM# was assigned (see
    app/services/decision_context.py's
    _build_organizational_memory_reference_catalog) - never by rereading
    the database, never by parsing the numeric suffix out of the ref
    string. A cited ref that cannot be resolved this way fails closed: a
    receipt must never silently claim to represent fewer citations than
    the reasoning result actually made.

    outcome_memory_ids on the returned ref is EXACTLY the outcome id
    subset actually rendered to the model for that OM# (Founder
    Correction 2) - never the full source aggregate if it was larger than
    the prompt-rendering budget allowed.

    If the final reasoning cites no Organizational Memory at all, an
    empty cited_om_refs list returns an empty result - that is valid, not
    an error.
    """
    if not isinstance(organizational_memory_reference_catalog, dict):
        raise InvalidMemoryInput("organizational_memory_reference_catalog must be an object")

    refs: list[OrganizationalMemoryProvenanceRef] = []
    for om_label in cited_om_refs:
        if not isinstance(om_label, str):
            raise InvalidMemoryInput(
                f"cited organizational_memory_basis reference must be a string, got {type(om_label).__name__}"
            )

        catalog_entry = organizational_memory_reference_catalog.get(om_label)
        if not isinstance(catalog_entry, dict):
            raise InvalidMemoryInput(
                f"cited organizational_memory_basis reference {om_label!r} was not supplied in this "
                "turn's Historical Organizational Memory context"
            )

        raw_decision_id = catalog_entry.get("decision_memory_id")
        raw_outcome_ids = catalog_entry.get("rendered_outcome_memory_ids")
        if not raw_decision_id or not raw_outcome_ids:
            raise InvalidMemoryInput(
                f"cited organizational_memory_basis reference {om_label!r} has no resolvable source item"
            )

        try:
            decision_memory_id = raw_decision_id if isinstance(raw_decision_id, UUID) else UUID(str(raw_decision_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise InvalidMemoryInput(
                f"cited organizational_memory_basis reference {om_label!r} has a malformed "
                f"decision_memory_id: {raw_decision_id!r}"
            ) from exc

        outcome_ids: list[UUID] = []
        for raw_outcome_id in raw_outcome_ids:
            try:
                outcome_ids.append(
                    raw_outcome_id if isinstance(raw_outcome_id, UUID) else UUID(str(raw_outcome_id))
                )
            except (ValueError, AttributeError, TypeError) as exc:
                raise InvalidMemoryInput(
                    f"cited organizational_memory_basis reference {om_label!r} has a malformed "
                    f"rendered outcome id: {raw_outcome_id!r}"
                ) from exc

        refs.append(
            OrganizationalMemoryProvenanceRef(
                decision_memory_id=decision_memory_id,
                outcome_memory_ids=tuple(outcome_ids),
            )
        )

    return refs
