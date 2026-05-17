import json
from typing import Any, Dict, Optional

ARABIC_HEADINGS = {
    "Executive Summary": "الملخص التنفيذي",
    "Key Insights": "أبرز الملاحظات",
    "Risks": "المخاطر",
    "Recommended Actions": "الإجراءات الموصى بها",
    "Priority Level": "مستوى الأولوية",
}

ENGLISH_HEADINGS = {value: key for key, value in ARABIC_HEADINGS.items()}


def _is_arabic(language: str) -> bool:
    return (language or "").strip().lower() in {"ar", "arabic", "العربية"}


def _normalize_section_headings(text: str, language: str) -> str:
    replacements = ARABIC_HEADINGS if _is_arabic(language) else ENGLISH_HEADINGS
    normalized = str(text or "")
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


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
        ceo_text=(
            "لم يتم توليد ملخص تنفيذي واضح بسبب خلل في التنسيق."
            if _is_arabic(language)
            else "A clear executive summary was not generated because the response format was invalid."
        ),
        logic_json=fallback_logic
    )

    if not answer_text:
        return fallback

    try:
        parsed = json.loads(answer_text)

        # Case A: already ceo_text + logic_json
        if isinstance(parsed, dict) and "ceo_text" in parsed and "logic_json" in parsed:
            return envelope(
                ceo_text=_normalize_section_headings(parsed.get("ceo_text", ""), language),
                logic_json=parsed.get("logic_json") or {}
            )

        # Case B: old contract executive_summary + raw_decision
        if isinstance(parsed, dict) and "executive_summary" in parsed and "raw_decision" in parsed:
            return envelope(
                ceo_text=_normalize_section_headings(parsed.get("executive_summary", ""), language),
                logic_json=parsed.get("raw_decision") or {}
            )

        return fallback

    except Exception:
        return fallback
