"""Live Operational Timeline API routes."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.core.role_permissions import (
    OPERATIONAL_FORM_READ_PERMISSION,
    OPERATIONAL_FORM_SUBMIT_PERMISSION,
)
from app.models.request import OperationalEventCreateRequest
from app.models.response import OperationalEventListResponse, OperationalEventResponse
from app.services.operational_event_service import OperationalEventService

router = APIRouter(prefix="/operational-events", tags=["Operational Events"])
logger = logging.getLogger(__name__)


async def get_operational_event_service(request: Request) -> OperationalEventService:
    """Return an OperationalEventService backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Operational timeline service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return OperationalEventService(pool)


@router.post("", response_model=OperationalEventResponse, status_code=status.HTTP_201_CREATED)
async def create_operational_event(
    request: OperationalEventCreateRequest,
    auth_context: AuthContext = Depends(
        # Temporary until timeline-specific permissions are added.
        require_permission(OPERATIONAL_FORM_SUBMIT_PERMISSION),
    ),
    event_service: OperationalEventService = Depends(get_operational_event_service),
) -> OperationalEventResponse:
    """Create one operational event for the authenticated company timeline."""
    try:
        company_id = UUID(auth_context.company_id)
        if request.company_id is not None and UUID(request.company_id) != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="company_id does not match authenticated company",
            )

        event = await event_service.create_event(
            company_id=company_id,
            user_id=UUID(auth_context.user_id),
            department_id=UUID(request.department_id) if request.department_id else None,
            event_type=request.event_type,
            category=request.category,
            priority=request.priority,
            title=request.title,
            summary=request.summary,
            event_timestamp=request.event_timestamp,
            source_type=request.source_type,
            source_ref=request.source_ref,
            payload=request.payload,
            metadata=request.metadata,
        )
        return OperationalEventResponse.model_validate(event)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("Create operational event failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Create operational event endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational timeline service unavailable",
        ) from exc


@router.get("", response_model=OperationalEventListResponse)
async def list_operational_events(
    auth_context: AuthContext = Depends(
        # Temporary until timeline-specific permissions are added.
        require_permission(OPERATIONAL_FORM_READ_PERMISSION),
    ),
    event_service: OperationalEventService = Depends(get_operational_event_service),
    department_id: UUID | None = None,
    category: str | None = None,
    priority: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OperationalEventListResponse:
    """Return operational timeline events for the authenticated company."""
    try:
        events = await event_service.list_events(
            company_id=UUID(auth_context.company_id),
            department_id=department_id,
            category=category,
            priority=priority,
            limit=limit,
            offset=offset,
        )
        return OperationalEventListResponse.model_validate({"events": events})
    except ValueError as exc:
        logger.info("List operational events failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("List operational events endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational timeline service unavailable",
        ) from exc
