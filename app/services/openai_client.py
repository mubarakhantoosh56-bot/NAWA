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


# -----------------------------
# Memory Intelligence Prompts
# -----------------------------
FACT_EXTRACTOR_SYSTEM = """
You are a memory extraction engine.
Extract durable facts that should be saved as Institutional Memory for a company.

Return ONLY valid JSON. No markdown. No extra text.

Schema:
{
  "facts": [
    {
      "fact_type": "company|product|process|goal|constraint|metric|risk|decision|other",
      "fact_key": "short_key",
      "fact_value": "plain text",
      "confidence": 0
    }
  ]
}

Rules:
- facts must be durable, not transient chat fluff.
- fact_key must be stable and reusable (e.g., "product_name", "mvp_stage", "target_market").
- confidence 0-100.
- If nothing to save, return {"facts": []}.
"""


def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        return None


def _build_facts_block(facts: List[Dict[str, Any]]) -> str:
    if not facts:
        return "INSTITUTIONAL FACTS (COMPANY TRUTHS): none"

    lines = ["INSTITUTIONAL FACTS (COMPANY TRUTHS):"]
    for f in facts[:25]:
        ft = (f.get("fact_type") or "other").strip()
        fk = (f.get("fact_key") or "").strip()
        fv = (f.get("fact_value") or "").strip()
        conf = f.get("confidence") or 0

        if len(fv) > 220:
            fv = fv[:220] + "..."

        if fk:
            lines.append(f"- [{ft}] {fk} = {fv} (conf:{conf})")
        else:
            lines.append(f"- [{ft}] {fv} (conf:{conf})")

    lines.append("RULES: These are the company's current truths. Use them for continuity. Do NOT repeat them in your output.")
    return "\n".join(lines)


class AIService:
    def __init__(self) -> None:
        print("DB_URL=", getattr(settings, "DATABASE_URL", "MISSING"))
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # In-memory short-term memory
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_history: int = 10

        # DB memory (لا تنشئ repo هنا!)
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

            self.db_pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=5)
            self.repo = MemoryRepository(db=self.db_pool)
            print("[DB] Institutional Memory Enabled ✅")

        except Exception as e:
            print(f"[DB INIT FAILED] {e}")
            self.db_pool = None
            self.repo = None
            self.db_enabled = False

    async def _extract_and_upsert_facts(
        self,
        company_id: str,
        session_id: str,
        user_message: str,
        executive_summary: str,
        raw_decision: Dict[str, Any],
    ) -> None:
        if self.repo is None:
            return

        payload = {
            "user_message": user_message,
            "executive_summary": executive_summary,
            "raw_decision": raw_decision,
        }

        messages = [
            {"role": "system", "content": FACT_EXTRACTOR_SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

        try:
            model_name = getattr(settings, "FACT_MODEL", getattr(settings, "MODEL", "gpt-4o-mini"))
            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            txt = resp.choices[0].message.content or '{"facts": []}'
            data = _safe_json_loads(txt) or {}
            facts = data.get("facts", [])

            if not isinstance(facts, list) or not facts:
                return

            normalized = 0
            for f in facts[:25]:
                if not isinstance(f, dict):
                    continue

                fact_type = (f.get("fact_type") or "other").strip()
                fact_key = (f.get("fact_key") or "").strip()
                fact_value = (f.get("fact_value") or "").strip()
                confidence = int(f.get("confidence") or 0)

                if not fact_value:
                    continue
                if not fact_key:
                    fact_key = "general_fact"

                await self.repo.upsert_fact(
                    company_id=company_id,
                    session_id=session_id,
                    fact_type=fact_type,
                    fact_key=fact_key,
                    fact_value=fact_value,
                    confidence=confidence,
                    source_event_id=None,
                )
                normalized += 1

            print(f"[FACTS] upserted = {normalized}")

        except Exception as e:
            print(f"[FACT EXTRACT WARNING] {e}")

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
            # 1) Context block
            context_block = (
                "COMPANY CONTEXT:\n"
                f"Stage: {context.get('stage', 'N/A')}\n"
                f"Size: {context.get('size', 'N/A')}\n"
                f"Industry: {context.get('industry', 'N/A')}\n"
                f"Resources: {context.get('resources', 'N/A')}\n"
            )

            # 2) DB memory blocks (Facts + Events)
            memory_events_block = ""
            memory_facts_block = ""

            await self._ensure_db()

            if self.repo is not None:
                try:
                    recent_events = await self.repo.fetch_recent_events(
                        company_id=company_id,
                        session_id=session_id,
                        limit=8,
                    )
                    if not recent_events:
                        recent_events = await self.repo.fetch_recent_events(
                            company_id=company_id,
                            session_id=None,
                            limit=10,
                        )

                    memory_events_block = build_memory_block(recent_events) or ""

                    facts = await self.repo.fetch_facts(company_id=company_id, limit=25)
                    memory_facts_block = _build_facts_block(facts) or ""

                    print("[MEMORY] events_fetched =", len(recent_events))
                    print("[MEMORY] facts_fetched  =", len(facts))

                except Exception as e:
                    print(f"[MEMORY BLOCK WARNING] {e}")
                    memory_events_block = ""
                    memory_facts_block = ""

            # 3) Build messages
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": AIMX_SYSTEM_PROMPT},
                {"role": "system", "content": AIMX_DECISION_PROMPT},
            ]

            if memory_facts_block:
                messages.append({"role": "system", "content": memory_facts_block})

            if memory_events_block:
                messages.append({"role": "system", "content": memory_events_block})

            messages.append({"role": "system", "content": context_block})

            messages.extend(self.sessions[key])
            messages.append({"role": "user", "content": message})

            # 4) OpenAI call
            model_name = getattr(settings, "MODEL", "gpt-4o-mini")
            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            answer_text = resp.choices[0].message.content or "لم يتم توليد رد."
            parsed: Optional[Dict[str, Any]] = _safe_json_loads(answer_text)

            # 5) File log
            try:
                log_decision_event(
                    company_id=company_id,
                    session_id=session_id,
                    payload={"answer": answer_text, "parsed": parsed, "context": context},
                )
            except Exception as e:
                print(f"[FILE LOG WARNING] {e}")

            # 6) DB log events + facts extraction
            executive_summary = ""
            raw_decision: Dict[str, Any] = {}

            if isinstance(parsed, dict):
                executive_summary = parsed.get("executive_summary", "") or ""
                raw_decision = parsed.get("raw_decision", {}) or {}

            if self.repo is not None and isinstance(parsed, dict):
                try:
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

                await self._extract_and_upsert_facts(
                    company_id=company_id,
                    session_id=session_id,
                    user_message=message,
                    executive_summary=executive_summary,
                    raw_decision=raw_decision,
                )

            # 7) Update in-memory
            self.sessions[key].append({"role": "user", "content": message})
            self.sessions[key].append({"role": "assistant", "content": answer_text})
            if len(self.sessions[key]) > self.max_history * 2:
                self.sessions[key] = self.sessions[key][-self.max_history * 2 :]

            # 8) Return
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