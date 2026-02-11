from typing import Dict, Any, Optional
import json


def _safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None


def format_ai_response(
    answer_text: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    company_id: Optional[str] = None,
    followup_question: Optional[str] = None,
    parsed: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Output Contract (API):
    - ceo_text: string
    - logic_json: object (raw_decision)
    - meta: company_id, session_id, context
    - followup_question: optional
    """

    context = context or {}
    data = parsed or _safe_json_parse(answer_text)

    # ✅ enforce strict schema
    if not (isinstance(data, dict) and "executive_summary" in data and "raw_decision" in data):
        raise ValueError("Model did NOT respect strict decision schema (executive_summary/raw_decision).")

    ceo_text = data.get("executive_summary") or ""
    logic_json = data.get("raw_decision") or {}

    # حماية بسيطة: لا نخلي ceo_text يصير JSON بالغلط
    stripped = ceo_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        ceo_text = "تم توليد تحليل منظم. راجع logic_json."

    return {
        "ceo_text": ceo_text,
        "logic_json": logic_json,
        "followup_question": followup_question,
        "meta": {
            "company_id": company_id,
            "session_id": session_id,
            "context": context,
        },
    }