"""Auth API routes for AIMX register and login."""

import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext, get_auth_context
from app.models.request import AuthLoginRequest, AuthRegisterRequest
from app.models.response import AuthMeResponse, AuthResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


async def get_auth_service(request: Request) -> AuthService:
    """Return an AuthService backed by a lazily initialized asyncpg pool."""
    pool = getattr(request.app.state, "auth_db_pool", None)
    if pool is None:
        if not settings.DATABASE_URL:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            )
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5,
        )
        request.app.state.auth_db_pool = pool

    return AuthService(pool)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: AuthRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Register a company owner and return auth tokens."""
    try:
        result = await auth_service.register(
            company_slug=request.company_slug,
            company_name=request.company_name,
            owner_email=request.owner_email,
            owner_full_name=request.owner_full_name,
            password=request.password,
        )
        return AuthResponse.model_validate(result)
    except ValueError as exc:
        logger.info("Register failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Register endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service unavailable",
        ) from exc


@router.post("/login", response_model=AuthResponse)
async def login(
    request: AuthLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Authenticate a user for one company and return auth tokens."""
    try:
        result = await auth_service.login(
            email=request.email,
            password=request.password,
            company_slug=request.company_slug,
        )
        return AuthResponse.model_validate(result)
    except ValueError as exc:
        logger.info("Login failed with safe domain error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid email, password, or company",
        ) from exc
    except Exception as exc:
        logger.error("Login endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service unavailable",
        ) from exc


@router.get("/me", response_model=AuthMeResponse)
async def me(
    auth_context: AuthContext = Depends(get_auth_context),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthMeResponse:
    """Return the current authenticated user context."""
    try:
        result = await auth_service.get_current_context(
            company_id=auth_context.company_id,
            user_id=auth_context.user_id,
        )
        return AuthMeResponse.model_validate(result)
    except ValueError as exc:
        logger.info("Current auth context failed validation")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid authenticated context",
        ) from exc
    except Exception as exc:
        logger.error("Current auth context endpoint failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service unavailable",
        ) from exc
