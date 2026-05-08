from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import validate_token, InvalidToken, TokenExpired


bearer_scheme = HTTPBearer(auto_error=False)


class AuthContext:
    """Authenticated user context extracted from JWT token."""

    def __init__(self, company_id: str, user_id: str):
        self.company_id = company_id
        self.user_id = user_id


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthContext:
    """
    Validate JWT Bearer token and return authenticated context.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = validate_token(credentials.credentials)
        return AuthContext(
            company_id=payload["company_id"],
            user_id=payload["user_id"],
        )
    except (InvalidToken, TokenExpired) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )