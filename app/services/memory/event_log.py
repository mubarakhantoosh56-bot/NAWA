from datetime import datetime
import hashlib
import json
import logging
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)
logger.debug("Event log module loaded", extra={"module_path": __file__})

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
        logger.warning(
            "File decision log write failed",
            extra={"company_id": company_id, "session_id": session_id},
            exc_info=True,
        )


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
        logger.info(
            "Inserting decision event",
            extra={"company_id": company_id, "session_id": session_id},
        )
        await repo.insert_event(event)
        logger.info(
            "Decision event inserted or skipped by idempotency",
            extra={"company_id": company_id, "session_id": session_id},
        )


    except Exception as e:
        logger.error(
            "Database decision log failed",
            extra={"company_id": company_id, "session_id": session_id},
            exc_info=True,
        )
