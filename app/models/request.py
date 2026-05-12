from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for the AIMX chat endpoint."""

    company_id: str
    session_id: str
    message: str
    context: dict[str, Any] | None = None


class AuthRegisterRequest(BaseModel):
    """Request body for registering a new company owner."""

    company_slug: str
    company_name: str
    owner_email: str
    owner_full_name: str
    password: str


class AuthLoginRequest(BaseModel):
    """Request body for logging into one tenant company."""

    email: str
    password: str
    company_slug: str
