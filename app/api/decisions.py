"""M8 Slice 3B-1: Human Decision recording API.

Core law (unchanged from the M8 OME architecture): AI recommendation !=
human decision. A DecisionMemory row is created ONLY because an
authenticated human explicitly called this endpoint - nothing in
app/services/openai_client.py or app/api/chat.py ever calls
DecisionMemoryService, and this module never calls anything in those two
files either. The reasoning receipt a decision cites remains fully
immutable; recording a decision never mutates it.

MVP authorization limitation (Founder Decision 2, accepted for this slice):
ome_decision_memories has no department_id column, so decision authority
here is company-scoped only - any authenticated user holding the existing
"memory.write" permission may record a decision for the whole company, not
just their own department. This is a known, accepted MVP limitation, not an
oversight; department-scoped decision authority would require a schema
change out of scope for this slice.
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
from app.ome.errors import InvalidMemoryInput, ReceiptNotFound
from app.ome.services.decision_memory_service import DecisionMemoryService

router = APIRouter(prefix="/decisions", tags=["Human Decisions"])
logger = logging.getLogger(__name__)

# Existing, already-defined permission (app/core/role_permissions.py) - held
# by every role template except "employee". Not a new permission: reused
# exactly as-is per Founder Decision 2. ai.chat is deliberately NOT the
# gate here - using the AI chat feature is not the same authority as
# recording an organizational decision.
DECISION_WRITE_PERMISSION = "memory.write"


class DecisionCreateRequest(BaseModel):
    """Client-authorable fields only. extra="forbid" (Founder Correction 1):
    any undeclared field - company_id, created_by_user_id/decided_by_user_id,
    evidence_refs, company_brain_refs, response_snapshot, status,
    created_at, decided_at, supersedes_id/superseded_by, or anything else -
    fails request validation (422) before this handler ever runs. Nothing
    is silently ignored."""

    model_config = ConfigDict(extra="forbid")

    reasoning_receipt_id: UUID
    decision_text: str
    rationale: str | None = None
    situation_id: UUID | None = None


class DecisionMemoryResponse(BaseModel):
    """Minimum MVP response - never redundantly echoes receipt evidence_refs,
    Company Brain provenance, or response_snapshot (all remain reachable
    only through reasoning_receipt_id). company_id/decided_by_user_id are
    intentionally omitted here (the caller already knows both from their
    own auth context) - they are still persisted and tested, just not
    returned in this minimal response."""

    id: UUID
    reasoning_receipt_id: UUID
    situation_id: UUID | None
    decision_text: str
    rationale: str | None
    status: str
    decided_at: datetime
    created_at: datetime


async def get_decision_memory_service(request: Request) -> DecisionMemoryService:
    """Return a DecisionMemoryService backed by the app database pool -
    identical dependency pattern to app/api/situations.py's
    get_operational_situation_service."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Decision recording service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return DecisionMemoryService(pool)


@router.post("", response_model=DecisionMemoryResponse, status_code=status.HTTP_201_CREATED)
async def record_decision(
    request: DecisionCreateRequest,
    auth_context: AuthContext = Depends(require_permission(DECISION_WRITE_PERMISSION)),
    decision_service: DecisionMemoryService = Depends(get_decision_memory_service),
) -> DecisionMemoryResponse:
    """Record one explicit human decision bound to an immutable reasoning
    receipt. company_id and the acting human identity are ALWAYS the
    JWT-derived AuthContext - never client-supplied, never inferred from
    the receipt's own creator (the human recording the decision right now
    is authoritative, even if a different or the same user generated the
    original response)."""
    try:
        decision = await decision_service.record_decision(
            company_id=UUID(auth_context.company_id),
            acting_user_id=UUID(auth_context.user_id),
            reasoning_receipt_id=request.reasoning_receipt_id,
            decision_text=request.decision_text,
            rationale=request.rationale,
            situation_id=request.situation_id,
        )
        return DecisionMemoryResponse(
            id=decision.id,
            reasoning_receipt_id=decision.reasoning_receipt_id,
            situation_id=decision.situation_id,
            decision_text=decision.decision_text,
            rationale=decision.rationale,
            status=decision.status,
            decided_at=decision.decided_at,
            created_at=decision.created_at,
        )
    except ReceiptNotFound as exc:
        # Never distinguishes "does not exist" from "belongs to another
        # company" (Founder Correction 3, unchanged project-wide
        # convention) - both resolve identically to 404.
        logger.info("Record decision failed: receipt not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reasoning receipt not found") from exc
    except InvalidMemoryInput as exc:
        # Covers blank/non-string decision_text, invalid rationale, AND a
        # nonexistent/cross-company situation_id - the current service
        # raises the same InvalidMemoryInput for all of these (no distinct
        # SituationNotFound class exists). Accepted for this slice per
        # Founder Decision (Step 8): mapped uniformly to 422 rather than
        # splitting situation-not-found into its own 404, which would
        # require a service-layer change out of scope here.
        logger.info("Record decision failed with a safe domain validation error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Record decision endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Decision recording service unavailable",
        ) from exc
