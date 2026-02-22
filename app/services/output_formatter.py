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
    memory_injected: bool = False,
    events_count: int = 0,
) -> Dict[str, Any]:
    """
    Stable Output Contract (Investor-Ready)

    Always returns:
    - ceo_text: string
    - logic_json: object (never null)
    - followup_question
    - meta: stable metadata block
    """

    context = context or {}

    parse_ok = True
    data = parsed or _safe_json_parse(answer_text)

    # -------------------------
    # Fallback if model broke schema
    # -------------------------
    if not (
        isinstance(data, dict)
        and "executive_summary" in data
        and "raw_decision" in data
    ):
        parse_ok = False
        ceo_text = answer_text.strip()
        logic_json = {}
    else:
        ceo_text = data.get("executive_summary") or ""
        logic_json = data.get("raw_decision") or {}

    # -------------------------
    # Protection: prevent JSON injection inside ceo_text
    # -------------------------
    stripped = ceo_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        ceo_text = "تم توليد تحليل منظم. راجع logic_json."

    # -------------------------
    # Final Stable Contract
    # -------------------------
    return {
        "ceo_text": ceo_text,
        "logic_json": logic_json if isinstance(logic_json, dict) else {},
        "followup_question": followup_question,
        "meta": {
            "company_id": company_id,
            "session_id": session_id,
            "context": context,
            "parse_ok": parse_ok,
            "memory_injected": memory_injected,
            "events_count": events_count,
        },
    }