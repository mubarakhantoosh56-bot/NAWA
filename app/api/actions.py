"""M9 Slice 2: Action Persistence Foundation -- Backend Service/API.

Core law (Architecture Contract Sec 5): AI recommendation != human
Action. An Action row is created ONLY because an authenticated human
explicitly called this endpoint - nothing in app/services/openai_client.py
or app/api/chat.py ever calls ActionService, and this module never calls
anything in those two files either.

Two narrow PATCH endpoints, not one generic PATCH /actions/{id} (Sec 22):
title, instructions, decision_memory_id, and created_by_user_id are
immutable after creation. The only mutable surface is status and
assigned_user_id, each behind its own purpose-named endpoint.

MVP authorization limitation (same accepted limitation as the Decision
and Outcome APIs): ome_actions has no department_id column, so Action
write authority here is company-scoped only - any authenticated user
holding "memory.write" may create/mutate Actions for the whole company,
not just their own department (Architecture Contract Sec 10).
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.ome.errors import (
    ActionNotFound,
    DecisionNotFound,
    InvalidActionTransition,
    InvalidAssignee,
    InvalidMemoryInput,
)
from app.ome.models.action import Action
from app.ome.models.action_change_event import ActionChangeEvent
from app.ome.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["Actions"])
logger = logging.getLogger(__name__)

# Existing, already-defined permission (app/core/role_permissions.py) -
# the same one the Decision and Outcome APIs reuse. Not a new permission.
ACTION_WRITE_PERMISSION = "memory.write"


class ActionCreateRequest(BaseModel):
    """Client-authorable fields only. extra="forbid": any undeclared field
    - company_id, created_by_user_id, status, created_at, updated_at,
    completed_at, cancelled_at, or anything else - fails request
    validation (422) before this handler ever runs."""

    model_config = ConfigDict(extra="forbid")

    decision_memory_id: UUID
    title: str
    instructions: str | None = None
    assigned_user_id: UUID | None = None


class ActionStatusUpdateRequest(BaseModel):
    """The only client-supplied value is the target status."""

    model_config = ConfigDict(extra="forbid")

    status: str


class ActionAssigneeUpdateRequest(BaseModel):
    """The only client-supplied value is the target assignee - explicit
    `null` clears it (Sec 22). assigned_user_id is REQUIRED (no default):
    an omitted field is a malformed request (422), never silently treated
    as "unassign" - the caller must say `{"assigned_user_id": null}` to
    mean that, distinguishing "I want to clear the assignee" from "I
    forgot to include this field"."""

    model_config = ConfigDict(extra="forbid")

    assigned_user_id: UUID | None


class ActionResponse(BaseModel):
    """Minimum MVP response. company_id is intentionally omitted (the
    caller already knows it from their own auth context) - it is still
    persisted and tested, just not returned here."""

    id: UUID
    decision_memory_id: UUID
    title: str
    instructions: str | None
    status: str
    assigned_user_id: UUID | None
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None


class ActionChangeEventResponse(BaseModel):
    """One row of the append-only change ledger."""

    id: UUID
    change_type: str
    from_status: str | None
    to_status: str | None
    from_assigned_user_id: UUID | None
    to_assigned_user_id: UUID | None
    changed_by_user_id: UUID
    changed_at: datetime


class ActionDetailResponse(ActionResponse):
    """GET /actions/{id}: one Action with its full change-event history
    (Sec 22: "optionally with its status history")."""

    events: list[ActionChangeEventResponse]


def _to_action_response(action: Action) -> ActionResponse:
    return ActionResponse(
        id=action.id,
        decision_memory_id=action.decision_memory_id,
        title=action.title,
        instructions=action.instructions,
        status=action.status,
        assigned_user_id=action.assigned_user_id,
        created_by_user_id=action.created_by_user_id,
        created_at=action.created_at,
        updated_at=action.updated_at,
        completed_at=action.completed_at,
        cancelled_at=action.cancelled_at,
    )


def _to_event_response(event: ActionChangeEvent) -> ActionChangeEventResponse:
    return ActionChangeEventResponse(
        id=event.id,
        change_type=event.change_type,
        from_status=event.from_status,
        to_status=event.to_status,
        from_assigned_user_id=event.from_assigned_user_id,
        to_assigned_user_id=event.to_assigned_user_id,
        changed_by_user_id=event.changed_by_user_id,
        changed_at=event.changed_at,
    )


