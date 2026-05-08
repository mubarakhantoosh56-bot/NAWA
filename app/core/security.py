from datetime import datetime, timedelta
from typing import Dict, Any
import jwt

from app.core.config import settings

JWT_ALGORITHM = "HS256"


class TokenExpired(Exception):
    """Raised when token has expired."""
    pass


class InvalidToken(Exception):
    """Raised when token is invalid or malformed."""
    pass


def create_token(
    company_id: str,
    user_id: str,
    expires_in_hours: int = 24,
) -> str:
    """
    Generate JWT token with company scope.

    Args:
        company_id: Company identifier
        user_id: User identifier
        expires_in_hours: Token expiration time in hours

    Returns:
        Encoded JWT token
    """
    payload = {
        "company_id": company_id,
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload containing company_id, user_id, exp, iat

    Raises:
        TokenExpired: If token has expired
        InvalidToken: If token is malformed, signature invalid, or missing required claims
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Validate required claims
        if not payload.get("company_id"):
            raise InvalidToken("Token missing or empty company_id")
        if not payload.get("user_id"):
            raise InvalidToken("Token missing or empty user_id")

        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpired("Token has expired")
    except jwt.InvalidTokenError as e:
        raise InvalidToken(f"Invalid token: {str(e)}")


def get_company_id_from_token(token: str) -> str:
    """Extract company_id from token without raising on expiry."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        return payload.get("company_id", "")
    except jwt.InvalidTokenError:
        return ""
