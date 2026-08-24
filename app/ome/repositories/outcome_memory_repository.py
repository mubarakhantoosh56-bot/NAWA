"""Repository for ome_outcome_memories (M8 Slice 2).

Append-only: no delete method, no generic global outcome search. Same
atomic supersession pattern as DecisionMemoryRepository.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.ome.errors import InvalidSupersession
from app.ome.models import OutcomeMemory


class OutcomeMemoryRepository:
    """Database access for tenant-scoped human-recorded outcome memories."""

    def __init__(self, db: Any) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create(
        self,
        *,
        company_id: UUID,
        decision_memory_id: UUID,
        outcome_summary: str,
        result_state: str,
        recorded_by_user_id: UUID,
        observed_at: datetime,
    ) -> OutcomeMemory:
        """Insert one active outcome memory scoped to a company."""
        row = await self.db.fetchrow(
            """
            INSERT INTO ome_outcome_memories
                (company_id, decision_memory_id, outcome_summary, result_state,
                 recorded_by_user_id, observed_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            company_id,
            decision_memory_id,
            outcome_summary,
            result_state,
            recorded_by_user_id,
            observed_at,
        )
        return OutcomeMemory.from_row(dict(row))

    async def get_by_id(self, *, company_id: UUID, outcome_id: UUID) -> OutcomeMemory | None:
        """Return one outcome by id, scoped to company_id. An outcome
        belonging to another company resolves to None, identically to an
        outcome that does not exist at all (Founder Correction 3)."""
        row = await self.db.fetchrow(
            "SELECT * FROM ome_outcome_memories WHERE id = $1 AND company_id = $2",
            outcome_id,
            company_id,
        )
        return OutcomeMemory.from_row(dict(row)) if row is not None else None

    async def list_by_decision(
        self,
        *,
        company_id: UUID,
        decision_memory_id: UUID,
        include_superseded: bool = False,
    ) -> list[OutcomeMemory]:
        """Return outcomes recorded for one decision, newest observed_at first."""
        query = "SELECT * FROM ome_outcome_memories WHERE company_id = $1 AND decision_memory_id = $2"
        if not include_superseded:
            query += " AND status = 'active'"
        query += " ORDER BY observed_at DESC"
        rows = await self.db.fetch(query, company_id, decision_memory_id)
        return [OutcomeMemory.from_row(dict(row)) for row in rows]

    async def supersede_with_new_outcome(
        self,
        *,
        company_id: UUID,
        old_outcome_id: UUID,
        outcome_summary: str,
        result_state: str,
        recorded_by_user_id: UUID,
        observed_at: datetime,
    ) -> tuple[OutcomeMemory, OutcomeMemory]:
        """Atomically create a replacement outcome and mark the old one
        superseded. Returns (new_outcome, old_outcome_after_update).

        No decision_memory_id parameter (Codex-required fix): an outcome
        supersession corrects the historical outcome record for the SAME
        decision - it is never a way to re-attach an outcome to a
        different decision (that would corrupt the meaning of the
        supersession chain; a genuinely different decision's outcome must
        go through create(), not supersession). The replacement's
        decision_memory_id is therefore read directly off the locked old
        row, inside this same transaction - the caller cannot forge it.

        Same lock-before-insert concurrency contract as
        DecisionMemoryRepository.supersede_with_new_decision - see that
        method's docstring for the full rationale.
        """
        async with self.db.acquire() as conn:
            async with conn.transaction():
                old_row = await conn.fetchrow(
                    """
                    SELECT * FROM ome_outcome_memories
                    WHERE id = $1 AND company_id = $2
                    FOR UPDATE
                    """,
                    old_outcome_id,
                    company_id,
                )
                if old_row is None or old_row["status"] != "active":
                    raise InvalidSupersession(
                        f"outcome {old_outcome_id} is not an active outcome inside this company"
                    )

                decision_memory_id = old_row["decision_memory_id"]

                new_row = await conn.fetchrow(
                    """
                    INSERT INTO ome_outcome_memories
                        (company_id, decision_memory_id, outcome_summary, result_state,
                         recorded_by_user_id, observed_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                    """,
                    company_id,
                    decision_memory_id,
                    outcome_summary,
                    result_state,
                    recorded_by_user_id,
                    observed_at,
                )

                updated_old_row = await conn.fetchrow(
                    """
                    UPDATE ome_outcome_memories
                    SET status = 'superseded', superseded_by = $3
                    WHERE id = $1 AND company_id = $2 AND status = 'active'
                    RETURNING *
                    """,
                    old_outcome_id,
                    company_id,
                    new_row["id"],
                )
                if updated_old_row is None:
                    raise InvalidSupersession(
                        f"outcome {old_outcome_id} could not be marked superseded"
                    )

                return OutcomeMemory.from_row(dict(new_row)), OutcomeMemory.from_row(dict(updated_old_row))
