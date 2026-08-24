"""Service for creating immutable reasoning receipts (M8 Slice 2, extended
by the pre-Slice-3 Company Brain provenance foundation).

All inputs here are TRUSTED INTERNAL inputs, intended for a future Slice 3
/ai/chat integration to call server-side, immediately after a response is
finalized - never a client-facing endpoint, and not called from anywhere
yet. company_id/created_by_user_id must come from AuthContext at that
future call site, never a request body.

Company Brain provenance (CB#) is no longer unsolved: company_brain_refs
now carries a durable, server-derived CompanyBrainProvenanceRef per cited
CB# (see app/ome/types.py and app/ome/provenance.py's
build_company_brain_provenance_refs, the only intended way to construct
them - never a client declaration, and never a stable identity built from
the ephemeral CB# label itself). This module still does not call itself:
nothing in app/api or app/services/openai_client.py invokes create_receipt
yet. LIVE reasoning-receipt integration remains a separate, later-gated
Slice 3 decision, not something this foundation round authorizes.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.ome.errors import InvalidMemoryInput
from app.ome.models import ReasoningReceipt
from app.ome.repositories.reasoning_receipt_repository import ReasoningReceiptRepository
from app.ome.types import CompanyBrainProvenanceRef, EvidenceRef
from app.repositories.file_repository import FileRepository


class ReasoningReceiptService:
    """Business logic for creating immutable reasoning receipts."""

    def __init__(self, db: Any) -> None:
        """Initialize the service with its repositories."""
        self.receipt_repo = ReasoningReceiptRepository(db)
        self.file_repo = FileRepository(db)

    async def create_receipt(
        self,
        *,
        company_id: UUID,
        created_by_user_id: UUID,
        session_id: str | None,
        response_snapshot: dict[str, Any],
        evidence_refs: list[EvidenceRef],
        company_brain_refs: list[CompanyBrainProvenanceRef] | None = None,
    ) -> ReasoningReceipt:
        """Validate and create one immutable reasoning receipt.

        response_snapshot minimum contract: {"ceo_text": str,
        "reasoning_assessment": dict}. The persisted snapshot is a
        CANONICAL dict this service constructs itself from exactly those
        two validated values - the caller's input object is never
        persisted verbatim and is never mutated. Any other key the caller
        happens to include (prompts, Decision Context, the reasoning
        reference catalog, or any other internal/sensitive field) is
        silently dropped, never persisted - a narrow, fixed audit-receipt
        contract, not an arbitrary passthrough. Evidence provenance is
        represented separately, through evidence_refs/company_brain_refs,
        never embedded inside response_snapshot.

        evidence_refs (Truth) may be empty (a purely conversational
        response cites nothing). Every non-empty ref is verified here to
        actually belong to company_id before persistence - the client is
        never trusted to declare provenance (see EvidenceRef's own
        docstring). Order is preserved exactly as given; duplicates are
        preserved, never deduplicated or reordered, since a genuinely
        repeated citation in the real reasoning result is real data, not
        an error.

        company_brain_refs (Company Brain, pre-Slice-3 foundation) are
        server-derived CompanyBrainProvenanceRef values - see
        app/ome/provenance.py's build_company_brain_provenance_refs, the
        only intended way to construct them. Every entry's company_id must
        match this receipt's company_id (tenant safety - never trusted
        blindly from caller input). If response_snapshot's
        reasoning_assessment cites any company_basis CB# labels, this
        service fails closed unless company_brain_refs represents EXACTLY
        that same ordered list of labels: a receipt must never silently
        persist with missing or extra Company Brain provenance relative to
        what the reasoning result actually cited. Both categories are
        persisted into the SAME evidence_refs JSONB array, each entry
        explicitly tagged with "category" ("truth" / "company_brain") so
        the union stays unambiguous - see each type's own to_dict().
        """
        if not isinstance(response_snapshot, dict):
            raise InvalidMemoryInput("response_snapshot must be an object")

        ceo_text = response_snapshot.get("ceo_text")
        if not isinstance(ceo_text, str):
            raise InvalidMemoryInput("response_snapshot.ceo_text must be a string")

        reasoning_assessment = response_snapshot.get("reasoning_assessment")
        if not isinstance(reasoning_assessment, dict):
            raise InvalidMemoryInput("response_snapshot.reasoning_assessment must be an object")

        canonical_snapshot: dict[str, Any] = {
            "ceo_text": ceo_text,
            "reasoning_assessment": reasoning_assessment,
        }

        persisted_refs: list[dict[str, Any]] = []
        for ref in evidence_refs:
            if not isinstance(ref, EvidenceRef):
                raise InvalidMemoryInput(f"evidence_refs entries must be EvidenceRef, got {type(ref).__name__}")
            await self._verify_evidence_ref(company_id=company_id, ref=ref)
            persisted_refs.append(ref.to_dict())

        cb_refs = list(company_brain_refs) if company_brain_refs is not None else []
        self._verify_company_brain_refs(
            company_id=company_id,
            company_brain_refs=cb_refs,
            reasoning_assessment=reasoning_assessment,
        )
        persisted_refs.extend(ref.to_dict() for ref in cb_refs)

        return await self.receipt_repo.create(
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            session_id=session_id,
            response_snapshot=canonical_snapshot,
            evidence_refs=persisted_refs,
        )

    async def _verify_evidence_ref(self, *, company_id: UUID, ref: EvidenceRef) -> None:
        """Fail closed unless `ref` resolves inside company_id. Uses the
        existing, already company-scoped FileRepository.get_file_by_id -
        never an unscoped lookup, and never reveals whether the id exists
        in a different company (it simply resolves to "not found")."""
        if ref.type == "file":
            file_row = await self.file_repo.get_file_by_id(company_id, ref.id)
            if file_row is None:
                raise InvalidMemoryInput(f"evidence ref file {ref.id} does not resolve inside this company")
            return
        # EvidenceRef.__post_init__ already rejects any type outside
        # EVIDENCE_REF_TYPES, so this branch is unreachable in practice -
        # kept only as an explicit fail-closed guard, never silently passed.
        raise InvalidMemoryInput(f"Unsupported EvidenceRef type: {ref.type!r}")

    def _verify_company_brain_refs(
        self,
        *,
        company_id: UUID,
        company_brain_refs: list[CompanyBrainProvenanceRef],
        reasoning_assessment: dict[str, Any],
    ) -> None:
        """Tenant safety + citation-completeness fail-closed checks.

        Tenant safety: every ref's own company_id must match this receipt's
        company_id - never trusted blindly, and never repaired/overwritten
        here (a mismatch is a caller bug, not something to silently fix).

        Citation completeness: reads
        reasoning_assessment.recommendation_basis.company_basis (the FINAL
        accepted CB# citations for this turn - see
        app/services/reasoning_validation.py's RecommendationBasis) and
        requires it to equal, in order, [ref.display_label for ref in
        company_brain_refs] EXACTLY. This is what prevents a receipt from
        ever silently persisting with fewer (or extra, uncited) Company
        Brain provenance entries than the reasoning result actually cited.
        If company_basis is absent/empty, an empty company_brain_refs is
        valid - most turns cite no company policy at all.
        """
        for ref in company_brain_refs:
            if not isinstance(ref, CompanyBrainProvenanceRef):
                raise InvalidMemoryInput(
                    f"company_brain_refs entries must be CompanyBrainProvenanceRef, got {type(ref).__name__}"
                )
            if ref.company_id != company_id:
                raise InvalidMemoryInput(
                    f"company_brain_refs entry company_id {ref.company_id} does not match "
                    f"receipt company_id {company_id}"
                )

        cited_company_basis: list[str] = []
        recommendation_basis = reasoning_assessment.get("recommendation_basis")
        if isinstance(recommendation_basis, dict):
            raw_company_basis = recommendation_basis.get("company_basis")
            if isinstance(raw_company_basis, list):
                cited_company_basis = [ref for ref in raw_company_basis if isinstance(ref, str)]

        represented_labels = [ref.display_label for ref in company_brain_refs]
        if cited_company_basis != represented_labels:
            raise InvalidMemoryInput(
                "response_snapshot.reasoning_assessment.recommendation_basis.company_basis cites "
                f"{cited_company_basis!r} but company_brain_refs represents {represented_labels!r} - "
                "every cited CB# must be represented by exactly one company_brain_refs entry, in "
                "the same order, with no extras"
            )
