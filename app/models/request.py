from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for the AIMX chat endpoint."""

    company_id: str
    session_id: str
    message: str
    context: dict[str, Any] | None = None
