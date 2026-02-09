from typing import Dict, Any, Optional
import json


def _safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """Try parse JSON from a string; return None if fails."""
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
    Output Contract:
    - ceo_text: string (human-readable, no JSON)
    - logic_json: object | null (structured decision)
    - meta: includes company_id, session_id, context
    - followup_question: optional (OFF حاليا)
    """

    context = context or {}

    # 1) Prefer parsed passed from openai_client; otherwise try parse from answer_text
    data = parsed or _safe_json_parse(answer_text)

    # 2) If model returned strict decision JSON:
    # expected keys: executive_summary (string) + raw_decision (object)
    if isinstance(data, dict) and "executive_summary" in data and "raw_decision" in data:
        ceo_text = data.get("executive_summary") or ""
        logic_json = data.get("raw_decision") or {}
    else:
        # fallback: treat whole output as CEO text
        ceo_text = answer_text or ""
        logic_json = None

    # 3) Make sure CEO text never includes JSON blob by accident
    # (basic safety: if it starts like JSON, strip and keep short message)
    stripped = ceo_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        ceo_text = "تم توليد تحليل منظم، لكن عرض الـ CEO يحتاج تنسيق. (راجع logic_json)."

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