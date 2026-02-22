from typing import Any, Dict, List

def build_memory_block(events: List[Dict[str, Any]]) -> str:
    """
    Builds a strong, model-friendly memory injection block.

    Goals:
    - Make memory "hard facts" the model must use if relevant.
    - Keep it compact to avoid token bloat.
    - Avoid forcing the model to output memory verbatim.
    - Provide a clear structure: facts + summaries.
    """

    if not events:
        return (
            "INSTITUTIONAL MEMORY (HARD FACTS):\n"
            "- none\n"
            "RULES:\n"
            "1) If the user refers to past decisions or context, you MUST rely on this memory if relevant.\n"
            "2) Do NOT quote this memory verbatim in your output.\n"
        )

    header = (
        "INSTITUTIONAL MEMORY (HARD FACTS — MUST USE IF RELEVANT)\n"
        "The following are prior verified events for continuity.\n"
        "If the current user request relates to these items, you MUST use them in reasoning.\n"
        "Do NOT repeat this memory verbatim in your output.\n"
    )

    # ✅ We want chronological readability (old -> new)
    # events usually come DESC from DB
    ordered = list(reversed(events))

    lines: List[str] = [header, "MEMORY FACTS:"]
    for i, e in enumerate(ordered, start=1):
        ts = str(e.get("created_at", ""))[:19]
        et = (e.get("event_type") or "UNKNOWN").strip()
        msg = (e.get("user_message") or "").strip()
        summ = (e.get("executive_summary") or "").strip()

        # ✅ Aggressive trimming to reduce tokens
        if len(msg) > 120:
            msg = msg[:120] + "..."
        if len(summ) > 180:
            summ = summ[:180] + "..."

        # ✅ Build a clean “fact line”
        # Keep consistent separators so the model can scan quickly
        lines.append(f"{i}. [{ts}] ({et}) USER: {msg} | SUMMARY: {summ}")

    # ✅ Final hard rules (short + strong)
    lines.append("")
    lines.append("RULES:")
    lines.append("1) Use MEMORY FACTS for continuity when relevant.")
    lines.append("2) If memory conflicts with the user’s new info, flag it in truth_validation.contradictions.")
    lines.append("3) Never output memory lines verbatim; only use them internally to answer.")
    lines.append("4) If memory is not relevant, ignore it.")

    return "\n".join(lines)