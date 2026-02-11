from typing import Any, Dict, List, Optional
import json


class MemoryRepository:
    def __init__(self, db):
        self.db = db  # asyncpg pool

    async def insert_event(self, event: Dict[str, Any]) -> None:
        query = """
        INSERT INTO memory_events
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
        limit: int = 10
    ) -> List[Dict[str, Any]]:

        if session_id:
            query = """
            SELECT created_at, event_type, user_message, executive_summary, logic_json
            FROM memory_events
            WHERE company_id=$1 AND session_id=$2
            ORDER BY created_at DESC
            LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, company_id, session_id, limit)
        else:
            query = """
            SELECT created_at, event_type, user_message, executive_summary, logic_json
            FROM memory_events
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