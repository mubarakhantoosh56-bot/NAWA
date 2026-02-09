from typing import Any, Dict, List

def build_memory_block(events: List[Dict[str, Any]]) -> str:
    if not events:
        return "INSTITUTIONAL MEMORY (RECENT EVENTS): none"

    lines = ["INSTITUTIONAL MEMORY (RECENT EVENTS):"]
    # الأحداث جايه DESC، نخليها بالعكس حتى تقرأ تسلسل
    for e in reversed(events):
        ts = str(e.get("created_at", ""))[:19]
        et = e.get("event_type", "UNKNOWN")
        msg = (e.get("user_message") or "").strip()
        summ = (e.get("executive_summary") or "").strip()

        # نختصر حتى لا ينفخ التوكنز
        if len(msg) > 160:
            msg = msg[:160] + "..."
        if len(summ) > 220:
            summ = summ[:220] + "..."

        lines.append(f"- [{ts}] {et} | user: {msg} | summary: {summ}")

    lines.append("RULES: Use this memory for continuity. Do NOT repeat it in your output.")
    return "\n".join(lines)