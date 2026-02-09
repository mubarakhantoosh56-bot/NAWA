import json
from typing import Any, Dict, Optional

def format_ai_response(
    answer_text: str,
    context: Dict[str, Any],
    session_id: str,
    company_id: str,
    followup_question: Optional[str] = None,
    language: str = "auto",
) -> Dict[str, Any]:

    def envelope(ceo_text: str, logic_json: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ceo_text": ceo_text or "",
            "logic_json": logic_json or {},
            "followup_question": followup_question,
            "meta": {
                "company_id": company_id,
                "session_id": session_id,
                "language": language,
                "context": context or {},
            }
        }

    fallback_logic = {
        "context_lock": {
            "missing_fields": [],
            "is_locked": True,
            "confidence": 0,
            "why": "Model output could not be parsed as valid JSON",
        }
    }
    fallback = envelope(
        ceo_text="⚠️ لم يتم توليد ملخص تنفيذي واضح بسبب خلل في التنسيق.",
        logic_json=fallback_logic
    )

    if not answer_text:
        return fallback

    try:
        parsed = json.loads(answer_text)

        # Case A: already ceo_text + logic_json
        if isinstance(parsed, dict) and "ceo_text" in parsed and "logic_json" in parsed:
            return envelope(
                ceo_text=parsed.get("ceo_text", ""),
                logic_json=parsed.get("logic_json") or {}
            )

        # Case B: old contract executive_summary + raw_decision
        if isinstance(parsed, dict) and "executive_summary" in parsed and "raw_decision" in parsed:
            return envelope(
                ceo_text=parsed.get("executive_summary", ""),
                logic_json=parsed.get("raw_decision") or {}
            )

        return fallback

    except Exception:
        return fallback