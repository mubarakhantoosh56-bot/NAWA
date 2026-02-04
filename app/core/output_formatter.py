from typing import Dict, Any, List

def _bullet(lines: List[str]) -> str:
    return "\n".join([f"- {x}" for x in lines if x])

def format_executive_output(result: Dict[str, Any], context: Dict[str, Any]) -> str:
    ctx = []
    if context:
        ctx.append(f"Stage: {context.get('stage','')}")
        ctx.append(f"Size: {context.get('size','')}")
        ctx.append(f"Industry: {context.get('industry','')}")
        ctx.append(f"Resources: {context.get('resources','')}")
    ctx_text = " | ".join([c for c in ctx if c and ":" in c])

    problem = result.get("problem_classification", {})
    truth = result.get("truth_validation", {})
    root = result.get("root_cause_engine", {})
    sol = result.get("solution_generator", {})
    acc = result.get("accountability", {})

    problem_line = f"{problem.get('type','')}".strip()
    confidence = problem.get("confidence", "")
    why = problem.get("why", "")

    contradictions = truth.get("contradictions", []) or []
    trust_score = truth.get("trust_score", "")
    truth_notes = truth.get("notes", "")

    root_causes = root.get("root_causes", []) or []
    why_chain = root.get("why_chain", []) or []

    urgent = sol.get("urgent_0_30_days", []) or []
    tactical = sol.get("tactical_1_3_months", []) or []
    strategic = sol.get("strategic_3_12_months", []) or []
    tradeoffs = sol.get("tradeoffs", []) or []

    responsible = acc.get("responsible_party", "")
    statement = acc.get("accountability_statement", "")

    text = []
    text.append("🧠 AIMX — Executive Decision Brief")
    if ctx_text:
        text.append(f"📌 Context: {ctx_text}")

    text.append("")
    text.append(f"1) التشخيص: {problem_line} (Confidence: {confidence}%)")
    if why:
        text.append(f"   - السبب الظاهر: {why}")

    text.append("")
    text.append(f"2) اختبار الصدق: Trust Score = {trust_score}")
    if contradictions:
        text.append("   - تناقضات:")
        text.append(_bullet(contradictions))
    if truth_notes:
        text.append(f"   - ملاحظات: {truth_notes}")

    text.append("")
    text.append("3) السبب الجذري (Root Cause):")
    if root_causes:
        text.append(_bullet(root_causes))
    if why_chain:
        text.append("   - Why Chain:")
        text.append(_bullet(why_chain))

    text.append("")
    text.append("4) الحلول المقترحة:")
    if urgent:
        text.append("   ✅ عاجل (0-30 يوم):")
        text.append(_bullet(urgent))
    if tactical:
        text.append("   ✅ تكتيكي (1-3 أشهر):")
        text.append(_bullet(tactical))
    if strategic:
        text.append("   ✅ استراتيجي (3-12 شهر):")
        text.append(_bullet(strategic))
    if tradeoffs:
        text.append("   ⚖️ Trade-offs:")
        text.append(_bullet(tradeoffs))

    text.append("")
    text.append("5) المساءلة:")
    if responsible:
        text.append(f"   - الطرف المسؤول: {responsible}")
    if statement:
        text.append(f"   - بيان: {statement}")

    return "\n".join(text)