"""Lightweight operational input service for FMCG MVP forms."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.services.memory.repository import MemoryRepository


OPERATIONAL_FIELDS: dict[str, list[str]] = {
    "production_ai": ["production_quantity", "downtime", "wastage", "line_issues"],
    "sales_ai": ["daily_sales", "collections", "market_issues"],
    "finance_ai": ["expenses", "payment_delays", "cashflow_notes"],
    "marketing_ai": ["campaign_status", "launch_updates", "competitor_notes"],
}


class OperationalInputService:
    """Stores daily operational forms as tenant-scoped memory events."""

    def __init__(self, db: Any) -> None:
        self.memory_repo = MemoryRepository(db)

    async def submit_input(
        self,
        *,
        company_id: UUID,
        user_id: UUID,
        department_id: UUID,
        department_type: str,
        form_type: str,
        metrics: dict[str, Any],
        notes: str,
        severity: str,
    ) -> dict[str, Any]:
        normalized_department_type = department_type.strip().lower()
        normalized_severity = _normalize_severity(severity)
        cleaned_metrics = _clean_metrics(metrics)
        summary = _build_summary(
            department_type=normalized_department_type,
            metrics=cleaned_metrics,
            notes=notes,
            severity=normalized_severity,
        )
        event_type = f"operational.{_department_key(normalized_department_type)}.{form_type or 'daily_input'}"
        context = {
            "source": "operational_input_form",
            "department_id": str(department_id),
            "department_type": normalized_department_type,
            "form_type": form_type or "daily_input",
            "metrics": cleaned_metrics,
            "notes": notes.strip(),
            "severity": normalized_severity,
            "submitted_by_user_id": str(user_id),
        }
        idempotency_key = _idempotency_key(company_id, user_id, department_id, context)

        await self.memory_repo.insert_event(
            {
                "company_id": str(company_id),
                "session_id": f"operational-{department_id}",
                "event_type": event_type,
                "user_message": f"Operational form submitted for {normalized_department_type}",
                "executive_summary": summary,
                "logic_json": {
                    "operational_event": True,
                    "department_type": normalized_department_type,
                    "metrics": cleaned_metrics,
                    "severity": normalized_severity,
                    "impact_hint": _impact_hint(normalized_department_type),
                },
                "context": context,
                "tags": [
                    "operational_event",
                    normalized_department_type,
                    normalized_severity,
                    form_type or "daily_input",
                ],
                "idempotency_key": idempotency_key,
            }
        )

        return {
            "status": "stored",
            "event_type": event_type,
            "department_id": department_id,
            "department_type": normalized_department_type,
            "summary": summary,
            "memory_event_created": True,
        }


def _clean_metrics(metrics: dict[str, Any]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in (metrics or {}).items():
        clean_key = str(key).strip()
        clean_value = " ".join(str(value or "").split())
        if clean_key and clean_value:
            cleaned[clean_key] = clean_value[:240]
    return cleaned


def _build_summary(
    *,
    department_type: str,
    metrics: dict[str, str],
    notes: str,
    severity: str,
) -> str:
    label = _department_key(department_type).replace("_", " ").title()
    metric_text = ", ".join(f"{key}: {value}" for key, value in metrics.items()) or "no metrics submitted"
    note_text = " ".join((notes or "").split())[:300]
    if note_text:
        return f"{label} daily input ({severity}): {metric_text}. Notes: {note_text}"
    return f"{label} daily input ({severity}): {metric_text}."


def _impact_hint(department_type: str) -> str:
    hints = {
        "production_ai": "Production affects stock availability, distribution timing, wastage, and margin.",
        "sales_ai": "Sales affects demand signals, collections, stock pressure, fulfillment, and revenue quality.",
        "finance_ai": "Finance affects margin, cash flow, payment discipline, and approval guardrails.",
        "marketing_ai": "Marketing affects demand generation, launch timing, stock pressure, and campaign ROI.",
    }
    return hints.get(department_type, "Operational event may affect cross-department execution.")


def _department_key(department_type: str) -> str:
    return department_type.removesuffix("_ai") or "department"


def _normalize_severity(value: str) -> str:
    normalized = (value or "normal").strip().lower()
    return normalized if normalized in {"normal", "watch", "high", "critical"} else "normal"


def _idempotency_key(
    company_id: UUID,
    user_id: UUID,
    department_id: UUID,
    context: dict[str, Any],
) -> str:
    day = datetime.now(timezone.utc).date().isoformat()
    raw = json.dumps(context, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"operational:{company_id}:{department_id}:{user_id}:{day}:{digest}"
