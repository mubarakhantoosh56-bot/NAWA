"""Service layer for the NAWA Live Operational Timeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.repositories.department_repository import DepartmentRepository
from app.repositories.operational_event_repository import OperationalEventRepository


VALID_PRIORITIES = {"low", "normal", "watch", "high", "critical"}


class OperationalEventService:
    """Business logic for tenant-scoped operational events."""

    def __init__(self, db: Any) -> None:
        """Initialize the service with timeline and department repositories."""
        self.event_repo = OperationalEventRepository(db)
        self.department_repo = DepartmentRepository(db)

    async def create_event(
        self,
        *,
        company_id: UUID,
        user_id: UUID,
        event_type: str,
        category: str,
        priority: str,
        title: str,
        summary: str,
        department_id: UUID | None = None,
        event_timestamp: datetime | None = None,
        source_type: str = "manual",
        source_ref: str | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Validate and create one operational timeline event."""
        if department_id is not None:
            department = await self.department_repo.get_by_id(
                company_id=company_id,
                department_id=department_id,
            )
            if department is None:
                raise ValueError("Invalid department_id")

        return await self.event_repo.create_event(
            company_id=company_id,
            created_by_user_id=user_id,
            department_id=department_id,
            event_type=_clean_text(event_type, default="operational.manual", max_chars=120),
            category=_clean_text(category, default="daily_update", max_chars=80),
            priority=_normalize_priority(priority),
            title=_clean_text(title, default="", max_chars=240),
            summary=_clean_text(summary, default="", max_chars=2000),
            event_timestamp=event_timestamp,
            source_type=_clean_text(source_type, default="manual", max_chars=80),
            source_ref=_clean_optional_text(source_ref, max_chars=240),
            payload=_clean_mapping(payload),
            metadata=_clean_mapping(metadata),
        )

    async def list_events(
        self,
        *,
        company_id: UUID,
        department_id: UUID | None = None,
        category: str | None = None,
        priority: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return operational events visible inside one company."""
        if department_id is not None:
            department = await self.department_repo.get_by_id(
                company_id=company_id,
                department_id=department_id,
            )
            if department is None:
                raise ValueError("Invalid department_id")

        normalized_priority = _normalize_priority(priority) if priority else None
        normalized_category = _clean_optional_text(category, max_chars=80)
        return await self.event_repo.list_events(
            company_id=company_id,
            department_id=department_id,
            category=normalized_category,
            priority=normalized_priority,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )


def _clean_text(value: str | None, *, default: str, max_chars: int) -> str:
    cleaned = " ".join(str(value or default).split())[:max_chars].strip()
    if not cleaned:
        raise ValueError("Required event text is empty")
    return cleaned


def _clean_optional_text(value: str | None, *, max_chars: int) -> str | None:
    cleaned = " ".join(str(value or "").split())[:max_chars].strip()
    return cleaned or None


def _normalize_priority(value: str) -> str:
    normalized = (value or "normal").strip().lower()
    return normalized if normalized in VALID_PRIORITIES else "normal"


def _clean_mapping(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return value
