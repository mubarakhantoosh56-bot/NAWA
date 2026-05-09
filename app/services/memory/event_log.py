from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import hashlib
import traceback

print("[event_log.py loaded from]", __file__)

def _safe_json(obj: Any) -> Any:
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def _make_idempotency_key(
    company_id: str,
    session_id: str,
    user_message: str,
    executive_summary: str,
) -> str:
    raw = f"{company_id}|{session_id}|{user_message}|{executive_summary}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ✅ القديم: File-based log (optional)
def log_decision_event(company_id: str, session_id: str, payload: Dict[str, Any]) -> None:
    try:
        os.makedirs("logs", exist_ok=True)
        path = os.path.join("logs", "decision_events.jsonl")
        record = {
            "ts": datetime.utcnow().isoformat(),
            "company_id": company_id,
            "session_id": session_id,
            "payload": payload,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[FILE LOG ERROR] {e}")


# ✅ الجديد: DB log (Institutional Memory)
async def log_decision_event_db(
    repo,
    company_id: str,
    session_id: str,
    user_message: str,
    executive_summary: str,
    logic_json: Dict[str, Any],
    context: Dict[str, Any],
    tags: Optional[List[str]] = None,
) -> None:
    try:
        event = {
            "company_id": company_id,
            "session_id": session_id,
            "event_type": "decision",
            "user_message": user_message,
            "executive_summary": executive_summary,
            "logic_json": _safe_json(logic_json),
            "context": _safe_json(context),
            "tags": tags or [],
            "idempotency_key": _make_idempotency_key(
                company_id=company_id,
                session_id=session_id,
                user_message=user_message,
                executive_summary=executive_summary,
            ),
        }
        print("[DB LOG] inserting event for", company_id, session_id)
        await repo.insert_event(event)
        print("[DB LOG] inserted (or skipped by idempotency)")


    except Exception as e:
        print(f"[DB LOG ERROR] {e}")
        traceback.print_exc()