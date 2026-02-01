from fastapi import APIRouter
from pydantic import BaseModel

from app.core.aimx_prompt import AIMX_SYSTEM_PROMPT
from app.services.openai_client import get_openai_client
from app.services.memory import (
    get_history,
    add_user_message,
    add_assistant_message
)

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
def chat(payload: ChatRequest):
    session_id = payload.session_id.strip()
    user_msg = payload.message.strip()

    if not session_id or not user_msg:
        return {
            "error": "session_id and message are required"
        }

    try:
        # 1) خزّن رسالة المستخدم
        add_user_message(session_id, user_msg)

        # 2) ابنِ الرسائل (system + history)
        history = get_history(session_id)
        messages = [
            {"role": "system", "content": AIMX_SYSTEM_PROMPT.strip()}
        ] + history

        # 3) نداء OpenAI
        client = get_openai_client()
        response = client.responses.create(
            model="gpt-4o-mini",
            input=messages
        )

        reply_text = response.output_text

        # 4) خزّن رد المساعد
        add_assistant_message(session_id, reply_text)

        return {
            "session_id": session_id,
            "reply": reply_text,
            "memory_turns": len(get_history(session_id))
        }

    except Exception as e:
        return {
            "error": str(e),
            "where": "chat endpoint"
        }