"""M8 Slice 3C-1: Human Outcome recording API.

Core law (unchanged from the M8 OME architecture): human decision != human
outcome. An OutcomeMemory row is created ONLY because an authenticated
human explicitly called this endpoint - nothing in app/services/
openai_client.py, app/api/chat.py, or app/api/decisions.py ever calls
OutcomeMemoryService, and this module never calls anything in those files
either. Recording an outcome never mutates the DecisionMemory or
ReasoningReceipt it traces back to - both remain fully immutable.

Outcome recording is a HUMAN HISTORICAL OBSERVATION, never fresh
operational Truth: outcome_summary is never written into operational
events, memory facts, Truth ingestion, or Company Brain, and never fed
back into any reasoning path. Provenance for an outcome remains reachable
only through decision_memory_id -> DecisionMemory -> reasoning_receipt_id
-> ReasoningReceipt -> original Truth + Company Brain provenance - never a
client-supplied evidence_refs field on the outcome itself (none exists on
OutcomeMemory, by design).

MVP authorization limitation (same accepted limitation as Slice 3B-1's
Decision API): ome_outcome_memories has no department_id column, so
outcome-recording authority here is company-scoped only - any
authenticated user holding "memory.write" may record an outcome for any
decision in the company, not just their own department.

CREATE-only by design: outcome supersession already exists in the closed
OutcomeMemoryService/OutcomeMemoryRepository (record_outcome's sibling
supersede_outcome), but this route deliberately does not expose it - no
PUT/PATCH, no superseded_by/old_outcome_id request field. The existing
schema/service also intentionally allow multiple simultaneously-active
OutcomeMemory rows for the same decision (no uniqueness constraint) - this
route does not add one; recording a second, independent outcome for a
decision that already has one is a legitimate action, not an error.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.ome.errors import DecisionNotFound, InvalidMemoryInput
from app.ome.services.outcome_memory_service import OutcomeMemoryService

router = APIRouter(prefix="/outcomes", tags=["Human Outcomes"])
logger = logging.getLogger(__name__)

# Existing, already-defined permission (app/core/role_permissions.py) -
# the same one Slice 3B-1's Decision API reuses. Not a new permission.
OUTCOME_WRITE_PERMISSION = "memory.write"


class OutcomeCreateRequest(BaseModel):
    """Client-authorable fields only. extra="forbid": any undeclared field
    - company_id, recorded_by_user_id/created_by_user_id/decided_by_user_id/
    user_id, evidence_refs, company_brain_refs, response_snapshot, status,
    created_at, superseded_by/supersedes_id/old_outcome_id, or anything
    else - fails request validation (422) before this handler ever runs.

    observed_at is the ONE deliberate exception to "no client-authored
    timestamps": it represents when the real-world outcome actually
    occurred, which a human may legitimately know only after the fact -
    the service validates it (timezone-aware, not in the future) rather
    than rejecting it outright. created_at remains DB/server-only and has
    no field here at all."""

    model_config = ConfigDict(extra="forbid")

    decision_memory_id: UUID
    outcome_summary: str
    result_state: str
    observed_at: datetime | None = None


class OutcomeMemoryResponse(BaseModel):
    """Minimum MVP response - never redundantly echoes receipt evidence_refs,
    Company Brain provenance, or response_snapshot (all remain reachable
    only through decision_memory_id -> reasoning_receipt_id). company_id/
    recorded_by_user_id are intentionally omitted here (the caller already
    knows both from their own auth context) - they are still persisted and
    tested, just not returned in this minimal response."""

    id: UUID
    decision_memory_id: UUID
    outcome_summary: str
    result_state: str
    status: str
    observed_at: datetime
    created_at: datetime


async def get_outcome_memory_service(request: Request) -> OutcomeMemoryService:
    """Return an OutcomeMemoryService backed by the app database pool -
    identical dependency pattern to app/api/decisions.py's
    get_decision_memory_service."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Outcome recording service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return OutcomeMemoryService(pool)


@router.post("", response_model=OutcomeMemoryResponse, status_code=status.HTTP_201_CREATED)
async def record_outcome(
    request: OutcomeCreateRequest,
    auth_context: AuthContext = Depends(require_permission(OUTCOME_WRITE_PERMISSION)),
    outcome_service: OutcomeMemoryService = Depends(get_outcome_memory_service),
) -> OutcomeMemoryResponse:
    """Record one explicit human-observed outcome of a prior decision.
    company_id and the acting human identity are ALWAYS the JWT-derived
    AuthContext - never client-supplied, never inferred from the
    decision's own recorder or the original receipt's creator (the human
    recording the outcome right now is authoritative)."""
    try:
        outcome = await outcome_service.record_outcome(
            company_id=UUID(auth_context.company_id),
            acting_user_id=UUID(auth_context.user_id),
            decision_memory_id=request.decision_memory_id,
            outcome_summary=request.outcome_summary,
            result_state=request.result_state,
            observed_at=request.observed_at,
        )
        return OutcomeMemoryResponse(
            id=outcome.id,
            decision_memory_id=outcome.decision_memory_id,
            outcome_summary=outcome.outcome_summary,
            result_state=outcome.result_state,
            status=outcome.status,
            observed_at=outcome.observed_at,
            created_at=outcome.created_at,
        )
    except DecisionNotFound as exc:
        # Never distinguishes "does not exist" from "belongs to another
        # company" (Founder Correction 3, unchanged project-wide
        # convention) - both resolve identically to 404.
        logger.info("Record outcome failed: decision not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found") from exc
    except InvalidMemoryInput as exc:
        # Covers blank/non-string outcome_summary, invalid result_state,
        # naive observed_at, and future observed_at - the service raises
        # the same InvalidMemoryInput for all of these (no distinct error
        # subclasses exist). Mapped uniformly to 422, matching the
        # accepted precedent from Slice 3B-1's Decision API.
        logger.info("Record outcome failed with a safe domain validation error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Record outcome endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Outcome recording service unavailable",
        ) from exc
