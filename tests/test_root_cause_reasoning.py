from app.services.decision_context import build_decision_context, build_decision_context_prompt_block
from app.services.root_cause_reasoning import build_root_cause_reasoning


def test_line_instability_chain_prioritizes_fulfillment_and_margin():
    reasoning = build_root_cause_reasoning(
        department_key="ceo",
        detected_patterns=[
            {
                "finding_type": "bottleneck",
                "department": "production",
                "related_departments": ["warehouse", "operations", "sales", "finance"],
                "evidence": [
                    "Production issue: line speed down and finished goods waiting for dispatch.",
                    "Production issue: overtime added after downtime.",
                ],
                "severity": "high",
                "confidence": 86,
                "suggested_action": "Stabilize the line today.",
            }
        ],
        operational_events=[],
        related_departments=[
            "Production capacity drives inventory availability, distribution load, sales commitments, and cash exposure.",
            "Distribution delays reduce fulfillment.",
        ],
    )

    assert reasoning["likely_operational_bottleneck"] == "Production reliability is constraining fulfillment capacity."
    assert "Warehouse and distribution" in " ".join(reasoning["probable_cause_effect_chain"])
    assert "margin pressure" in reasoning["operational_impact"]
    assert "production" in reasoning["affected_departments"]
    assert "finance" in reasoning["affected_departments"]


def test_sales_growth_low_stock_chain_flags_supply_risk():
    reasoning = build_root_cause_reasoning(
        department_key="ceo",
        detected_patterns=[
            {
                "finding_type": "risk",
                "department": "sales",
                "related_departments": ["warehouse", "production", "operations"],
                "evidence": ["Sales kpi: orders up 18% while low stock complaints increased."],
                "severity": "high",
                "confidence": 82,
                "suggested_action": "Reconcile demand and stock.",
            }
        ],
        operational_events=[],
        related_departments=[],
    )

    assert reasoning["likely_operational_bottleneck"] == "Demand is running ahead of available stock."
    assert "Sales commitments may exceed production or warehouse readiness." in reasoning["probable_cause_effect_chain"]
    assert "Supply risk" in reasoning["operational_impact"]


def test_decision_context_includes_root_cause_reasoning_and_prompt_rules():
    event = {
        "event_type": "operational.production.issue",
        "executive_summary": "Production issue: line speed down, overtime rising, and finished goods waiting for warehouse release.",
        "logic_json": {"impact_hint": "Production reliability affects service level and margin."},
        "context": {
            "source_role": "production_manager",
            "source_department": "production",
            "category": "issue",
            "priority": "high",
            "payload": {
                "text": "Line speed down and overtime added after downtime.",
                "metrics": {"line_speed": "down 12%", "overtime": "up 9%"},
            },
        },
    }
    context = build_decision_context(
        context={"nawa_role": {"slug": "ceo"}},
        response_language="en",
        memory_events=[event],
    )
    block = build_decision_context_prompt_block(context)

    assert context["root_cause_reasoning"]["likely_operational_bottleneck"]
    assert "root_cause_reasoning" in block
    assert "operating narrative spine" in block
    assert "execution capacity, fulfillment constraints, production readiness" in block
    assert "Avoid generic phrases" in block
