"""Company Intelligence Profile API routes."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.models.request import CompanyIntelligenceProfileRequest
from app.models.response import CompanyIntelligenceProfileResponse
from app.repositories.company_repository import CompanyRepository
from app.repositories.organizational_intelligence_repository import OrganizationalIntelligenceRepository
from app.services.company_profile import normalize_company_profile
from app.services.organizational_intelligence import build_organizational_intelligence

router = APIRouter(prefix="/company/intelligence-profile", tags=["Company"])
logger = logging.getLogger(__name__)


async def get_company_repository(request: Request) -> CompanyRepository:
    """Return a CompanyRepository backed by the app database pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Company profile service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return CompanyRepository(pool)


@router.get("", response_model=CompanyIntelligenceProfileResponse)
async def get_intelligence_profile(
    auth_context: AuthContext = Depends(require_permission("ai.chat")),
    company_repo: CompanyRepository = Depends(get_company_repository),
) -> CompanyIntelligenceProfileResponse:
    """Return the authenticated company's persistent intelligence profile."""
    try:
        profile = await company_repo.get_intelligence_profile(UUID(auth_context.company_id))
        return CompanyIntelligenceProfileResponse.model_validate(
            normalize_company_profile(profile),
        )
    except Exception as exc:
        logger.error("Get company intelligence profile failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Company profile service unavailable",
        ) from exc


@router.put("", response_model=CompanyIntelligenceProfileResponse)
async def update_intelligence_profile(
    request: CompanyIntelligenceProfileRequest,
    auth_context: AuthContext = Depends(require_permission("ai.chat")),
    company_repo: CompanyRepository = Depends(get_company_repository),
) -> CompanyIntelligenceProfileResponse:
    """Persist the authenticated company's intelligence profile."""
    try:
        normalized = normalize_company_profile(request.model_dump())
        saved = await company_repo.update_intelligence_profile(
            company_id=UUID(auth_context.company_id),
            profile=normalized,
            updated_by_user_id=UUID(auth_context.user_id),
        )
        if saved is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        return CompanyIntelligenceProfileResponse.model_validate(
            normalize_company_profile(saved),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Update company intelligence profile failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Company profile service unavailable",
        ) from exc


@router.get("/organizational-intelligence")
async def get_organizational_intelligence(
    request: Request,
    auth_context: AuthContext = Depends(require_permission("ai.chat")),
    company_repo: CompanyRepository = Depends(get_company_repository),
) -> dict[str, object]:
    """Return the company-brain organizational context for the authenticated tenant."""
    try:
        company_id = UUID(auth_context.company_id)
        profile = normalize_company_profile(await company_repo.get_intelligence_profile(company_id))
        pool = getattr(request.app.state, "auth_db_pool", None)
        snapshot = None
        if pool is not None:
            snapshot = await OrganizationalIntelligenceRepository(pool).get_snapshot(
                company_id=company_id,
                user_id=UUID(auth_context.user_id),
            )
        return build_organizational_intelligence(
            company_profile=profile,
            snapshot=snapshot,
        )
    except Exception as exc:
        logger.error("Get organizational intelligence failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Organizational intelligence service unavailable",
        ) from exc
