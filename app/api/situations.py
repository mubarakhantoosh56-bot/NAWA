"""Operational situations API routes."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.core.role_permissions import OPERATIONAL_FORM_READ_PERMISSION
from app.models.response import (
    OperationalSituationDetailResponse,
    OperationalSituationGroupResponse,
    OperationalSituationListResponse,
)
from app.services.operational_situation_service import OperationalSituationService

router = APIRouter(prefix="/situations", tags=["Operational Situations"])
logger = logging.getLogger(__name__)


async def get_operational_situation_service(request: Request) -> OperationalSituationService:
    """Return an OperationalSituationService backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Operational situations service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return OperationalSituationService(pool)


@router.post("/group", response_model=OperationalSituationGroupResponse)
async def group_operational_situations(
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_READ_PERMISSION)),
    situation_service: OperationalSituationService = Depends(get_operational_situation_service),
) -> OperationalSituationGroupResponse:
    """Manually group recent operational events into rule-based situations."""
    try:
        result = await situation_service.group_recent_events(
            company_id=UUID(auth_context.company_id),
            source_type="manual_rule",
        )
        return OperationalSituationGroupResponse.model_validate(result)
    except ValueError as exc:
        logger.info("Group operational situations failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Group operational situations endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational situations service unavailable",
        ) from exc


@router.get("", response_model=OperationalSituationListResponse)
async def list_operational_situations(
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_READ_PERMISSION)),
    situation_service: OperationalSituationService = Depends(get_operational_situation_service),
    status_filter: str | None = Query(default=None, alias="status"),
    department_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OperationalSituationListResponse:
    """Return operational situations for the authenticated company."""
    try:
        situations = await situation_service.list_situations(
            company_id=UUID(auth_context.company_id),
            status=status_filter,
            department_id=department_id,
            limit=limit,
            offset=offset,
        )
        return OperationalSituationListResponse.model_validate({"situations": situations})
    except ValueError as exc:
        logger.info("List operational situations failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("List operational situations endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational situations service unavailable",
        ) from exc


@router.get("/{situation_id}", response_model=OperationalSituationDetailResponse)
async def get_operational_situation(
    situation_id: UUID,
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_READ_PERMISSION)),
    situation_service: OperationalSituationService = Depends(get_operational_situation_service),
) -> OperationalSituationDetailResponse:
    """Return one operational situation with its linked events."""
    try:
        situation = await situation_service.get_situation(
            company_id=UUID(auth_context.company_id),
            situation_id=situation_id,
        )
        if situation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Situation not found",
            )
        return OperationalSituationDetailResponse.model_validate(situation)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("Get operational situation failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Get operational situation endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational situations service unavailable",
        ) from exc
