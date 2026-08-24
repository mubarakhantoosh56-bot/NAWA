import logging
from typing import Any
from uuid import UUID

import asyncpg
from fastapi import APIRouter, HTTPException, Depends, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import has_permission, require_permission
from app.core.role_permissions import CEO_WORKSPACE_PERMISSION
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.repositories.company_repository import CompanyRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.organizational_intelligence_repository import OrganizationalIntelligenceRepository
from app.services.memory.repository import MemoryRepository
from app.services.company_profile import normalize_company_profile
from app.services.openai_client import ai_engine
from app.services.organizational_intelligence import build_organizational_intelligence
from app.services.unified_data_capture import UnifiedDataCaptureService

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
        await _capture_chat_input(
            http_request=http_request,
            request=request,
            auth_context=auth_context,
            context=context or {},
        )

        result = await ai_engine.chat(
            session_id=request.session_id,
            message=request.message,
            context=context,
            company_id=auth_context.company_id,
            # M8 Slice 3A: trusted, authenticated caller identity for live
            # reasoning-receipt creation - only ever from the JWT-derived
            # AuthContext, never the request body.
            created_by_user_id=auth_context.user_id,
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
    # Security: aimx_department is server-authoritative context (gates
    # pilot-specific Company Brain/Truth Context applicability). A client
    # can put anything in request.context, so any client-supplied
    # aimx_department must never survive into the authoritative context -
    # it is only ever set below, from a validated, company-scoped,
    # RBAC-checked department row.
    context.pop("aimx_department", None)
    context["nawa_role"] = {
        "slug": auth_context.role_slug,
        "permissions": auth_context.permissions,
    }
    company_repo = await _get_company_repository(http_request)
    profile = await company_repo.get_intelligence_profile(UUID(auth_context.company_id))
    normalized_profile = normalize_company_profile(profile)
    context["company_intelligence_profile"] = normalized_profile
    context["organizational_intelligence"] = await _build_organizational_context(
        http_request=http_request,
        company_id=UUID(auth_context.company_id),
        user_id=UUID(auth_context.user_id),
        company_profile=normalized_profile,
    )
    if normalized_profile.get("preferred_response_language") and not context.get("response_language"):
        context["response_language"] = normalized_profile["preferred_response_language"]

    if request.department_id is None:
        if not has_permission(auth_context.permissions, CEO_WORKSPACE_PERMISSION):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing permission",
            )
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


async def _build_organizational_context(
    *,
    http_request: Request,
    company_id: UUID,
    user_id: UUID,
    company_profile: dict[str, Any],
) -> dict[str, Any]:
    pool = getattr(http_request.app.state, "auth_db_pool", None)
    snapshot: dict[str, Any] | None = None
    if pool is not None:
        try:
            snapshot = await OrganizationalIntelligenceRepository(pool).get_snapshot(
                company_id=company_id,
                user_id=user_id,
            )
        except Exception:
            logger.warning(
                "organizational_intelligence_snapshot_failed",
                extra={"company_id": str(company_id)},
                exc_info=True,
            )
            snapshot = None
    return build_organizational_intelligence(
        company_profile=company_profile,
        snapshot=snapshot,
    )


async def _capture_chat_input(
    *,
    http_request: Request,
    request: ChatRequest,
    auth_context: AuthContext,
    context: dict[str, Any],
) -> None:
    pool = getattr(http_request.app.state, "auth_db_pool", None)
    if pool is None:
        return

    department_id = UUID(request.department_id) if request.department_id else None
    try:
        capture = await UnifiedDataCaptureService(pool).capture(
            company_id=UUID(auth_context.company_id),
            created_by=UUID(auth_context.user_id),
            source_type="chat",
            source_ref=request.session_id,
            raw_content=request.message,
            department_id=department_id,
            submitted_category=None,
            submitted_priority=None,
            payload={
                "session_id": request.session_id,
                "role_slug": auth_context.role_slug,
            },
        )
        context["latest_raw_input_id"] = str(capture.raw_input["id"])
        context["latest_structured_record_draft_id"] = str(capture.structured_draft["id"])
        context["latest_input_classification"] = _json_safe(capture.classification)

        if not capture.should_create_event:
            return

        classification = capture.classification
        department = (
            classification.get("inferred_department")
            or _department_key_from_context(context)
            or "company"
        )
        category = str(classification.get("category") or "daily_update")
        priority = str(classification.get("priority") or "normal")
        await MemoryRepository(pool).insert_event(
            {
                "company_id": auth_context.company_id,
                "session_id": request.session_id,
                "event_type": f"operational.{department}.{category}",
                "user_message": "Chat operational input captured",
                "executive_summary": f"{str(department).title()} {category} ({priority}): {request.message[:500]}",
                "logic_json": {
                    "operational_event": True,
                    "raw_input_id": str(capture.raw_input["id"]),
                    "structured_record_draft_id": str(capture.structured_draft["id"]),
                    "classification": _json_safe(capture.classification),
                    "parsed_entities": _json_safe(capture.entities),
                },
                "context": {
                    "source": "chat",
                    "source_role": auth_context.role_slug,
                    "source_department": _department_key_from_context(context),
                    "target_department": department,
                    "category": category,
                    "priority": priority,
                    "raw_input_id": str(capture.raw_input["id"]),
                    "structured_record_draft_id": str(capture.structured_draft["id"]),
                    "classification": _json_safe(capture.classification),
                    "parsed_entities": _json_safe(capture.entities),
                    "payload": {"text": request.message[:2000]},
                },
                "tags": ["operational_event", str(department), category, priority, "chat"],
                "idempotency_key": f"chat:{auth_context.company_id}:{request.session_id}:{capture.raw_input['id']}",
            }
        )
    except Exception:
        logger.warning(
            "chat_raw_input_capture_failed",
            extra={"company_id": auth_context.company_id, "session_id": request.session_id},
            exc_info=True,
        )


def _department_key_from_context(context: dict[str, Any]) -> str | None:
    department = context.get("aimx_department") if isinstance(context.get("aimx_department"), dict) else {}
    department_type = str(department.get("department_type") or "").strip().lower()
    return department_type.removesuffix("_ai") or None


def _json_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
