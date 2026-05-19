"""Operational input routes for lightweight NAWA FMCG forms."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import has_permission, require_permission
from app.core.role_permissions import OPERATIONAL_FORM_SUBMIT_PERMISSION
from app.models.request import OperationalInputRequest
from app.models.response import OperationalInputResponse
from app.repositories.department_repository import DepartmentRepository
from app.services.operational_input_service import OPERATIONAL_FIELDS, OperationalInputService

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
    """Store one lightweight daily operational input as a memory event."""
    try:
        company_id = UUID(auth_context.company_id)
        user_id = UUID(auth_context.user_id)
        department_id = UUID(request.department_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid operational input scope",
        ) from exc

    department_type = request.department_type.strip().lower()
    if department_type not in OPERATIONAL_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported operational form department",
        )

    required_agent_permission = f"agents.{department_type}.use"
    if not has_permission(auth_context.permissions, required_agent_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission",
        )

    pool = await _get_pool(http_request)
    department_repo = DepartmentRepository(pool)
    department = await department_repo.get_by_id(company_id=company_id, department_id=department_id)
    if department is None or str(department.get("department_type") or "") != department_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid department access",
        )

    try:
        result = await operational_service.submit_input(
            company_id=company_id,
            user_id=user_id,
            department_id=department_id,
            department_type=department_type,
            form_type=request.form_type,
            metrics=request.metrics,
            notes=request.notes,
            severity=request.severity,
        )
        return OperationalInputResponse.model_validate(result)
    except Exception as exc:
        logger.error("Operational input submission failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operational input service unavailable",
        ) from exc


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
