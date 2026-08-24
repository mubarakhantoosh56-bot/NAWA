"""Repository for ome_decision_memories (M8 Slice 2).

Append-only: no delete method. Corrections happen only through
supersede_with_new_decision, never an in-place UPDATE of substantive
fields (decision_text/rationale).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.ome.errors import InvalidSupersession
from app.ome.models import DecisionMemory

DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 50


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIST_LIMIT))


def _require_valid_offset(offset: int) -> int:
    """Fail closed on a malformed offset (M8 Slice 4A required fix): unlike
    _clamp_limit's silent clamping, an out-of-domain offset is a caller bug
    (a negative page position, or `bool` - a subclass of `int` in Python -
    silently being accepted as 0/1) that must never resolve to a
    plausible-looking page result. Raises ValueError, matching the existing
    fail-closed convention used elsewhere in the OME model layer (e.g.
    DecisionMemory/OutcomeMemory's own _required_uuid)."""
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError(f"offset must be a non-negative integer, got {offset!r}")
    return offset


class DecisionMemoryRepository:
    """Database access for tenant-scoped human decision memories."""

    def __init__(self, db: Any) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create(
        self,
        *,
        company_id: UUID,
        reasoning_receipt_id: UUID,
        situation_id: UUID | None,
        decision_text: str,
        rationale: str | None,
        decided_by_user_id: UUID,
        decided_at: datetime,
    ) -> DecisionMemory:
        """Insert one active decision memory scoped to a company."""
        row = await self.db.fetchrow(
            """
            INSERT INTO ome_decision_memories
                (company_id, reasoning_receipt_id, situation_id, decision_text,
                 rationale, decided_by_user_id, decided_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            company_id,
            reasoning_receipt_id,
            situation_id,
            decision_text,
            rationale,
            decided_by_user_id,
            decided_at,
        )
        return DecisionMemory.from_row(dict(row))

    async def get_by_id(self, *, company_id: UUID, decision_id: UUID) -> DecisionMemory | None:
        """Return one decision by id, scoped to company_id. A decision
        belonging to another company resolves to None, identically to a
        decision that does not exist at all (Founder Correction 3)."""
        row = await self.db.fetchrow(
            "SELECT * FROM ome_decision_memories WHERE id = $1 AND company_id = $2",
            decision_id,
            company_id,
        )
        return DecisionMemory.from_row(dict(row)) if row is not None else None

    async def list_recent(
        self,
        *,
        company_id: UUID,
        include_superseded: bool = False,
        limit: int = DEFAULT_LIST_LIMIT,
    ) -> list[DecisionMemory]:
        """Return recent decisions for one company, newest decided_at first."""
        query = "SELECT * FROM ome_decision_memories WHERE company_id = $1"
        if not include_superseded:
            query += " AND status = 'active'"
        query += " ORDER BY decided_at DESC LIMIT $2"
        rows = await self.db.fetch(query, company_id, _clamp_limit(limit))
        return [DecisionMemory.from_row(dict(row)) for row in rows]

    async def list_by_situation(
        self,
        *,
        company_id: UUID,
        situation_id: UUID,
        include_superseded: bool = False,
        limit: int = DEFAULT_LIST_LIMIT,
        offset: int = 0,
    ) -> list[DecisionMemory]:
        """Return decisions linked to one situation, newest decided_at
        first, with an explicit id ASC tie-break for a fully deterministic
        row order (M8 Slice 4A required fix: stable pagination requires a
        deterministic order, not just an ORDER BY that happens to usually
        behave consistently).

        offset defaults to 0 - every existing caller remains valid
        unchanged. It exists so a caller (M8 Slice 4A's
        OrganizationalMemoryRetrievalService, in exact-situation mode) can
        page through one situation's FULL decision history rather than
        being capped at one MAX_LIST_LIMIT-sized page - a decision outside
        the first page must remain reachable, never silently invisible.
        """
        query = "SELECT * FROM ome_decision_memories WHERE company_id = $1 AND situation_id = $2"
        if not include_superseded:
            query += " AND status = 'active'"
        query += " ORDER BY decided_at DESC, id ASC LIMIT $3 OFFSET $4"
        rows = await self.db.fetch(
            query, company_id, situation_id, _clamp_limit(limit), _require_valid_offset(offset)
        )
        return [DecisionMemory.from_row(dict(row)) for row in rows]

    async def list_by_receipt(
        self,
        *,
        company_id: UUID,
        reasoning_receipt_id: UUID,
        include_superseded: bool = False,
    ) -> list[DecisionMemory]:
        """Return every decision made in response to one reasoning receipt."""
        query = "SELECT * FROM ome_decision_memories WHERE company_id = $1 AND reasoning_receipt_id = $2"
        if not include_superseded:
            query += " AND status = 'active'"
        query += " ORDER BY decided_at DESC"
        rows = await self.db.fetch(query, company_id, reasoning_receipt_id)
        return [DecisionMemory.from_row(dict(row)) for row in rows]

    async def supersede_with_new_decision(
        self,
        *,
        company_id: UUID,
        old_decision_id: UUID,
        reasoning_receipt_id: UUID,
        situation_id: UUID | None,
        decision_text: str,
        rationale: str | None,
        decided_by_user_id: UUID,
        decided_at: datetime,
    ) -> tuple[DecisionMemory, DecisionMemory]:
        """Atomically create a replacement decision and mark the old one
        superseded. Returns (new_decision, old_decision_after_update).

        Concurrency: the old row is locked with SELECT ... FOR UPDATE
        BEFORE the replacement is inserted, so a losing concurrent
        transaction raises InvalidSupersession and rolls back before ever
        inserting its own replacement row - no orphan row is ever created
        by a losing attempt. Original substantive fields on the old row
        (decision_text/rationale) are never updated - only status and
        superseded_by.

        Raises InvalidSupersession from inside the transaction (not the
        service layer) because the old-row-active check must happen while
        still holding the FOR UPDATE lock this same method owns; a
        service-layer check afterward could not see a consistent view.
        """
        async with self.db.acquire() as conn:
            async with conn.transaction():
                old_row = await conn.fetchrow(
                    """
                    SELECT * FROM ome_decision_memories
                    WHERE id = $1 AND company_id = $2
                    FOR UPDATE
                    """,
                    old_decision_id,
                    company_id,
                )
                if old_row is None or old_row["status"] != "active":
                    raise InvalidSupersession(
                        f"decision {old_decision_id} is not an active decision inside this company"
                    )

                new_row = await conn.fetchrow(
                    """
                    INSERT INTO ome_decision_memories
                        (company_id, reasoning_receipt_id, situation_id, decision_text,
                         rationale, decided_by_user_id, decided_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    company_id,
                    reasoning_receipt_id,
                    situation_id,
                    decision_text,
                    rationale,
                    decided_by_user_id,
                    decided_at,
                )

                updated_old_row = await conn.fetchrow(
                    """
                    UPDATE ome_decision_memories
                    SET status = 'superseded', superseded_by = $3
                    WHERE id = $1 AND company_id = $2 AND status = 'active'
                    RETURNING *
                    """,
                    old_decision_id,
                    company_id,
                    new_row["id"],
                )
                if updated_old_row is None:
                    raise InvalidSupersession(
                        f"decision {old_decision_id} could not be marked superseded"
                    )

                return DecisionMemory.from_row(dict(new_row)), DecisionMemory.from_row(dict(updated_old_row))
