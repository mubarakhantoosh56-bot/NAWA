from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from fastapi import HTTPException
from app.services.output_formatter import format_ai_response
from app.core.config import settings
from app.core.aimx_prompt import AIMX_SYSTEM_PROMPT
from app.core.decision_prompt import AIMX_DECISION_PROMPT
from app.services.memory.event_log import log_decision_event



class AIService:
    def __init__(self) -> None:
        """
        AIMX Async Engine (MVP Stable)
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # In-memory short-term memory
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_history: int = 10

    def _memory_key(self, company_id: str, session_id: str) -> str:
        return f"{company_id}:{session_id}"

    async def chat(
        self,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        company_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        context = context or {}
        company_id = company_id or "default"
        key = self._memory_key(company_id, session_id)

        # Ensure session exists
        if key not in self.sessions:
            self.sessions[key] = []

        try:
            # 1) Company context block
            context_block = (
                "COMPANY CONTEXT (CORE BRAIN MODEL):\n"
                f"Stage: {context.get('stage', 'N/A')}\n"
                f"Size: {context.get('size', 'N/A')}\n"
                f"Industry: {context.get('industry', 'N/A')}\n"
                f"Resources: {context.get('resources', 'N/A')}\n"
            )

            # 2) Build messages
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": AIMX_SYSTEM_PROMPT},
                {"role": "system", "content": AIMX_DECISION_PROMPT},
                {"role": "system", "content": context_block},
            ]


            # add previous memory
            messages.extend(self.sessions[key])

            # add user
            messages.append({"role": "user", "content": message})

            # 3) OpenAI call
            model_name = getattr(settings, "MODEL", "gpt-4o-mini")

            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.4,
            )

            answer_text = resp.choices[0].message.content or "لم يتم توليد رد."

            # 4) Event log (don’t break if log fails)
            try:
                log_decision_event(
                    company_id=company_id,
                    session_id=session_id,
                    payload={"answer": answer_text, "context": context},
                )
            except Exception as log_err:
                print(f"[EVENT LOG WARNING] {log_err}")

            # 5) Update short memory
            self.sessions[key].append({"role": "user", "content": message})
            self.sessions[key].append({"role": "assistant", "content": answer_text})

            if len(self.sessions[key]) > self.max_history * 2:
                self.sessions[key] = self.sessions[key][-self.max_history * 2 :]

            return format_ai_response (
                answer_text=answer_text,
                context=context,
                session_id=session_id,
                company_id=company_id,
                followup_question=None,
     )

        except Exception as e:
            print(f"[CRITICAL AI ERROR] {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"AIMX engine failed: {str(e)}",
            )


ai_engine = AIService()