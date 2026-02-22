from typing import Any, Dict, List, Optional
import json


class MemoryRepository:
    def __init__(self, db):
        # asyncpg pool
        self.db = db

    # -------------------------
    # Events (memory_events)
    # -------------------------
    async def insert_event(self, event: Dict[str, Any]) -> None:
        query = """
        INSERT INTO public.memory_events
        (company_id, session_id, event_type, user_message, executive_summary, logic_json, context, tags, idempotency_key)
        VALUES
        ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::text[],$9)
        ON CONFLICT (idempotency_key) DO NOTHING
        """
        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                event.get("company_id"),
                event.get("session_id"),
                event.get("event_type"),
                event.get("user_message"),
                event.get("executive_summary"),
                json.dumps(event.get("logic_json", {}), ensure_ascii=False),
                json.dumps(event.get("context", {}), ensure_ascii=False),
                event.get("tags") or [],
                event.get("idempotency_key"),
            )

    async def fetch_recent_events(
        self,
        company_id: str,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if session_id:
            query = """
            SELECT created_at, event_type, user_message, executive_summary, logic_json
            FROM public.memory_events
            WHERE company_id=$1 AND session_id=$2
            ORDER BY created_at DESC
            LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, session_id, limit)
        else:
            query = """
            SELECT created_at, event_type, user_message, executive_summary, logic_json
            FROM public.memory_events
            WHERE company_id=$1
            ORDER BY created_at DESC
            LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, limit)

        return [
            {
                "created_at": r["created_at"],
                "event_type": r["event_type"],
                "user_message": r["user_message"],
                "executive_summary": r["executive_summary"],
                "logic_json": r["logic_json"],
            }
            for r in rows
        ]

    # -------------------------
    # Facts (memory_facts)
    # -------------------------
    async def upsert_fact(
        self,
        company_id: str,
        session_id: Optional[str],
        fact_type: str,
        fact_key: str,
        fact_value: str,
        confidence: int = 0,
        source_event_id: Optional[str] = None,
    ) -> None:
        """
        Uses the constraint name directly to avoid ON CONFLICT mismatch.
        Requires UNIQUE constraint:
          memory_facts_company_key_unique (company_id, fact_key)
        """
        # تنظيف بسيط حتى ما ننخزن garbage
        fact_type = (fact_type or "other").strip()
        fact_key = (fact_key or "").strip()
        fact_value = (fact_value or "").strip()

        if not fact_key or not fact_value:
            return

        conf = int(confidence or 0)
        if conf < 0:
            conf = 0
        if conf > 100:
            conf = 100

        query = """
        INSERT INTO public.memory_facts
        (company_id, session_id, fact_type, fact_key, fact_value, confidence, source_event_id)
        VALUES
        ($1,$2,$3,$4,$5,$6,$7)
        ON CONFLICT ON CONSTRAINT memory_facts_company_key_unique
        DO UPDATE SET
          session_id = EXCLUDED.session_id,
          fact_type = EXCLUDED.fact_type,
          fact_value = EXCLUDED.fact_value,
          confidence = EXCLUDED.confidence,
          source_event_id = EXCLUDED.source_event_id,
          updated_at = NOW()
        """
        async with self.db.acquire() as conn:
            await conn.execute(
                query,
                company_id,
                session_id,
                fact_type,
                fact_key,
                fact_value,
                conf,
                source_event_id,
            )

    async def fetch_facts(self, company_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        query = """
        SELECT fact_type, fact_key, fact_value, confidence, updated_at
        FROM public.memory_facts
        WHERE company_id=$1
        ORDER BY updated_at DESC
        LIMIT $2
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, company_id, limit)

        return [
            {
                "fact_type": r["fact_type"],
                "fact_key": r["fact_key"],
                "fact_value": r["fact_value"],
                "confidence": r["confidence"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]