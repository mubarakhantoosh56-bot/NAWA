from typing import Any

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