async def get_action_service(request: Request) -> ActionService:
    """Return an ActionService backed by the app database pool - identical
    dependency pattern to app/api/decisions.py's get_decision_memory_service."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Action service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return ActionService(pool)


@router.post("", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    request: ActionCreateRequest,
    auth_context: AuthContext = Depends(require_permission(ACTION_WRITE_PERMISSION)),
    action_service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Record one human-authorized Action against a decision. company_id
    and the acting human identity are ALWAYS the JWT-derived AuthContext -
    never client-supplied."""
    try:
        action = await action_service.create_action(
            company_id=UUID(auth_context.company_id),
            acting_user_id=UUID(auth_context.user_id),
            decision_memory_id=request.decision_memory_id,
            title=request.title,
            instructions=request.instructions,
            assigned_user_id=request.assigned_user_id,
        )
        return _to_action_response(action)
    except DecisionNotFound as exc:
        logger.info("Create action failed: decision not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found") from exc
    except InvalidAssignee as exc:
        # Never distinguishes "does not exist" from "belongs to another
        # company" from "no active membership" (Sec 11.3) - all resolve
        # identically to 404.
        logger.info("Create action failed: assignee not valid")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found") from exc
    except InvalidMemoryInput as exc:
        logger.info("Create action failed with a safe domain validation error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Create action endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Action service unavailable",
        ) from exc


@router.get("", response_model=list[ActionResponse])
async def list_actions(
    decision_memory_id: UUID = Query(..., description="Required (Sec 22): list is anchored to one decision"),
    status_filter: str | None = Query(default=None, alias="status", description="Optional status filter"),
    assigned_user_id: UUID | None = Query(default=None, description="Optional assignee filter"),
    auth_context: AuthContext = Depends(require_permission(ACTION_WRITE_PERMISSION)),
    action_service: ActionService = Depends(get_action_service),
) -> list[ActionResponse]:
    """List Actions for one decision. decision_memory_id is required - an
    unfiltered company-wide action list is out of MVP scope (Sec 22)."""
    try:
        actions = await action_service.list_actions(
            company_id=UUID(auth_context.company_id),
            decision_memory_id=decision_memory_id,
            status=status_filter,
            assigned_user_id=assigned_user_id,
        )
        return [_to_action_response(action) for action in actions]
    except InvalidMemoryInput as exc:
        logger.info("List actions failed with a safe domain validation error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("List actions endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Action service unavailable",
        ) from exc


@router.get("/{action_id}", response_model=ActionDetailResponse)
async def get_action(
    action_id: UUID,
    auth_context: AuthContext = Depends(require_permission(ACTION_WRITE_PERMISSION)),
    action_service: ActionService = Depends(get_action_service),
) -> ActionDetailResponse:
    """Return one Action together with its full chronological change
    history."""
    try:
        action, events = await action_service.get_action(
            company_id=UUID(auth_context.company_id),
            action_id=action_id,
        )
        base = _to_action_response(action)
        return ActionDetailResponse(
            **base.model_dump(),
            events=[_to_event_response(event) for event in events],
        )
    except ActionNotFound as exc:
        logger.info("Get action failed: action not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Get action endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Action service unavailable",
        ) from exc


@router.patch("/{action_id}/status", response_model=ActionResponse)
async def update_action_status(
    action_id: UUID,
    request: ActionStatusUpdateRequest,
    auth_context: AuthContext = Depends(require_permission(ACTION_WRITE_PERMISSION)),
    action_service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Transition an Action's execution state. Rejected transitions
    (invalid move, self-transition, or a mutation attempted on a
    terminal Action) return 409 and write no change event."""
    try:
        action = await action_service.change_status(
            company_id=UUID(auth_context.company_id),
            action_id=action_id,
            to_status=request.status,
            acting_user_id=UUID(auth_context.user_id),
        )
        return _to_action_response(action)
    except ActionNotFound as exc:
        logger.info("Update action status failed: action not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found") from exc
    except InvalidActionTransition as exc:
        logger.info("Update action status failed: invalid transition")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidMemoryInput as exc:
        logger.info("Update action status failed with a safe domain validation error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Update action status endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Action service unavailable",
        ) from exc


@router.patch("/{action_id}/assignee", response_model=ActionResponse)
async def update_action_assignee(
    action_id: UUID,
    request: ActionAssigneeUpdateRequest,
    auth_context: AuthContext = Depends(require_permission(ACTION_WRITE_PERMISSION)),
    action_service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Set, change, or clear the human responsible for an Action. Rejected
    reassignments (no-op target, terminal Action, or invalid assignee)
    return 409 or 404 and write no change event."""
    try:
        action = await action_service.change_assignee(
            company_id=UUID(auth_context.company_id),
            action_id=action_id,
            assigned_user_id=request.assigned_user_id,
            acting_user_id=UUID(auth_context.user_id),
        )
        return _to_action_response(action)
    except ActionNotFound as exc:
        logger.info("Update action assignee failed: action not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found") from exc
    except InvalidAssignee as exc:
        logger.info("Update action assignee failed: assignee not valid")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found") from exc
    except InvalidActionTransition as exc:
        logger.info("Update action assignee failed: invalid reassignment")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Update action assignee endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Action service unavailable",
        ) from exc
