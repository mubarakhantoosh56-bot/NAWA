from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMeta(BaseModel):
    """Metadata returned with every NAWA chat response."""

    company_id: str | None = None
    session_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    language: str | None = None
    parse_ok: bool
    memory_injected: bool
    events_count: int


class ChatResponse(BaseModel):
    """Stable top-level response contract for NAWA chat."""

    ceo_text: str
    logic_json: dict[str, Any]
    followup_question: str | None = None
    meta: ChatMeta


class CompanyIntelligenceProfileResponse(BaseModel):
    """Persisted MVP company intelligence profile."""

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
    is_active: bool = False


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


class FileResponse(BaseModel):
    """Safe file metadata returned by file endpoints."""

    id: UUID
    company_id: UUID
    department_id: UUID | None = None
    uploaded_by_user_id: UUID
    filename: str
    content_type: str
    file_size_bytes: int
    status: str
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class FileDetailResponse(FileResponse):
    """Safe file detail returned by file detail endpoint."""

    chunk_count: int = 0


class FileListResponse(BaseModel):
    """List response for tenant files."""

    files: list[FileResponse]


class OperationalInputResponse(BaseModel):
    """Safe response after storing a lightweight operational input."""

    status: str
    event_type: str
    department_id: UUID | None = None
    department_type: str | None = None
    target_department_id: UUID | None = None
    category: str
    priority: str
    summary: str
    memory_event_created: bool = True
    raw_input_id: UUID | None = None
    structured_record_draft_id: UUID | None = None
    classification: dict[str, Any] | None = None


class OperationalEventResponse(BaseModel):
    """Safe operational event returned by the Live Operational Timeline."""

    id: UUID
    company_id: UUID
    department_id: UUID | None = None
    created_by_user_id: UUID
    event_type: str
    category: str
    priority: str
    title: str
    summary: str
    event_timestamp: datetime
    source_type: str
    source_ref: str | None = None
    payload: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class OperationalEventListResponse(BaseModel):
    """List response for the Live Operational Timeline."""

    events: list[OperationalEventResponse]


class OperationalSituationResponse(BaseModel):
    """Safe operational situation returned by the feedback loop."""

    id: UUID
    company_id: UUID
    title: str
    summary: str
    situation_type: str
    severity: str
    status: str
    time_window_start: datetime
    time_window_end: datetime
    department_id: UUID | None = None
    detection_method: str
    source_type: str
    event_count: int = 0
    created_at: datetime
    updated_at: datetime


class OperationalSituationListResponse(BaseModel):
    """List response for operational situations."""

    situations: list[OperationalSituationResponse]


class OperationalSituationDetailResponse(OperationalSituationResponse):
    """Detailed operational situation with linked timeline events."""

    events: list[OperationalEventResponse]


class OperationalSituationGroupResponse(BaseModel):
    """Response returned after manual rule-based situation grouping."""

    created_situations: list[OperationalSituationResponse]
    created_count: int
    duplicate_clusters_skipped: int
    analyzed_event_count: int
    window_start: datetime
    window_end: datetime


class EventDraftResponse(BaseModel):
    """One AI-proposed operational event draft, pending human confirmation."""

    id: UUID
    company_id: UUID
    file_id: UUID
    department_id: UUID | None = None
    proposed_title: str
    proposed_category: str
    proposed_priority: str
    proposed_summary: str
    evidence_quote: str | None = None
    confidence: int
    needs_clarification: bool
    clarification_hint: str | None = None
    status: str
    confirmed_event_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class EventDraftListResponse(BaseModel):
    """Pending AI-proposed drafts for one file."""

    file_id: UUID
    drafts: list[EventDraftResponse]


class DraftConfirmResponse(BaseModel):
    """Returned after a draft is confirmed: the updated draft and the created event."""

    draft: EventDraftResponse
    event: OperationalEventResponse


class IntegrationProviderResponse(BaseModel):
    """MVP integration provider capability descriptor."""

    key: str
    name: str
    status: str
    ingestion_modes: list[str]
    description: str


class IntegrationProviderListResponse(BaseModel):
    """Available future operational-system providers."""

    providers: list[IntegrationProviderResponse]
