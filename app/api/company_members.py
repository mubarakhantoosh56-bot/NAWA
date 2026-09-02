"""M9 Slice 3 completion pass: bounded, read-only company-member source.

Exists for exactly one MVP purpose (Founder Decision): let the Action UI
list/select humans who may responsibly own an Action. It is deliberately
NOT a people directory, not an HR endpoint, not an org chart, not an
employee search engine, and not role/permission management - see
docs/execution/m9/M9_SLICE3_FRONTEND_GOLDEN_PATH.md for the scoped decision.

No new permission is introduced: this reuses the same "memory.write"
permission that already authorizes every Action operation, since this
endpoint exists solely to serve that flow.
"""

from __future__ import annotations

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.repositories.membership_repository import MembershipRepository

router = APIRouter(prefix="/company", tags=["Company Members"])
logger = logging.getLogger(__name__)

COMPANY_MEMBERS_READ_PERMISSION = "memory.write"


class CompanyMemberResponse(BaseModel):
    """Minimum fields the Action assignee selector needs. Deliberately
    excludes membership id, company_id, role/permissions, department,
    invitation metadata, and any other profile data."""

    id: UUID
    full_name: str
    email: str


async def get_membership_repository(request: Request) -> MembershipRepository:
    """Return a MembershipRepository backed by the app database pool -
    identical dependency pattern to app/api/actions.py's get_action_service."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Company member service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return MembershipRepository(pool)


@router.get("/members", response_model=list[CompanyMemberResponse])
async def list_company_members(
    auth_context: AuthContext = Depends(require_permission(COMPANY_MEMBERS_READ_PERMISSION)),
    membership_repository: MembershipRepository = Depends(get_membership_repository),
) -> list[CompanyMemberResponse]:
    """Return one row per distinct user holding at least one ACTIVE,
    non-deleted membership in the authenticated company. company_id is
    always derived from AuthContext (JWT), never from client input -
    there is no way to request another company's members through this
    endpoint. Read-only: no mutation exists on this router."""
    try:
        members = await membership_repository.list_active_company_members(
            company_id=UUID(auth_context.company_id),
        )
        return [CompanyMemberResponse.model_validate(member) for member in members]
    except Exception as exc:
        logger.error("List company members endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Company member service unavailable",
        ) from exc
