from typing import Dict, Any, Optional, List
import json

from openai import AsyncOpenAI
from fastapi import HTTPException

from app.services.output_formatter import format_ai_response
from app.core.config import settings
from app.core.aimx_prompt import AIMX_SYSTEM_PROMPT
from app.core.decision_prompt import AIMX_DECISION_PROMPT

from app.services.memory.event_log import log_decision_event, log_decision_event_db
from app.services.memory.repository import MemoryRepository
from app.services.memory.memory_prompt import build_memory_block


class AIService:
    def __init__(self) -> None:
        print("DB_URL=", getattr(settings, "DATABASE_URL", "MISSING"))
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # In-memory short-term memory
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_history: int = 10

        # DB memory
        self.db_pool = None
        self.repo: Optional[MemoryRepository] = None
        self.db_enabled: bool = bool(getattr(settings, "DATABASE_URL", ""))

    def _memory_key(self, company_id: str, session_id: str) -> str:
        return f"{company_id}:{session_id}"

    async def _ensure_db(self) -> None:
        """Lazy init asyncpg pool + repo (safe)."""
        if not self.db_enabled:
            return
        if self.repo is not None:
            return

        db_url = getattr(settings, "DATABASE_URL", "")
        if not db_url:
            self.db_enabled = False
            return

        try:
            import asyncpg  # type: ignore
            self.db_pool = await asyncpg.create_pool(
                dsn=db_url,
                min_size=1,
                max_size=5,
            )
            self.repo = MemoryRepository(db=self.db_pool)
            print("[DB] Institutional Memory Enabled ✅")
        except Exception as e:
            print(f"[DB INIT FAILED] {e}")
            self.db_pool = None
            self.repo = None
            self.db_enabled = False

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

        if key not in self.sessions:
            self.sessions[key] = []

        try:
            # 1) context block
            context_block = (
                "COMPANY CONTEXT:\n"
                f"Stage: {context.get('stage', 'N/A')}\n"
                f"Size: {context.get('size', 'N/A')}\n"
                f"Industry: {context.get('industry', 'N/A')}\n"
                f"Resources: {context.get('resources', 'N/A')}\n"
            )

            # 2) DB memory block (Session -> fallback Company)
            memory_block = ""
            await self._ensure_db()

            if self.repo is not None:
                try:
                    # (A) أول شي: نفس السيشن
                    recent = await self.repo.fetch_recent_events(
                        company_id=company_id,
                        session_id=session_id,
                        limit=8,
                    )

                    # (B) إذا فاضي (مثل s100 جديد): fallback على الشركة كلها
                    if not recent:
                        recent = await self.repo.fetch_recent_events(
                            company_id=company_id,
                            session_id=None,
                            limit=10,
                        )

                    memory_block = build_memory_block(recent) or ""

                    # ✅ Debug خفيف حتى نتأكد injection شغال
                    print("[MEMORY] events_fetched =", len(recent))
                    if memory_block:
                        preview = "\n".join(memory_block.splitlines()[:3])
                        print("[MEMORY] block_preview:\n", preview)
                    else:
                        print("[MEMORY] block is EMPTY")

                except Exception as e:
                    print(f"[MEMORY BLOCK WARNING] {e}")
                    memory_block = ""

            messages: List[Dict[str, str]] = [
                # 1️⃣ Global guardrails
                {"role": "system", "content": AIMX_SYSTEM_PROMPT},

                # 2️⃣ Strict output contract + schema
                {"role": "system", "content": AIMX_DECISION_PROMPT},
        ]

                # 3️⃣ Institutional Memory (إذا موجود)
            if memory_block:
                    messages.append({
                        "role": "system",
                        "content": memory_block
                    })

                # 4️⃣ Company Context (آخر system message قبل user)
                    messages.append({
                        "role": "system",
                        "content": context_block
                })

            # include last short memory (in-memory)
            messages.extend(self.sessions[key])
            messages.append({"role": "user", "content": message})

            # 4) openai call
            model_name = getattr(settings, "MODEL", "gpt-4o-mini")
            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            answer_text = resp.choices[0].message.content or "لم يتم توليد رد."
            parsed: Optional[Dict[str, Any]] = None
            try:
                parsed = json.loads(answer_text)
            except Exception:
                parsed = None

            # 5) old file log (optional)
            try:
                log_decision_event(
                    company_id=company_id,
                    session_id=session_id,
                    payload={"answer": answer_text, "parsed": parsed, "context": context},
                )
            except Exception as e:
                print(f"[FILE LOG WARNING] {e}")

            # 6) DB log (Institutional Memory)
            if self.repo is not None and isinstance(parsed, dict):
                try:
                    executive_summary = parsed.get("executive_summary", "") or ""
                    raw_decision = parsed.get("raw_decision", {}) or {}

                    await log_decision_event_db(
                        repo=self.repo,
                        company_id=company_id,
                        session_id=session_id,
                        user_message=message,
                        executive_summary=executive_summary,
                        logic_json=raw_decision,
                        context=context,
                        tags=[context.get("industry", "unknown")],
                    )
                except Exception as e:
                    print(f"[DB EVENT LOG WARNING] {e}")

            # 7) update in-memory
            self.sessions[key].append({"role": "user", "content": message})
            self.sessions[key].append({"role": "assistant", "content": answer_text})
            if len(self.sessions[key]) > self.max_history * 2:
                self.sessions[key] = self.sessions[key][-self.max_history * 2 :]

            # 8) return formatted response
            return format_ai_response(
                answer_text=answer_text,
                context=context,
                session_id=session_id,
                company_id=company_id,
                followup_question=None,
                parsed=parsed,
            )

        except Exception as e:
            print(f"[CRITICAL AI ERROR] {str(e)}")
            raise HTTPException(status_code=500, detail=f"AIMX engine failed: {str(e)}")


ai_engine = AIService()