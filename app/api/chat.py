import logging
from typing import Any
from uuid import UUID

import asyncpg
from fastapi import APIRouter, HTTPException, Depends, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import has_permission, require_permission
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.repositories.company_repository import CompanyRepository
from app.repositories.department_repository import DepartmentRepository
from app.services.company_profile import normalize_company_profile
from app.services.openai_client import ai_engine

router = APIRouter(tags=["AI"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    http_request: Request,
    auth_context: AuthContext = Depends(require_permission("ai.chat")),
) -> ChatResponse:
    try:
        # Verify company_id matches authenticated token
        if request.company_id != auth_context.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized company_id"
            )

        context = await _build_chat_context(
            http_request=http_request,
            request=request,
            auth_context=auth_context,
        )

        result = await ai_engine.chat(
            session_id=request.session_id,
            message=request.message,
            context=context,
            company_id=auth_context.company_id,
        )
        return ChatResponse.model_validate(result)
    except HTTPException as e:
        if e.status_code >= 500:
            logger.error(
                "Chat endpoint failed with service error",
                extra={"company_id": auth_context.company_id, "session_id": request.session_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
        raise
    except Exception as e:
        logger.error(
            "Chat endpoint failed",
            extra={"company_id": auth_context.company_id, "session_id": request.session_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


async def _build_chat_context(
    http_request: Request,
    request: ChatRequest,
    auth_context: AuthContext,
) -> dict[str, Any] | None:
    context = dict(request.context or {})
    company_repo = await _get_company_repository(http_request)
    profile = await company_repo.get_intelligence_profile(UUID(auth_context.company_id))
    normalized_profile = normalize_company_profile(profile)
    context["company_intelligence_profile"] = normalized_profile
    if normalized_profile.get("preferred_response_language") and not context.get("response_language"):
        context["response_language"] = normalized_profile["preferred_response_language"]

    if request.department_id is None:
        return context

    try:
        company_id = UUID(auth_context.company_id)
        department_id = UUID(request.department_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid department_id",
        ) from exc

    department_repo = await _get_department_repository(http_request)
    department = await department_repo.get_by_id(
        company_id=company_id,
        department_id=department_id,
    )
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid department access",
        )

    department_type = str(department.get("department_type") or "")
    required_permission = f"agents.{department_type}.use"
    if not has_permission(auth_context.permissions, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing permission",
        )

    context["aimx_department"] = {
        "id": str(department["id"]),
        "name": department["name"],
        "slug": department["slug"],
        "department_type": department_type,
        "ai_agent_enabled": department["ai_agent_enabled"],
    }
    return context


async def _get_company_repository(request: Request) -> CompanyRepository:
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Company service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return CompanyRepository(pool)


async def _get_department_repository(request: Request) -> DepartmentRepository:
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

    return DepartmentRepository(pool)
