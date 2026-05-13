import logging

from fastapi import APIRouter, HTTPException, Depends, status

from app.services.openai_client import ai_engine
from app.core.dependencies import AuthContext
from app.core.permissions import require_permission
from app.models.request import ChatRequest
from app.models.response import ChatResponse

router = APIRouter(tags=["AI"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    auth_context: AuthContext = Depends(require_permission("ai.chat")),
) -> ChatResponse:
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
        return ChatResponse.model_validate(result)
    except HTTPException as e:
        if e.status_code >= 500:
            logger.error(
                "Chat endpoint failed with service error",
                extra={"company_id": auth_context.company_id, "session_id": request.session_id},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
        raise
    except Exception as e:
        logger.error(
            "Chat endpoint failed",
            extra={"company_id": auth_context.company_id, "session_id": request.session_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
