"""Rule-based operational pattern detection for the NAWA FMCG MVP."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatternFinding:
    finding_type: str
    department: str
    related_departments: list[str]
    evidence: list[str]
    severity: str
    confidence: int
    suggested_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "department": self.department,
            "related_departments": self.related_departments,
            "evidence": self.evidence[:3],
            "severity": self.severity,
            "confidence": self.confidence,
            "suggested_action": self.suggested_action,
        }


RELATED_DEPARTMENTS = {
    "production": ["warehouse", "operations", "sales", "finance"],
    "sales": ["warehouse", "operations", "finance", "production"],
    "finance": ["sales", "production", "warehouse", "operations"],
    "marketing": ["sales", "production", "warehouse", "finance"],
    "operations": ["production", "warehouse", "sales", "finance"],
    "warehouse": ["production", "sales", "operations", "finance"],
    "company": ["production", "sales", "finance", "marketing", "operations"],
}

SIGNALS = {
    "delay": {
        "type": "bottleneck",
        "severity": "high",
        "keywords": (
            "waiting",
            "pending",
            "not ready",
            "not received",
            "missed window",
            "behind schedule",
            "late",
            "backlog",
            "blocked",
            "hold",
            "stuck",
            "no dispatch",
            "لم يصل",
            "متأخر",
            "انتظار",
            "معلق",
        ),
        "action": "Confirm owner, unblock the handoff, and reset the delivery or execution commitment today.",
    },
    "mistake": {
        "type": "issue",
        "severity": "medium",
        "keywords": (
            "wrong",
            "mistake",
            "error",
            "mismatch",
            "incorrect",
            "rework",
            "return",
            "complaint",
            "خطأ",
            "غير صحيح",
            "مرتجع",
            "شكوى",
        ),
        "action": "Run a same-day root-cause check and assign one corrective control before the next cycle.",
    },
    "weak_execution": {
        "type": "risk",
        "severity": "medium",
        "keywords": (
            "missed",
            "not completed",
            "failed",
            "low completion",
            "weak",
            "short",
            "gap",
            "unassigned",
            "unresolved",
            "لم يكتمل",
            "ضعيف",
            "فشل",
            "فجوة",
        ),
        "action": "Escalate the execution gap with a named owner, due date, and follow-up checkpoint.",
    },
    "positive": {
        "type": "positive",
        "severity": "low",
        "keywords": (
            "improved",
            "resolved",
            "completed",
            "ahead",
            "above target",
            "record",
            "strong",
            "stable",
            "recovered",
            "on time",
            "تحسن",
            "اكتمل",
            "ممتاز",
            "مستقر",
        ),
        "action": "Capture the practice behind the improvement and repeat it in the next operating cycle.",
    },
}


def detect_operational_patterns(
    events: list[dict[str, Any]],
    *,
    active_department: str = "ceo",
    max_findings: int = 8,
) -> list[dict[str, Any]]:
    """Detect operational risks, issues, positives, and patterns using MVP rules."""

    operational_events = [_normalize_event(event) for event in events if _is_operational_event(event)]
    if not operational_events:
        return []

    findings: list[PatternFinding] = []
    findings.extend(_signal_findings(operational_events))
    findings.extend(_repeated_category_findings(operational_events))
    findings.extend(_priority_findings(operational_events))
    findings.extend(_kpi_findings(operational_events))
    findings.extend(_missing_followup_findings(operational_events))

    scoped = _scope_findings(findings, active_department)
    deduped = _dedupe(scoped)
    deduped.sort(key=lambda finding: (_severity_rank(finding.severity), finding.confidence), reverse=True)
    return [finding.as_dict() for finding in deduped[:max_findings]]


def _signal_findings(events: list[dict[str, Any]]) -> list[PatternFinding]:
    findings: list[PatternFinding] = []
    grouped_evidence: dict[tuple[str, str], list[str]] = defaultdict(list)

    for event in events:
        text = event["text"].lower()
        for signal, config in SIGNALS.items():
            if any(keyword in text for keyword in config["keywords"]):
                grouped_evidence[(signal, event["department"])].append(event["summary"])

    for (signal, department), evidence in grouped_evidence.items():
        config = SIGNALS[signal]
        count = len(evidence)
        severity = "critical" if signal != "positive" and count >= 3 else str(config["severity"])
        confidence = min(92, 58 + count * 12)
        findings.append(
            PatternFinding(
                finding_type=str(config["type"]),
                department=department,
                related_departments=_related(department),
                evidence=evidence,
                severity=severity,
                confidence=confidence,
                suggested_action=str(config["action"]),
            )
        )
    return findings


def _repeated_category_findings(events: list[dict[str, Any]]) -> list[PatternFinding]:
    counts: Counter[tuple[str, str]] = Counter(
        (event["department"], event["category"])
        for event in events
        if event["category"] and event["category"] not in {"daily_update", "note"}
    )
    findings: list[PatternFinding] = []
    for (department, category), count in counts.items():
        if count < 2:
            continue
        evidence = [event["summary"] for event in events if event["department"] == department and event["category"] == category]
        finding_type = "bottleneck" if category in {"issue", "alert"} else "opportunity"
        findings.append(
            PatternFinding(
                finding_type=finding_type,
                department=department,
                related_departments=_related(department),
                evidence=evidence,
                severity="high" if category in {"issue", "alert"} else "medium",
                confidence=min(88, 55 + count * 11),
                suggested_action=f"Review repeated {category.replace('_', ' ')} events and assign one owner for closure.",
            )
        )
    return findings


def _priority_findings(events: list[dict[str, Any]]) -> list[PatternFinding]:
    high_events = [
        event
        for event in events
        if event["priority"] in {"high", "critical"}
    ]
    by_department: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in high_events:
        by_department[event["department"]].append(event)

    findings: list[PatternFinding] = []
    for department, items in by_department.items():
        if len(items) == 1 and items[0]["priority"] != "critical":
            continue
        findings.append(
            PatternFinding(
                finding_type="risk",
                department=department,
                related_departments=_related(department),
                evidence=[item["summary"] for item in items],
                severity="critical" if any(item["priority"] == "critical" for item in items) else "high",
                confidence=min(90, 62 + len(items) * 10),
                suggested_action="Escalate high-priority operational events into today's management review.",
            )
        )
    return findings


def _kpi_findings(events: list[dict[str, Any]]) -> list[PatternFinding]:
    findings: list[PatternFinding] = []
    for event in events:
        metrics_text = " ".join(f"{key} {value}" for key, value in event["metrics"].items()).lower()
        if not metrics_text:
            continue
        if any(token in metrics_text for token in ("down", "drop", "below", "-", "worse", "decrease", "low")):
            findings.append(
                PatternFinding(
                    finding_type="risk",
                    department=event["department"],
                    related_departments=_related(event["department"]),
                    evidence=[event["summary"]],
                    severity="medium",
                    confidence=64,
                    suggested_action="Check whether this KPI movement affects fulfillment, margin, cash, or customer commitments.",
                )
            )
        if any(token in metrics_text for token in ("up", "above", "improved", "+", "increase", "strong")):
            findings.append(
                PatternFinding(
                    finding_type="positive",
                    department=event["department"],
                    related_departments=_related(event["department"]),
                    evidence=[event["summary"]],
                    severity="low",
                    confidence=66,
                    suggested_action="Identify what changed operationally and preserve the improvement in the next cycle.",
                )
            )
    return findings


def _missing_followup_findings(events: list[dict[str, Any]]) -> list[PatternFinding]:
    findings: list[PatternFinding] = []
    for event in events:
        text = event["text"].lower()
        if any(token in text for token in ("needs follow-up", "follow up", "unresolved", "pending owner", "no owner", "without owner")):
            findings.append(
                PatternFinding(
                    finding_type="issue",
                    department=event["department"],
                    related_departments=_related(event["department"]),
                    evidence=[event["summary"]],
                    severity="medium",
                    confidence=72,
                    suggested_action="Assign a follow-up owner and deadline before the next operating review.",
                )
            )
    return findings


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    context = event.get("context") if isinstance(event.get("context"), dict) else {}
    logic = event.get("logic_json") if isinstance(event.get("logic_json"), dict) else {}
    payload = context.get("payload") if isinstance(context.get("payload"), dict) else {}
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    department = (
        str(context.get("target_department") or context.get("source_department") or "")
        or _department_from_event_type(str(event.get("event_type") or ""))
        or "company"
    )
    summary = str(event.get("executive_summary") or event.get("user_message") or "").strip()
    text = " ".join(
        str(part or "")
        for part in [
            summary,
            payload.get("text"),
            context.get("category"),
            context.get("priority"),
            logic.get("impact_hint"),
            " ".join(f"{key} {value}" for key, value in metrics.items()),
        ]
    )
    return {
        "department": department,
        "category": str(context.get("category") or "").strip().lower(),
        "priority": str(context.get("priority") or "").strip().lower(),
        "summary": summary[:260],
        "text": text,
        "metrics": metrics,
    }


def _is_operational_event(event: dict[str, Any]) -> bool:
    event_type = str(event.get("event_type") or "")
    return event_type.startswith("operational.")


def _department_from_event_type(event_type: str) -> str:
    parts = event_type.split(".")
    return parts[1] if len(parts) >= 3 else ""


def _related(department: str) -> list[str]:
    return RELATED_DEPARTMENTS.get(department, RELATED_DEPARTMENTS["company"])[:4]


def _scope_findings(findings: list[PatternFinding], active_department: str) -> list[PatternFinding]:
    if active_department in {"ceo", "company", ""}:
        return findings
    return [
        finding
        for finding in findings
        if finding.department == active_department or active_department in finding.related_departments
    ]


def _dedupe(findings: list[PatternFinding]) -> list[PatternFinding]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[PatternFinding] = []
    for finding in findings:
        key = (finding.finding_type, finding.department, finding.suggested_action)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


def _severity_rank(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 0)
