"""Service for confirming or rejecting AI-proposed operational event drafts.

Invariant: operational_events is written ONLY via confirm(). No autonomous creation.
Tenant isolation is enforced at every call: company_id always comes from the caller
(which must derive it from the JWT, never from request body or draft row).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.repositories.file_repository import FileRepository
from app.repositories.operational_event_draft_repository import OperationalEventDraftRepository
from app.services.operational_event_service import OperationalEventService

logger = logging.getLogger(__name__)

_VALID_CATEGORIES = frozenset(
    {"daily_update", "kpi", "issue", "decision", "report", "alert", "note"}
)
_VALID_PRIORITIES = frozenset({"low", "normal", "watch", "high", "critical"})


class OperationalEventDraftService:
    """Manages draft lifecycle. Confirmation creates one operational_event with full provenance."""

    def __init__(self, db: Any) -> None:
        self.draft_repo = OperationalEventDraftRepository(db)
        self.event_service = OperationalEventService(db)
        self.file_repo = FileRepository(db)

    async def list_pending(
        self,
        *,
        company_id: UUID,
        file_id: UUID,
    ) -> list[dict[str, Any]]:
        """Return pending drafts for one file. company_id is always from JWT."""
        return await self.draft_repo.list_pending_for_file(
            company_id=company_id,
            file_id=file_id,
        )

    async def confirm(
        self,
        *,
        company_id: UUID,
        file_id: UUID,
        draft_id: UUID,
        confirmed_by_user_id: UUID,
        user_edits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Confirm one pending draft.

        Creates exactly one operational_event with source provenance, then marks
        the draft confirmed. Raises ValueError for any invalid state.
        """
        draft = await self.draft_repo.get_for_company(company_id, draft_id)
        if draft is None:
            raise ValueError("draft not found")
        if str(draft["file_id"]) != str(file_id):
            raise ValueError("draft does not belong to this file")
        if draft["status"] != "pending":
            raise ValueError(f"draft is already {draft['status']}")

        edits = user_edits or {}
        title = _pick(edits.get("title"), draft["proposed_title"])
        category = _coerce_category(edits.get("category") or draft["proposed_category"])
        priority = _coerce_priority(edits.get("priority") or draft["proposed_priority"])
        summary = _pick(edits.get("summary"), draft["proposed_summary"])

        file_record = await self.file_repo.get_file_by_id(
            company_id=company_id,
            file_id=file_id,
        )
        source_ref = str((file_record or {}).get("filename") or "").strip() or None

        event = await self.event_service.create_event(
            company_id=company_id,
            user_id=confirmed_by_user_id,
            event_type="operational.file_draft",
            category=category,
            priority=priority,
            title=title,
            summary=summary,
            department_id=draft.get("department_id"),
            source_type="file_draft",
            source_ref=source_ref,
            metadata={
                "source_file_id": str(draft["file_id"]),
                "draft_id": str(draft["id"]),
                "evidence_quote": str(draft.get("evidence_quote") or ""),
                "confidence": int(draft.get("confidence") or 0),
                "ai_proposed": True,
            },
        )

        updated_draft = await self.draft_repo.mark_confirmed(
            company_id=company_id,
            draft_id=draft_id,
            confirmed_by_user_id=confirmed_by_user_id,
            confirmed_event_id=event["id"],
            user_edits=edits,
        )
        if updated_draft is None:
            raise ValueError("draft was already confirmed by a concurrent request")

        logger.info(
            "draft_confirmed",
            extra={
                "company_id": str(company_id),
                "draft_id": str(draft_id),
                "event_id": str(event["id"]),
            },
        )
        return {"draft": updated_draft, "event": event}

    async def reject(
        self,
        *,
        company_id: UUID,
        file_id: UUID,
        draft_id: UUID,
    ) -> dict[str, Any]:
        """Reject a pending draft. No operational_event is created."""
        draft = await self.draft_repo.get_for_company(company_id, draft_id)
        if draft is None:
            raise ValueError("draft not found")
        if str(draft["file_id"]) != str(file_id):
            raise ValueError("draft does not belong to this file")
        if draft["status"] != "pending":
            raise ValueError(f"draft is already {draft['status']}")

        updated = await self.draft_repo.mark_rejected(
            company_id=company_id,
            draft_id=draft_id,
        )
        logger.info(
            "draft_rejected",
            extra={"company_id": str(company_id), "draft_id": str(draft_id)},
        )
        return updated or draft


def _pick(override: object, fallback: str) -> str:
    cleaned = str(override or "").strip()
    return cleaned if cleaned else str(fallback or "").strip()


def _coerce_category(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in _VALID_CATEGORIES else "daily_update"


def _coerce_priority(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in _VALID_PRIORITIES else "normal"
