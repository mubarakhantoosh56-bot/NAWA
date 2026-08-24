"""Service for recording and correcting human outcome memories (M8 Slice 2).

No outcome evidence_refs exist in Slice 2: outcome-level evidence
provenance beyond the human-attributed outcome itself is deferred until a
server-verifiable trust boundary is separately designed. The original
decision remains traceable to its evidence through
decision_memory_id -> reasoning_receipt -> evidence_refs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.ome.errors import DecisionNotFound, InvalidMemoryInput, OutcomeNotFound
from app.ome.models import OUTCOME_RESULT_STATES, OutcomeMemory
from app.ome.repositories.decision_memory_repository import DecisionMemoryRepository
from app.ome.repositories.outcome_memory_repository import OutcomeMemoryRepository


class OutcomeMemoryService:
    """Business logic for creating and correcting human-recorded outcomes.

    An outcome may be recorded for a superseded decision - that decision
    remains real history, and recording what actually happened after it
    (even if a later decision superseded it) is legitimate audit trail,
    never blocked.
    """

    def __init__(self, db) -> None:
        """Initialize the service with its repositories."""
        self.outcome_repo = OutcomeMemoryRepository(db)
        self.decision_repo = DecisionMemoryRepository(db)

    async def record_outcome(
        self,
        *,
        company_id: UUID,
        acting_user_id: UUID,
        decision_memory_id: UUID,
        outcome_summary: str,
        result_state: str,
        observed_at: datetime | None = None,
    ) -> OutcomeMemory:
        """Record one human-observed outcome of a prior decision."""
        decision = await self.decision_repo.get_by_id(company_id=company_id, decision_id=decision_memory_id)
        if decision is None:
            raise DecisionNotFound(f"decision {decision_memory_id} not found inside this company")

        cleaned_summary = _require_text(outcome_summary, field_name="outcome_summary")
        _require_valid_result_state(result_state)
        effective_observed_at = _resolve_observed_at(observed_at)

        return await self.outcome_repo.create(
            company_id=company_id,
            decision_memory_id=decision_memory_id,
            outcome_summary=cleaned_summary,
            result_state=result_state,
            recorded_by_user_id=acting_user_id,
            observed_at=effective_observed_at,
        )

    async def supersede_outcome(
        self,
        *,
        company_id: UUID,
        acting_user_id: UUID,
        old_outcome_id: UUID,
        outcome_summary: str,
        result_state: str,
        observed_at: datetime | None = None,
    ) -> tuple[OutcomeMemory, OutcomeMemory]:
        """Correct a prior outcome by creating a new one and marking the
        old one superseded, atomically. Returns
        (new_outcome, old_outcome_after_update).

        No decision_memory_id parameter (Codex-required fix): an outcome
        supersession always corrects the historical record for the SAME
        decision the old outcome already belongs to - that identity is
        derived from the old outcome itself (company-scoped lookup here,
        then re-derived authoritatively inside the repository's own
        transaction), never accepted from the caller. A correction that
        needs to attach to a genuinely different decision is not a
        supersession - call record_outcome() for that instead.
        """
        existing = await self.outcome_repo.get_by_id(company_id=company_id, outcome_id=old_outcome_id)
        if existing is None:
            raise OutcomeNotFound(f"outcome {old_outcome_id} not found inside this company")

        cleaned_summary = _require_text(outcome_summary, field_name="outcome_summary")
        _require_valid_result_state(result_state)
        effective_observed_at = _resolve_observed_at(observed_at)

        return await self.outcome_repo.supersede_with_new_outcome(
            company_id=company_id,
            old_outcome_id=old_outcome_id,
            outcome_summary=cleaned_summary,
            result_state=result_state,
            recorded_by_user_id=acting_user_id,
            observed_at=effective_observed_at,
        )


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidMemoryInput(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise InvalidMemoryInput(f"{field_name} cannot be blank")
    return cleaned


def _require_valid_result_state(result_state: str) -> None:
    if result_state not in OUTCOME_RESULT_STATES:
        raise InvalidMemoryInput(f"Invalid result_state: {result_state!r}")


def _resolve_observed_at(observed_at: datetime | None) -> datetime:
    """Default to server UTC now. A caller-supplied value must be
    timezone-aware (never naive - a naive datetime's real instant is
    ambiguous) and must not be in the future (a real-world outcome cannot
    be observed ahead of now)."""
    if observed_at is None:
        return datetime.now(timezone.utc)
    if observed_at.tzinfo is None or observed_at.tzinfo.utcoffset(observed_at) is None:
        raise InvalidMemoryInput("observed_at must be timezone-aware")
    if observed_at > datetime.now(timezone.utc):
        raise InvalidMemoryInput("observed_at cannot be in the future")
    return observed_at
