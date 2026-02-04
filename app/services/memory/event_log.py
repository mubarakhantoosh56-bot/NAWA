from typing import Dict, Any
from datetime import datetime

def log_decision_event(company_id: str, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # مؤقتاً نخليه يطبع فقط (بعدها نربطه DB)
    event = {
        "company_id": company_id,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }
    print("[EVENT_LOG]", event)
    return event