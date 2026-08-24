"""Server-internal Company Brain provenance extraction (pre-Slice-3
Company Brain provenance foundation).

Pure, server-only helper: resolves the CB# labels a reasoning turn's FINAL
accepted assessment actually cited
(reasoning_assessment.recommendation_basis.company_basis) against that SAME
turn's already-built, server-owned reasoning_reference_catalog
(app/services/decision_context.py) - never rereads a knowledge file, never
queries current Company Brain source state, never trusts any client-supplied
field.

Dormant by design: nothing in app/api or app/services/openai_client.py calls
this yet - wiring a live caller is separate, later Slice 3 work, gated
independently by the Founder.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.ome.errors import InvalidMemoryInput
from app.ome.types import CompanyBrainProvenanceRef


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
