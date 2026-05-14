from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMeta(BaseModel):
    """Metadata returned with every AIMX chat response."""

    company_id: str | None = None
    session_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    parse_ok: bool
    memory_injected: bool
    events_count: int


class ChatResponse(BaseModel):
    """Stable top-level response contract for AIMX chat."""

    ceo_text: str
    logic_json: dict[str, Any]
    followup_question: str | None = None
    meta: ChatMeta


class AuthCompanyResponse(BaseModel):
    """Safe company fields returned by auth endpoints."""

    id: UUID
    slug: str
    name: str
    status: str
    plan: str


class AuthUserResponse(BaseModel):
    """Safe user fields returned by auth endpoints."""

    id: UUID
    email: str
    full_name: str
    status: str
    auth_provider: str


class AuthMembershipResponse(BaseModel):
    """Safe membership fields returned by auth endpoints."""

    id: UUID
    company_id: UUID
    user_id: UUID
    role_id: UUID
    department_id: UUID | None = None
    status: str


class AuthResponse(BaseModel):
    """Structured token response returned by register and login."""

    access_token: str
    refresh_token: str
    token_type: str
    company: AuthCompanyResponse
    user: AuthUserResponse
    membership: AuthMembershipResponse


class AuthRoleResponse(BaseModel):
    """Safe role fields returned for the current auth context."""

    id: UUID
    slug: str
    name: str
    permissions: list[str]
    is_system_role: bool


class AuthMeResponse(BaseModel):
    """Current authenticated user context for dashboard clients."""

    company: AuthCompanyResponse
    user: AuthUserResponse
    membership: AuthMembershipResponse
    role: AuthRoleResponse


class DepartmentResponse(BaseModel):
    """Safe department fields returned by department endpoints."""

    id: UUID
    company_id: UUID
    name: str
    slug: str
    description: str | None = None
    department_type: str
    ai_agent_enabled: bool
    ai_agent_config: dict[str, object]


class DepartmentListResponse(BaseModel):
    """List response for tenant departments."""

    departments: list[DepartmentResponse]
