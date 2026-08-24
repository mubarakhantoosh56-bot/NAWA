"""Service for recording and correcting human decision memories (M8 Slice 2).

company_id/acting_user_id are trusted caller context, intended to come
from AuthContext at a future API boundary - this service never re-validates
company membership itself (Founder Correction / existing project
convention: membership is an API-boundary concern, not a service concern).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.ome.errors import DecisionNotFound, InvalidMemoryInput, ReceiptNotFound
from app.ome.models import DecisionMemory
from app.ome.repositories.decision_memory_repository import DecisionMemoryRepository
from app.ome.repositories.reasoning_receipt_repository import ReasoningReceiptRepository
from app.repositories.operational_situation_repository import OperationalSituationRepository


class DecisionMemoryService:
    """Business logic for creating and correcting human decisions.

    An AI recommendation can never automatically become a DecisionMemory:
    there is no code path here that reads a reasoning response and writes
    a decision on its own - decision_text/decided_by_user_id only ever
    come from an explicit caller-supplied human action.
    """

    def __init__(self, db) -> None:
        """Initialize the service with its repositories."""
        self.decision_repo = DecisionMemoryRepository(db)
        self.receipt_repo = ReasoningReceiptRepository(db)
        self.situation_repo = OperationalSituationRepository(db)

    async def record_decision(
        self,
        *,
        company_id: UUID,
        acting_user_id: UUID,
        reasoning_receipt_id: UUID,
        decision_text: str,
        rationale: str | None = None,
        situation_id: UUID | None = None,
    ) -> DecisionMemory:
        """Record one explicit human decision bound to a reasoning receipt.

        No evidence_refs parameter exists here by design: a decision's
        authoritative evidence provenance is always
        decision -> reasoning_receipt -> evidence_refs, never a
        client-supplied value on the decision itself.
        """
        receipt = await self.receipt_repo.get_by_id(company_id=company_id, receipt_id=reasoning_receipt_id)
        if receipt is None:
            raise ReceiptNotFound(f"reasoning receipt {reasoning_receipt_id} not found inside this company")

        if situation_id is not None:
            situation = await self.situation_repo.get_situation(company_id=company_id, situation_id=situation_id)
            if situation is None:
                raise InvalidMemoryInput(f"situation {situation_id} not found inside this company")

        cleaned_text = _require_text(decision_text, field_name="decision_text")
        cleaned_rationale = _clean_optional_text(rationale)

        return await self.decision_repo.create(
            company_id=company_id,
            reasoning_receipt_id=reasoning_receipt_id,
            situation_id=situation_id,
            decision_text=cleaned_text,
            rationale=cleaned_rationale,
            decided_by_user_id=acting_user_id,
            decided_at=datetime.now(timezone.utc),
        )

    async def supersede_decision(
        self,
        *,
        company_id: UUID,
        acting_user_id: UUID,
        old_decision_id: UUID,
        reasoning_receipt_id: UUID,
        decision_text: str,
        rationale: str | None = None,
        situation_id: UUID | None = None,
    ) -> tuple[DecisionMemory, DecisionMemory]:
        """Correct a prior decision by creating a new one and marking the
        old one superseded, atomically. The replacement may reference a
        different valid reasoning receipt and/or situation than the
        original - it is a new, independently-valid decision, not a
        patched copy. Returns (new_decision, old_decision_after_update).

        Raises DecisionNotFound if old_decision_id does not resolve inside
        this company at all (a cheap pre-check before the atomic
        operation); the atomic operation itself raises InvalidSupersession
        if the row is not active by the time it acquires the lock (a
        concurrent supersession may have already won).
        """
        existing = await self.decision_repo.get_by_id(company_id=company_id, decision_id=old_decision_id)
        if existing is None:
            raise DecisionNotFound(f"decision {old_decision_id} not found inside this company")

        receipt = await self.receipt_repo.get_by_id(company_id=company_id, receipt_id=reasoning_receipt_id)
        if receipt is None:
            raise ReceiptNotFound(f"reasoning receipt {reasoning_receipt_id} not found inside this company")

        if situation_id is not None:
            situation = await self.situation_repo.get_situation(company_id=company_id, situation_id=situation_id)
            if situation is None:
                raise InvalidMemoryInput(f"situation {situation_id} not found inside this company")

        cleaned_text = _require_text(decision_text, field_name="decision_text")
        cleaned_rationale = _clean_optional_text(rationale)

        return await self.decision_repo.supersede_with_new_decision(
            company_id=company_id,
            old_decision_id=old_decision_id,
            reasoning_receipt_id=reasoning_receipt_id,
            situation_id=situation_id,
            decision_text=cleaned_text,
            rationale=cleaned_rationale,
            decided_by_user_id=acting_user_id,
            decided_at=datetime.now(timezone.utc),
        )


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidMemoryInput(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise InvalidMemoryInput(f"{field_name} cannot be blank")
    return cleaned


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidMemoryInput("rationale must be a string")
    cleaned = value.strip()
    return cleaned or None
