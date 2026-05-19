from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the NAWA chat endpoint."""

    company_id: str
    session_id: str
    message: str
    context: dict[str, Any] | None = None
    department_id: str | None = None


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


class DepartmentCreateRequest(BaseModel):
    """Request body for creating a department."""

    name: str
    department_type: str
    description: str | None = None
    ai_agent_enabled: bool = False
    ai_agent_config: dict[str, object] | None = None


class DepartmentUpdateRequest(BaseModel):
    """Request body for updating a department."""

    name: str | None = None
    department_type: str | None = None
    description: str | None = None
    ai_agent_enabled: bool | None = None
    ai_agent_config: dict[str, object] | None = None


class CompanyIntelligenceProfileRequest(BaseModel):
    """Editable MVP company intelligence profile."""

    company_name: str = ""
    industry: str = ""
    business_type: str = ""
    country_market: str = ""
    company_size: str = ""
    departments_enabled: list[str] = Field(default_factory=list)
    primary_goals: str = ""
    current_operational_challenges: str = ""
    growth_priorities: str = ""
    preferred_response_language: str = "en"


class OperationalInputRequest(BaseModel):
    """Lightweight operational form submission for one workspace."""

    department_id: str
    department_type: str
    form_type: str = "daily_input"
    metrics: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    severity: str = "normal"
