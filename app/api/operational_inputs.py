"""Operational input routes for universal NAWA updates."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import has_permission, require_permission
from app.core.role_permissions import CEO_WORKSPACE_PERMISSION, OPERATIONAL_FORM_SUBMIT_PERMISSION
from app.models.request import OperationalInputRequest
from app.models.response import OperationalInputResponse
from app.repositories.department_repository import DepartmentRepository
from app.repositories.unified_data_capture_repository import UnifiedDataCaptureRepository
from app.services.operational_input_service import OperationalInputService

router = APIRouter(prefix="/operational-inputs", tags=["Operational Inputs"])
logger = logging.getLogger(__name__)


async def get_operational_input_service(request: Request) -> OperationalInputService:
    pool = await _get_pool(request)
    return OperationalInputService(pool)


@router.post("", response_model=OperationalInputResponse, status_code=status.HTTP_201_CREATED)
async def submit_operational_input(
    request: OperationalInputRequest,
    http_request: Request,
    auth_context: AuthContext = Depends(require_permission(OPERATIONAL_FORM_SUBMIT_PERMISSION)),
    operational_service: OperationalInputService = Depends(get_operational_input_service),
) -> OperationalInputResponse:
    """Store one universal operational update as a memory event."""
    try:
        company_id = UUID(auth_context.company_id)
        user_id = UUID(auth_context.user_id)
        source_department_id = UUID(request.department_id) if request.department_id else None
        target_department_id = UUID(request.target_department_id) if request.target_department_id else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid operational input scope",
        ) from exc

    pool = await _get_pool(http_request)
    department_repo = DepartmentRepository(pool)
    source_department_type = await _resolve_department_type(
        department_repo=department_repo,
        company_id=company_id,
        department_id=source_department_id,
        submitted_type=request.department_type,
        auth_context=auth_context,
        allow_company_wide=has_permission(auth_context.permissions, CEO_WORKSPACE_PERMISSION),
    )
    target_department_type = await _resolve_department_type(
        department_repo=department_repo,
        company_id=company_id,
        department_id=target_department_id,
        submitted_type=request.target_department_type,
        auth_context=auth_context,
        allow_company_wide=True,
        require_agent_permission=False,
    )

    try:
        result = await operational_service.submit_input(
            company_id=company_id,
            user_id=user_id,
            source_role=auth_context.role_slug or "unknown",
            source_department_id=source_department_id,
            source_department_type=source_department_type,
            target_department_id=target_department_id,
            target_department_type=target_department_type,
            category=request.category,
            priority=request.priority,
            event_date=request.event_date,
            text=request.text,
            metrics=request.metrics,
            files_attached=request.files_attached,
            payload=request.payload,
        )
        return OperationalInputResponse.model_validate(result)
    except Exception as exc:
        logger.error("Operational input submission failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational input service unavailable",
        ) from exc


@router.get("/debug/{raw_input_id}")
async def get_raw_input_debug(
    raw_input_id: UUID,
    http_request: Request,
    auth_context: AuthContext = Depends(require_permission(CEO_WORKSPACE_PERMISSION)),
) -> dict[str, object]:
    """Inspect the unified data capture pipeline for one raw input."""
    pool = await _get_pool(http_request)
    repo = UnifiedDataCaptureRepository(pool)
    snapshot = await repo.get_debug_snapshot(
        company_id=UUID(auth_context.company_id),
        raw_input_id=raw_input_id,
    )
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw input not found",
        )
    return snapshot


async def _resolve_department_type(
    *,
    department_repo: DepartmentRepository,
    company_id: UUID,
    department_id: UUID | None,
    submitted_type: str | None,
    auth_context: AuthContext,
    allow_company_wide: bool,
    require_agent_permission: bool = True,
) -> str | None:
    if department_id is None:
        if allow_company_wide:
            return None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department scope is required",
        )

    department = await department_repo.get_by_id(company_id=company_id, department_id=department_id)
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid department access",
        )

    department_type = str(department.get("department_type") or "")
    if submitted_type and submitted_type.strip().lower() != department_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department type does not match department_id",
        )

    if require_agent_permission and not has_permission(
        auth_context.permissions,
        f"agents.{department_type}.use",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission",
        )

    return department_type


async def _get_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Operational input service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool
    return pool
