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
    async def get_fact_by_key(
        self,
        company_id: str,
        fact_key: str,
    ) -> Optional[Dict[str, Any]]:
        query = """
        SELECT fact_type, fact_key, fact_value, confidence, updated_at
        FROM public.memory_facts
        WHERE company_id=$1 AND fact_key=$2
        LIMIT 1
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, company_id, fact_key)

        if not row:
            return None

        return {
            "fact_type": row["fact_type"],
            "fact_key": row["fact_key"],
            "fact_value": row["fact_value"],
            "confidence": row["confidence"],
            "updated_at": row["updated_at"],
        }

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
        Confidence Evolution + Conflict Detection v1

        Rules:
        - If same fact_key and same fact_value:
            raise confidence slightly
        - If same fact_key but different fact_value:
            print conflict warning
            if new confidence >= existing confidence:
                replace value
            else:
                keep old value
        """
        fact_type = (fact_type or "other").strip().lower()
        fact_key = (fact_key or "").strip()
        fact_value = (fact_value or "").strip()

        if not fact_key or not fact_value:
            return

        conf = int(confidence or 0)
        if conf < 0:
            conf = 0
        if conf > 100:
            conf = 100

        existing = await self.get_fact_by_key(company_id=company_id, fact_key=fact_key)

        if existing:
            existing_value = (existing.get("fact_value") or "").strip()
            existing_conf = int(existing.get("confidence") or 0)

            # 1) نفس القيمة → نرفع الثقة
            if existing_value.lower() == fact_value.lower():
                new_conf = min(100, max(existing_conf, conf) + 5)

                query = """
                UPDATE public.memory_facts
                SET
                  session_id = $3,
                  fact_type = $4,
                  confidence = $5,
                  source_event_id = $6,
                  updated_at = NOW()
                WHERE company_id = $1 AND fact_key = $2
                """
                async with self.db.acquire() as conn:
                    await conn.execute(
                        query,
                        company_id,
                        fact_key,
                        session_id,
                        fact_type,
                        new_conf,
                        source_event_id,
                    )

                print(f"[FACTS] confidence increased for '{fact_key}' -> {new_conf}")
                return

            # 2) قيمة مختلفة → conflict
            print(
                f"[FACT CONFLICT] company={company_id} key={fact_key} | "
                f"old='{existing_value}' ({existing_conf}) vs new='{fact_value}' ({conf})"
            )

            # إذا الجديد أقوى أو يساوي القديم → نحدث
            if conf >= existing_conf:
                query = """
                UPDATE public.memory_facts
                SET
                  session_id = $3,
                  fact_type = $4,
                  fact_value = $5,
                  confidence = $6,
                  source_event_id = $7,
                  updated_at = NOW()
                WHERE company_id = $1 AND fact_key = $2
                """
                async with self.db.acquire() as conn:
                    await conn.execute(
                        query,
                        company_id,
                        fact_key,
                        session_id,
                        fact_type,
                        fact_value,
                        conf,
                        source_event_id,
                    )

                print(f"[FACTS] conflict resolved by replacing '{fact_key}' with higher-confidence value")
                return

            # إذا القديم أقوى → نبقي القديم
            print(f"[FACTS] kept existing value for '{fact_key}' because existing confidence is higher")
            return

        # 3) إذا ماكو existing fact → insert جديد
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
          confidence = GREATEST(public.memory_facts.confidence, EXCLUDED.confidence),
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

    async def build_company_profile(self, company_id: str) -> Dict[str, Any]:
        facts = await self.fetch_facts(company_id=company_id, limit=100)

        profile = {
            "product_name": None,
            "product_type": None,
            "target_market": None,
            "stage": None,
            "goal": None,
            "launch_timeline": None,
            "revenue": None,
            "team_size": None,
        }

        for f in facts:
            key = (f.get("fact_key") or "").strip()
            value = (f.get("fact_value") or "").strip()

            if key in profile and value:
                if profile[key] is None:
                    profile[key] = value

        return profile