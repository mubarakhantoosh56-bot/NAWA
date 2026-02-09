from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.openai_client import ai_engine

router = APIRouter(tags=["AI"])


class ChatRequest(BaseModel):
    company_id: str                 # ✅ الجديد
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        result = await ai_engine.chat(
    session_id=request.session_id,
    message=request.message,
    context=request.context,
    company_id=request.company_id
)
        return result 

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))