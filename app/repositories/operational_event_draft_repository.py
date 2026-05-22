"""Repository for AI-proposed operational event drafts.

All queries filter by company_id. No query touches operational_events.
Drafts remain pending until the service layer explicitly confirms or rejects them.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

_VALID_CATEGORIES = frozenset(
    {"daily_update", "kpi", "issue", "decision", "report", "alert", "note"}
)
_VALID_PRIORITIES = frozenset({"low", "normal", "watch", "high", "critical"})


class OperationalEventDraftRepository:
    """All SQL for the operational_event_drafts table."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def create_drafts(
        self,
        *,
        company_id: UUID,
        file_id: UUID,
        department_id: UUID | None,
        created_by_user_id: UUID,
        proposals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Insert up to 5 draft proposals for one file. Every row carries company_id."""
        query = """
        INSERT INTO operational_event_drafts
            (company_id, file_id, department_id, created_by_user_id,
             proposed_title, proposed_category, proposed_priority,
             proposed_summary, evidence_quote, confidence,
             needs_clarification, clarification_hint)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING *
        """
        created: list[dict[str, Any]] = []
        async with self.db.acquire() as conn:
            for proposal in proposals[:5]:
                row = await conn.fetchrow(
                    query,
                    company_id,
                    file_id,
                    department_id,
                    created_by_user_id,
                    str(proposal.get("proposed_title") or "")[:240],
                    _coerce_category(proposal.get("proposed_category")),
                    _coerce_priority(proposal.get("proposed_priority")),
                    str(proposal.get("proposed_summary") or "")[:2000],
                    _trim_or_none(proposal.get("evidence_quote"), 400),
                    _clamp_confidence(proposal.get("confidence")),
                    bool(proposal.get("needs_clarification") or False),
                    _trim_or_none(proposal.get("clarification_hint"), 400),
                )
                if row:
                    created.append(dict(row))
        return created

    async def list_pending_for_file(
        self,
        company_id: UUID,
        file_id: UUID,
    ) -> list[dict[str, Any]]:
        """Return pending drafts for one file, scoped to the authenticated company."""
        query = """
        SELECT *
        FROM operational_event_drafts
        WHERE company_id = $1 AND file_id = $2 AND status = 'pending'
        ORDER BY confidence DESC, created_at ASC
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, company_id, file_id)
        return [dict(r) for r in rows]

    async def get_for_company(
        self,
        company_id: UUID,
        draft_id: UUID,
    ) -> dict[str, Any] | None:
        """Return one draft by ID. company_id filter enforces tenant isolation."""
        query = """
        SELECT *
        FROM operational_event_drafts
        WHERE id = $1 AND company_id = $2
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, draft_id, company_id)
        return dict(row) if row else None

    async def mark_confirmed(
        self,
        *,
        company_id: UUID,
        draft_id: UUID,
        confirmed_by_user_id: UUID,
        confirmed_event_id: UUID,
        user_edits: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Set status=confirmed. Only succeeds if status is currently pending."""
        query = """
        UPDATE operational_event_drafts
        SET
            status               = 'confirmed',
            confirmed_by_user_id = $3,
            confirmed_event_id   = $4,
            user_edits           = $5::jsonb,
            confirmed_at         = NOW(),
            updated_at           = NOW()
        WHERE id = $1 AND company_id = $2 AND status = 'pending'
        RETURNING *
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                query,
                draft_id,
                company_id,
                confirmed_by_user_id,
                confirmed_event_id,
                json.dumps(user_edits, ensure_ascii=False),
            )
        return dict(row) if row else None

    async def mark_rejected(
        self,
        *,
        company_id: UUID,
        draft_id: UUID,
    ) -> dict[str, Any] | None:
        """Set status=rejected. Only succeeds if status is currently pending."""
        query = """
        UPDATE operational_event_drafts
        SET
            status     = 'rejected',
            updated_at = NOW()
        WHERE id = $1 AND company_id = $2 AND status = 'pending'
        RETURNING *
        """
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, draft_id, company_id)
        return dict(row) if row else None


def _coerce_category(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in _VALID_CATEGORIES else "daily_update"


def _coerce_priority(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in _VALID_PRIORITIES else "normal"


def _clamp_confidence(value: object) -> int:
    try:
        return max(0, min(100, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _trim_or_none(value: object, max_len: int) -> str | None:
    text = str(value or "").strip()
    return text[:max_len] if text else None
