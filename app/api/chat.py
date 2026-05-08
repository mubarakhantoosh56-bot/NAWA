from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.openai_client import ai_engine
from app.core.dependencies import get_auth_context, AuthContext

router = APIRouter(tags=["AI"])


class ChatRequest(BaseModel):
    company_id: str
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, auth_context: AuthContext = Depends(get_auth_context)):
    try:
        # Verify company_id matches authenticated token
        if request.company_id != auth_context.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized company_id"
            )

        result = await ai_engine.chat(
            session_id=request.session_id,
            message=request.message,
            context=request.context,
            company_id=auth_context.company_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))