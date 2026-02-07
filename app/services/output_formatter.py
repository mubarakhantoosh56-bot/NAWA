from typing import Any, Dict, Optional

def format_ai_response(
    answer_text: str,
    context: Dict[str, Any],
    session_id: str,
    company_id: str,
    followup_question: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Output Formatter (MVP):
    - executive_summary: نص جاهز للـ CEO
    - raw_decision: JSON منظم للمطورين/الواجهة
    - followup: سؤال متابعة (اختياري)
    """

    return {
        "executive_summary": answer_text,
        "raw_decision": {
            "full_text": answer_text,
            "context": context,
            "session_id": session_id,
            "company_id": company_id,
        },
        "followup": {
            "enabled": bool(followup_question),
            "question": followup_question,
        },
    }