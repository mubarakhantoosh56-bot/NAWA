"""Universal operational input service for NAWA MVP updates."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.services.memory.repository import MemoryRepository


UNIVERSAL_CATEGORIES = {
    "daily_update",
    "kpi",
    "issue",
    "decision",
    "report",
    "document",
    "alert",
    "note",
}


class OperationalInputService:
    """Stores universal operational updates as tenant-scoped memory events."""

    def __init__(self, db: Any) -> None:
        self.memory_repo = MemoryRepository(db)

    async def submit_input(
        self,
        *,
        company_id: UUID,
        user_id: UUID,
        source_role: str,
        source_department_id: UUID | None,
        source_department_type: str | None,
        target_department_id: UUID | None,
        target_department_type: str | None,
        category: str,
        priority: str,
        event_date: str | None,
        text: str,
        metrics: dict[str, Any],
        files_attached: list[dict[str, Any]],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_category = _normalize_category(category)
        normalized_priority = _normalize_priority(priority)
        cleaned_metrics = _clean_mapping(metrics)
        cleaned_payload = _clean_mapping(payload)
        cleaned_files = _clean_files(files_attached)
        source_department = _department_key(source_department_type)
        target_department = _department_key(target_department_type)
        scope = target_department or source_department or "company"
        summary = _build_summary(
            category=normalized_category,
            priority=normalized_priority,
            scope=scope,
            text=text,
            metrics=cleaned_metrics,
            files_attached=cleaned_files,
        )
        event_type = f"operational.{scope}.{normalized_category}"
        context = {
            "source": "universal_operational_input",
            "source_role": source_role,
            "source_department": source_department,
            "source_department_id": str(source_department_id) if source_department_id else None,
            "source_department_type": source_department_type,
            "target_department": target_department,
            "target_department_id": str(target_department_id) if target_department_id else None,
            "target_department_type": target_department_type,
            "category": normalized_category,
            "priority": normalized_priority,
            "event_date": event_date,
            "payload": {
                **cleaned_payload,
                "text": " ".join((text or "").split())[:2000],
                "metrics": cleaned_metrics,
            },
            "files_attached": cleaned_files,
            "submitted_by_user_id": str(user_id),
        }
        idempotency_key = _idempotency_key(company_id, user_id, context)

        await self.memory_repo.insert_event(
            {
                "company_id": str(company_id),
                "session_id": f"operational-{scope}",
                "event_type": event_type,
                "user_message": f"Universal operational update submitted for {scope}",
                "executive_summary": summary,
                "logic_json": {
                    "operational_event": True,
                    "source_role": source_role,
                    "source_department": source_department,
                    "target_department": target_department,
                    "category": normalized_category,
                    "priority": normalized_priority,
                    "payload": context["payload"],
                    "files_attached": cleaned_files,
                    "impact_hint": _impact_hint(scope, normalized_category),
                },
                "context": context,
                "tags": [
                    "operational_event",
                    scope,
                    normalized_category,
                    normalized_priority,
                    source_role,
                ],
                "idempotency_key": idempotency_key,
            }
        )

        return {
            "status": "stored",
            "event_type": event_type,
            "department_id": source_department_id,
            "department_type": source_department_type,
            "target_department_id": target_department_id,
            "category": normalized_category,
            "priority": normalized_priority,
            "summary": summary,
            "memory_event_created": True,
        }


def _clean_mapping(values: dict[str, Any]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in (values or {}).items():
        clean_key = str(key).strip()
        clean_value = " ".join(str(value or "").split())
        if clean_key and clean_value:
            cleaned[clean_key] = clean_value[:500]
    return cleaned


def _clean_files(files: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for item in files or []:
        file_id = str(item.get("id") or "").strip()
        filename = str(item.get("filename") or "").strip()
        if file_id or filename:
            cleaned.append({"id": file_id[:80], "filename": filename[:240]})
    return cleaned[:10]


def _build_summary(
    *,
    category: str,
    priority: str,
    scope: str,
    text: str,
    metrics: dict[str, str],
    files_attached: list[dict[str, str]],
) -> str:
    label = scope.replace("_", " ").title()
    metric_text = ", ".join(f"{key}: {value}" for key, value in metrics.items())
    note_text = " ".join((text or "").split())[:500]
    file_text = f"{len(files_attached)} file(s) attached" if files_attached else ""
    parts = [part for part in [note_text, metric_text, file_text] if part]
    detail = ". ".join(parts) if parts else "No detail provided."
    return f"{label} {category.replace('_', ' ')} ({priority}): {detail}"


def _impact_hint(scope: str, category: str) -> str:
    if scope == "company":
        return "Company-wide update should be interpreted across departments, risks, and executive priorities."
    if category == "issue":
        return f"{scope.title()} issue may create cross-department operational risk."
    if category == "kpi":
        return f"{scope.title()} KPI should be interpreted against related departments and operational impact."
    if category == "report":
        return f"{scope.title()} report request should summarize evidence, risks, and recommended decisions."
    return f"{scope.title()} update should be interpreted through department context and related operational dependencies."


def _department_key(department_type: str | None) -> str | None:
    if not department_type:
        return None
    return department_type.strip().lower().removesuffix("_ai") or None


def _normalize_category(value: str) -> str:
    normalized = (value or "daily_update").strip().lower()
    return normalized if normalized in UNIVERSAL_CATEGORIES else "daily_update"


def _normalize_priority(value: str) -> str:
    normalized = (value or "normal").strip().lower()
    return normalized if normalized in {"low", "normal", "watch", "high", "critical"} else "normal"


def _idempotency_key(company_id: UUID, user_id: UUID, context: dict[str, Any]) -> str:
    day = datetime.now(timezone.utc).date().isoformat()
    raw = json.dumps(context, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"operational:{company_id}:{user_id}:{day}:{digest}"
