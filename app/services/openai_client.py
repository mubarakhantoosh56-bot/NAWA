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
You are a STRICT institutional memory extraction engine.

Your job is to extract ALL durable company facts from the input.

You MUST extract facts whenever possible. Do NOT skip obvious facts.

Return ONLY valid JSON.

Schema:
{
  "facts": [
    {
      "fact_type": "company|product|process|goal|constraint|metric|risk|decision|other",
      "fact_key": "normalized_key",
      "fact_value": "plain text",
      "confidence": 0
    }
  ]
}

STRICT RULES:

1. ALWAYS extract:
   - timelines (e.g., "3 months" → launch_timeline)
   - markets (e.g., "Iraq" → target_market)
   - goals (e.g., "we want to launch" → goal)

2. Normalize keys EXACTLY as:
   - launch timeline → "launch_timeline"
   - market → "target_market"
   - goal → "goal"
   - revenue → "revenue"
   - product name → "product_name"

3. Never skip facts unless input is completely meaningless.

4. Confidence:
   - clear explicit fact → 90-100
   - inferred → 60-80

5. If multiple facts exist → extract ALL of them.

6. NEVER return empty unless truly no facts.

Example:
Input:
"we want to launch in Iraq within 3 months"

Output:
{
  "facts": [
    {"fact_type": "goal", "fact_key": "goal", "fact_value": "launch product", "confidence": 90},
    {"fact_type": "goal", "fact_key": "launch_timeline", "fact_value": "3 months", "confidence": 95},
    {"fact_type": "other", "fact_key": "target_market", "fact_value": "Iraq", "confidence": 95}
  ]
}
"""

# -----------------------------
# Fact Key Normalization
# -----------------------------
FACT_KEY_NORMALIZATION = {
    # revenue
    "revenue": "revenue",
    "monthly_revenue": "revenue",
    "target_revenue": "revenue",
    "sales_target": "revenue",
    "current_revenue": "revenue",
    "initial_revenue": "revenue",
    "mvp_revenue": "revenue",
    "projected_revenue": "revenue",

    # team size
    "team_size": "team_size",
    "employees": "team_size",
    "employee_count": "team_size",
    "team": "team_size",
    "staff_count": "team_size",
    "current_team_size": "team_size",

    # stage
    "company_stage": "stage",
    "business_stage": "stage",
    "mvp_stage": "stage",
    "current_stage": "stage",
    "stage": "stage",
    "mvp_current_stage": "stage",
    "startup_stage": "stage",

    # goal
    "goal": "goal",
    "objective": "goal",
    "business_goal": "goal",
    "mvp_goal": "goal",
    "mvp_objective": "goal",
    "initial_goal": "goal",
    "project_goal": "goal",

    # target market
    "target_market": "target_market",
    "market": "target_market",
    "market_focus": "target_market",
    "mvp_target_market": "target_market",
    "initial_target_market": "target_market",
    "primary_market": "target_market",
    "main_market": "target_market",

    # product/platform name
    "product_name": "product_name",
    "system_name": "product_name",
    "platform_name": "product_name",
    "project_name": "product_name",
    "company_name": "product_name",
    "solution_name": "product_name",

    # timeline
    "launch_timeline": "launch_timeline",
    "launch_timeframe": "launch_timeline",
    "timeline": "launch_timeline",
    "mvp_timeline": "launch_timeline",
    "mvp_launch_timeline": "launch_timeline",
    "mvp_launch_timeline_months": "launch_timeline",
    "initial_timeline": "launch_timeline",
}


def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        return None


def normalize_fact_key(key: str) -> str:
    key = (key or "").strip().lower()
    return FACT_KEY_NORMALIZATION.get(key, key)


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


def _build_company_profile_block(profile: Dict[str, Any]) -> str:
    if not profile:
        return "COMPANY PROFILE: none"

    lines = ["COMPANY PROFILE:"]
    for key, value in profile.items():
        if value:
            lines.append(f"- {key}: {value}")

    if len(lines) == 1:
        return "COMPANY PROFILE: none"

    lines.append("RULES: This is the stable company profile. Use it as the main reference when answering.")
    return "\n".join(lines)


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

            print("🔥 EXTRACTED FACTS:", facts)

            if not isinstance(facts, list) or not facts:
                print("[FACTS] no facts extracted")
                return

            normalized_count = 0

            for f in facts[:25]:
                if not isinstance(f, dict):
                    continue

                fact_type = (f.get("fact_type") or "other").strip().lower()
                raw_key = (f.get("fact_key") or "").strip()
                fact_key = normalize_fact_key(raw_key)
                fact_value = (f.get("fact_value") or "").strip()
                confidence = int(f.get("confidence") or 0)

                if not fact_value:
                    continue

                if not fact_key:
                    fact_key = "general_fact"

                if confidence < 0:
                    confidence = 0
                if confidence > 100:
                    confidence = 100

                await self.repo.upsert_fact(
                    company_id=company_id,
                    session_id=session_id,
                    fact_type=fact_type,
                    fact_key=fact_key,
                    fact_value=fact_value,
                    confidence=confidence,
                    source_event_id=None,
                )
                normalized_count += 1

            print(f"[FACTS] upserted = {normalized_count}")

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
            context_block = (
                "COMPANY CONTEXT:\n"
                f"Stage: {context.get('stage', 'N/A')}\n"
                f"Size: {context.get('size', 'N/A')}\n"
                f"Industry: {context.get('industry', 'N/A')}\n"
                f"Resources: {context.get('resources', 'N/A')}\n"
            )

            memory_events_block = ""
            memory_facts_block = ""
            company_profile_block = ""

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

                    profile = await self.repo.build_company_profile(company_id=company_id)
                    company_profile_block = _build_company_profile_block(profile) or ""

                    print("[MEMORY] events_fetched =", len(recent_events))
                    print("[MEMORY] facts_fetched  =", len(facts))

                except Exception as e:
                    print(f"[MEMORY BLOCK WARNING] {e}")
                    memory_events_block = ""
                    memory_facts_block = ""
                    company_profile_block = ""

            messages: List[Dict[str, str]] = [
                {"role": "system", "content": AIMX_SYSTEM_PROMPT},
                {"role": "system", "content": AIMX_DECISION_PROMPT},
            ]

            if company_profile_block:
                messages.append({"role": "system", "content": company_profile_block})

            if memory_facts_block:
                messages.append({"role": "system", "content": memory_facts_block})

            if memory_events_block:
                messages.append({"role": "system", "content": memory_events_block})

            messages.append({"role": "system", "content": context_block})

            messages.extend(self.sessions[key])
            messages.append({"role": "user", "content": message})

            model_name = getattr(settings, "MODEL", "gpt-4o-mini")
            resp = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            answer_text = resp.choices[0].message.content or "لم يتم توليد رد."
            parsed: Optional[Dict[str, Any]] = _safe_json_loads(answer_text)

            try:
                log_decision_event(
                    company_id=company_id,
                    session_id=session_id,
                    payload={"answer": answer_text, "parsed": parsed, "context": context},
                )
            except Exception as e:
                print(f"[FILE LOG WARNING] {e}")

            executive_summary = ""
            raw_decision: Dict[str, Any] = {}

            if isinstance(parsed, dict):
                executive_summary = parsed.get("executive_summary", "") or ""
                raw_decision = parsed.get("raw_decision", {}) or {}

            if self.repo is not None:
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

            self.sessions[key].append({"role": "user", "content": message})
            self.sessions[key].append({"role": "assistant", "content": answer_text})

            if len(self.sessions[key]) > self.max_history * 2:
                self.sessions[key] = self.sessions[key][-self.max_history * 2 :]

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