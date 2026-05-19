from app.services.decision_context import build_decision_context, build_decision_context_prompt_block
from app.services.operational_pattern_detector import detect_operational_patterns


def operational_event(
    *,
    department: str,
    category: str,
    priority: str,
    summary: str,
    text: str = "",
    metrics: dict[str, str] | None = None,
):
    return {
        "event_type": f"operational.{department}.{category}",
        "executive_summary": summary,
        "logic_json": {"impact_hint": "Operational handoff affects service level."},
        "context": {
            "source_role": f"{department}_manager",
            "source_department": department,
            "target_department": "",
            "category": category,
            "priority": priority,
            "payload": {
                "text": text,
                "metrics": metrics or {},
            },
        },
    }


def test_detects_implied_delay_without_delay_word():
    events = [
        operational_event(
            department="production",
            category="issue",
            priority="high",
            summary="Production issue: finished goods are waiting for warehouse release.",
            text="Dispatch team did not receive release confirmation before route planning.",
        ),
        operational_event(
            department="production",
            category="issue",
            priority="watch",
            summary="Production issue: pallets are still pending QA signoff.",
            text="Sales commitment window is blocked until signoff.",
        ),
    ]

    findings = detect_operational_patterns(events, active_department="ceo")

    assert any(finding["finding_type"] == "bottleneck" for finding in findings)
    assert any(finding["department"] == "production" for finding in findings)
    assert any("warehouse" in finding["related_departments"] for finding in findings)


def test_detects_positive_signals_and_strong_performance():
    events = [
        operational_event(
            department="sales",
            category="kpi",
            priority="normal",
            summary="Sales kpi: collections improved above target.",
            text="Team completed all key account follow-ups on time.",
            metrics={"collections": "up 14%", "conversion": "strong"},
        )
    ]

    findings = detect_operational_patterns(events, active_department="ceo")

    assert any(finding["finding_type"] == "positive" for finding in findings)
    assert any(finding["department"] == "sales" for finding in findings)


def test_detects_repeated_issue_and_high_priority_risk():
    events = [
        operational_event(
            department="finance",
            category="issue",
            priority="high",
            summary="Finance issue: three customer payments are unresolved.",
        ),
        operational_event(
            department="finance",
            category="issue",
            priority="critical",
            summary="Finance issue: distributor credit exposure remains without owner.",
        ),
    ]

    findings = detect_operational_patterns(events, active_department="ceo")

    assert any(finding["finding_type"] == "risk" and finding["severity"] == "critical" for finding in findings)
    assert any("repeated issue" in finding["suggested_action"].lower() for finding in findings)


def test_decision_context_includes_patterns_for_ceo_and_scopes_for_department():
    events = [
        operational_event(
            department="production",
            category="issue",
            priority="high",
            summary="Production issue: pallets waiting for warehouse release.",
            text="No dispatch confirmation before route planning.",
        ),
        operational_event(
            department="marketing",
            category="kpi",
            priority="normal",
            summary="Marketing kpi: campaign response improved above target.",
            metrics={"response_rate": "up 9%"},
        ),
    ]

    ceo_context = build_decision_context(
        context={"nawa_role": {"slug": "ceo"}},
        response_language="en",
        memory_events=events,
    )
    production_context = build_decision_context(
        context={
            "nawa_role": {"slug": "production_manager"},
            "aimx_department": {"department_type": "production_ai"},
        },
        response_language="en",
        memory_events=events,
    )

    assert len(ceo_context["detected_patterns"]) >= 2
    assert all(
        finding["department"] == "production" or "production" in finding["related_departments"]
        for finding in production_context["detected_patterns"]
    )


def test_decision_context_prompt_mentions_detected_patterns():
    context = build_decision_context(
        context={"nawa_role": {"slug": "ceo"}},
        response_language="en",
        memory_events=[
            operational_event(
                department="operations",
                category="issue",
                priority="high",
                summary="Operations issue: route dispatch is waiting for stock confirmation.",
            )
        ],
    )
    block = build_decision_context_prompt_block(context)

    assert "detected_patterns" in block
    assert "biggest risks, operational mistakes, positive signals" in block
