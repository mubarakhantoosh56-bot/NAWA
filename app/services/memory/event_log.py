import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log_path(company_id: str, session_id: str) -> Path:
    safe_company = company_id.replace("/", "_")
    safe_session = session_id.replace("/", "_")
    return LOG_DIR / f"{safe_company}__{safe_session}.jsonl"


def log_decision_event(company_id: str, session_id: str, payload: Dict[str, Any]) -> None:
    path = _log_path(company_id, session_id)
    event = {
        "ts": datetime.utcnow().isoformat(),
        "type": "decision",
        "company_id": company_id,
        "session_id": session_id,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


#def get_last_decision_event(company_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    path = _log_path(company_id, session_id)
    if not path.exists():
        return None

    last_line = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last_line = line

    if not last_line:
        return None

    try:
        return json.loads(last_line)
    except Exception:
        return None