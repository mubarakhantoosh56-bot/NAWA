from typing import Dict, Any, Optional
import json


ARABIC_HEADINGS = {
    "Executive Summary": "الملخص التنفيذي",
    "Key Insights": "أبرز الملاحظات",
    "Risks": "المخاطر",
    "Recommended Actions": "الإجراءات الموصى بها",
    "Priority Level": "مستوى الأولوية",
}

ENGLISH_HEADINGS = {value: key for key, value in ARABIC_HEADINGS.items()}


def _safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _is_arabic(language: str) -> bool:
    return (language or "").strip().lower() in {"ar", "arabic", "العربية"}


def _normalize_section_headings(text: str, language: str) -> str:
    replacements = ARABIC_HEADINGS if _is_arabic(language) else ENGLISH_HEADINGS
    normalized = text or ""
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def _json_injection_fallback(language: str) -> str:
    if _is_arabic(language):
        return "تم توليد تحليل منظم. راجع logic_json."
    return "Structured analysis generated. Review logic_json."


def format_ai_response(
    answer_text: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    company_id: Optional[str] = None,
    followup_question: Optional[str] = None,
    parsed: Optional[Dict[str, Any]] = None,
    memory_injected: bool = False,
    events_count: int = 0,
    language: str = "en",
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

    ceo_text = _normalize_section_headings(str(ceo_text), language)

    # -------------------------
    # Protection: prevent JSON injection inside ceo_text
    # -------------------------
    stripped = ceo_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        ceo_text = _json_injection_fallback(language)

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
            "language": "ar" if _is_arabic(language) else "en",
            "parse_ok": parse_ok,
            "memory_injected": memory_injected,
            "events_count": events_count,
        },
    }
