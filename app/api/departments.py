"""Department API routes for tenant-scoped department runtime."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.core.role_permissions import visible_department_types
from app.models.request import DepartmentCreateRequest, DepartmentUpdateRequest
from app.models.response import DepartmentListResponse, DepartmentResponse
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])
logger = logging.getLogger(__name__)


async def get_department_service(request: Request) -> DepartmentService:
    """Return a DepartmentService backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Department service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return DepartmentService(pool)


@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    auth_context: AuthContext = Depends(require_permission("departments.read")),
    department_service: DepartmentService = Depends(get_department_service),
) -> DepartmentListResponse:
    """Return departments for the authenticated tenant."""
    try:
        departments = await department_service.list_departments(
            company_id=UUID(auth_context.company_id),
        )
        visible_types = visible_department_types(auth_context.permissions)
        if visible_types is not None:
            departments = [
                department
                for department in departments
                if str(department.get("department_type") or "") in visible_types
            ]
        return DepartmentListResponse.model_validate({"departments": departments})
    except ValueError as exc:
        logger.info("List departments failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("List departments endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department service unavailable",
        ) from exc


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    request: DepartmentCreateRequest,
    auth_context: AuthContext = Depends(require_permission("departments.manage")),
    department_service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponse:
    """Create a department for the authenticated tenant."""
    try:
        department = await department_service.create_department(
            company_id=UUID(auth_context.company_id),
            name=request.name,
            department_type=request.department_type,
            description=request.description,
            ai_agent_enabled=request.ai_agent_enabled,
            ai_agent_config=request.ai_agent_config,
            created_by_user_id=UUID(auth_context.user_id),
        )
        return DepartmentResponse.model_validate(department)
    except ValueError as exc:
        logger.info("Create department failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Create department endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department service unavailable",
        ) from exc


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    request: DepartmentUpdateRequest,
    auth_context: AuthContext = Depends(require_permission("departments.manage")),
    department_service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponse:
    """Update a department for the authenticated tenant."""
    try:
        department = await department_service.update_department(
            company_id=UUID(auth_context.company_id),
            department_id=department_id,
            name=request.name,
            department_type=request.department_type,
            description=request.description,
            ai_agent_enabled=request.ai_agent_enabled,
            ai_agent_config=request.ai_agent_config,
            updated_by_user_id=UUID(auth_context.user_id),
        )
        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found",
            )
        return DepartmentResponse.model_validate(department)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.info("Update department failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Update department endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department service unavailable",
        ) from exc
