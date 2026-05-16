"""RBAC permission dependencies for protected NAWA endpoints."""

from collections.abc import Callable

import asyncpg
from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import AuthContext, get_auth_context
from app.services.auth_service import AuthService


def has_permission(permissions: list[object], required_permission: str) -> bool:
    """Return whether a permission list grants the required permission."""
    normalized_permissions = []
    for permission in permissions:
        if not isinstance(permission, str):
            return False
        stripped_permission = permission.strip()
        if not stripped_permission:
            return False
        normalized_permissions.append(stripped_permission)

    return "*" in normalized_permissions or required_permission in normalized_permissions


def require_permission(permission: str) -> Callable[..., object]:
    """Create a FastAPI dependency requiring one database-backed permission."""

    async def dependency(
        request: Request,
        auth_context: AuthContext = Depends(get_auth_context),
    ) -> AuthContext:
        auth_service = await _get_permission_auth_service(request)
        try:
            current_context = await auth_service.get_current_context(
                company_id=auth_context.company_id,
                user_id=auth_context.user_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid authenticated context",
            ) from exc

        role = current_context.get("role")
        if not isinstance(role, dict):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid authenticated context",
            )

        raw_permissions = role.get("permissions")
        if not isinstance(raw_permissions, list) or not has_permission(
            raw_permissions,
            permission,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing permission",
            )

        auth_context.permissions = [str(item).strip() for item in raw_permissions]
        auth_context.role_id = str(role.get("id") or "")
        auth_context.role_slug = str(role.get("slug") or "")
        return auth_context

    return dependency


async def _get_permission_auth_service(request: Request) -> AuthService:
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
