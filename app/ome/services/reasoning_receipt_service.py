"""Service for creating immutable reasoning receipts (M8 Slice 2).

All inputs here are TRUSTED INTERNAL inputs, intended for a future Slice 3
/ai/chat integration to call server-side, immediately after a response is
finalized - never a client-facing endpoint, and not called from anywhere
yet in this slice. company_id/created_by_user_id must come from
AuthContext at that future call site, never a request body.

Slice 3 gate (Company Brain provenance): real NAWA responses can cite
Company Brain references (CB#), and those currently resolve only to
request-local Company Brain items with no durable, server-verifiable
mapping - unlike file evidence, which this service already verifies
against a real company-scoped row. LIVE reasoning-receipt integration
(actually calling create_receipt from /ai/chat) MUST NOT be enabled until
CB# provenance has that same durable mapping. This module does not
attempt to solve that here - EvidenceRef stays file-only (see
app/ome/types.py) until it does.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.ome.errors import InvalidMemoryInput
from app.ome.models import ReasoningReceipt
from app.ome.repositories.reasoning_receipt_repository import ReasoningReceiptRepository
from app.ome.types import EvidenceRef
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
        represented separately, through evidence_refs, never embedded
        inside response_snapshot.

        evidence_refs may be empty (a purely conversational response cites
        nothing). Every non-empty ref is verified here to actually belong
        to company_id before persistence - the client is never trusted to
        declare provenance (see EvidenceRef's own docstring). Order is
        preserved exactly as given; duplicates are preserved, never
        deduplicated or reordered, since a genuinely repeated citation in
        the real reasoning result is real data, not an error.
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

        verified_refs: list[dict[str, str]] = []
        for ref in evidence_refs:
            if not isinstance(ref, EvidenceRef):
                raise InvalidMemoryInput(f"evidence_refs entries must be EvidenceRef, got {type(ref).__name__}")
            await self._verify_evidence_ref(company_id=company_id, ref=ref)
            verified_refs.append(ref.to_dict())

        return await self.receipt_repo.create(
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            session_id=session_id,
            response_snapshot=canonical_snapshot,
            evidence_refs=verified_refs,
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
