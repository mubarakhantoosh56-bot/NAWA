"""Repository for ome_actions / ome_action_change_events (M9 Slice 2).

The ome_actions row is the authoritative CURRENT execution state.
ome_action_change_events is an immutable, append-only side ledger - this
repository exposes no update/delete for events; they are written only as
a direct consequence of a valid Action creation, status transition, or
reassignment (Architecture Contract Sec 9.3/9.5).

Locked-row discipline (Sec 24 / 24.1): status and assignment mutation
each run inside ONE transaction, reading the actual current state from a
SELECT ... FOR UPDATE row - never from a client-supplied prior value -
mirroring the pattern already proven by
DecisionMemoryRepository.supersede_with_new_decision.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.ome.errors import ActionNotFound, InvalidActionTransition, InvalidAssignee
from app.ome.models import Action, ActionChangeEvent
from app.repositories.membership_repository import MembershipRepository

# Ratified state machine (Architecture Contract Sec 8). completed/cancelled
# are terminal - no transition out of either is ever valid, including
# reopening (Decision 8).
ALLOWED_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"in_progress", "completed", "cancelled"}),
    "in_progress": frozenset({"completed", "cancelled"}),
    "completed": frozenset(),
    "cancelled": frozenset(),
}

TERMINAL_STATUSES = frozenset({"completed", "cancelled"})


class ActionRepository:
    """Database access for tenant-scoped human-governed Actions and their
    append-only change ledger."""

    def __init__(self, db: Any) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create(
        self,
        *,
        company_id: UUID,
        decision_memory_id: UUID,
        title: str,
        instructions: str | None,
        created_by_user_id: UUID,
        assigned_user_id: UUID | None,
    ) -> Action:
        """Insert one Action plus its initial status event (NULL -> pending)
        and, if created with an assignee, its initial assignment event
        (NULL -> assigned_user_id) - atomically, in one transaction. An
        Action without its creation event must be impossible (Sec 24).

        If assigned_user_id is provided, active same-company membership is
        validated inside this same transaction; an invalid target raises
        InvalidAssignee and nothing is written.
        """
        async with self.db.acquire() as conn:
            async with conn.transaction():
                if assigned_user_id is not None:
                    membership = await MembershipRepository(conn).get_active_membership(
                        company_id, assigned_user_id
                    )
                    if membership is None:
                        raise InvalidAssignee(
                            f"user {assigned_user_id} has no active membership in this company"
                        )

                row = await conn.fetchrow(
                    """
                    INSERT INTO ome_actions
                        (company_id, decision_memory_id, title, instructions,
                         created_by_user_id, assigned_user_id)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                    """,
                    company_id,
                    decision_memory_id,
                    title,
                    instructions,
                    created_by_user_id,
                    assigned_user_id,
                )

                await conn.execute(
                    """
                    INSERT INTO ome_action_change_events
                        (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                    VALUES ($1, $2, 'status', NULL, 'pending', $3)
                    """,
                    company_id,
                    row["id"],
                    created_by_user_id,
                )

                if assigned_user_id is not None:
                    await conn.execute(
                        """
                        INSERT INTO ome_action_change_events
                            (company_id, action_id, change_type, from_assigned_user_id, to_assigned_user_id, changed_by_user_id)
                        VALUES ($1, $2, 'assignment', NULL, $3, $4)
                        """,
                        company_id,
                        row["id"],
                        assigned_user_id,
                        created_by_user_id,
                    )

                return Action.from_row(dict(row))

    async def get_by_id(self, *, company_id: UUID, action_id: UUID) -> Action | None:
        """Return one Action by id, scoped to company_id. An Action
        belonging to another company resolves to None, identically to an
        Action that does not exist at all (Founder Correction 3)."""
        row = await self.db.fetchrow(
            "SELECT * FROM ome_actions WHERE id = $1 AND company_id = $2",
            action_id,
            company_id,
        )
        return Action.from_row(dict(row)) if row is not None else None

    async def list_by_decision(
        self,
        *,
        company_id: UUID,
        decision_memory_id: UUID,
        status: str | None = None,
        assigned_user_id: UUID | None = None,
    ) -> list[Action]:
        """Return Actions for one decision, newest created_at first, with
        an explicit id ASC tie-break for a deterministic order."""
        query = "SELECT * FROM ome_actions WHERE company_id = $1 AND decision_memory_id = $2"
        params: list[Any] = [company_id, decision_memory_id]
        if status is not None:
            params.append(status)
            query += f" AND status = ${len(params)}"
        if assigned_user_id is not None:
            params.append(assigned_user_id)
            query += f" AND assigned_user_id = ${len(params)}"
        query += " ORDER BY created_at DESC, id ASC"
        rows = await self.db.fetch(query, *params)
        return [Action.from_row(dict(row)) for row in rows]

    async def list_change_events(self, *, company_id: UUID, action_id: UUID) -> list[ActionChangeEvent]:
        """Return the full chronological change ledger for one Action -
        deterministic display order only (changed_at ASC, id ASC tie
        -break); see the ledger's own migration comment for why this is
        not itself a causal-order guarantee."""
        rows = await self.db.fetch(
            """
            SELECT * FROM ome_action_change_events
            WHERE company_id = $1 AND action_id = $2
            ORDER BY changed_at ASC, id ASC
            """,
            company_id,
            action_id,
        )
        return [ActionChangeEvent.from_row(dict(row)) for row in rows]

    async def change_status(
        self,
        *,
        company_id: UUID,
        action_id: UUID,
        to_status: str,
        changed_by_user_id: UUID,
    ) -> Action:
        """Locked-row status transition. Reads the actual current status
        from a FOR UPDATE row, validates it against
        ALLOWED_STATUS_TRANSITIONS, updates the row (including terminal
        timestamps) and inserts exactly one status change event, all in
        one transaction. A rejected transition performs no mutation and
        inserts no event."""
        async with self.db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT * FROM ome_actions WHERE id = $1 AND company_id = $2 FOR UPDATE",
                    action_id,
                    company_id,
                )
                if row is None:
                    raise ActionNotFound(f"action {action_id} not found inside this company")

                from_status = row["status"]
                if to_status not in ALLOWED_STATUS_TRANSITIONS.get(from_status, frozenset()):
                    raise InvalidActionTransition(
                        f"action {action_id} cannot transition from {from_status!r} to {to_status!r}"
                    )

                now = datetime.now(timezone.utc)
                completed_at = now if to_status == "completed" else None
                cancelled_at = now if to_status == "cancelled" else None

                updated = await conn.fetchrow(
                    """
                    UPDATE ome_actions
                    SET status = $3, completed_at = $4, cancelled_at = $5, updated_at = NOW()
                    WHERE id = $1 AND company_id = $2
                    RETURNING *
                    """,
                    action_id,
                    company_id,
                    to_status,
                    completed_at,
                    cancelled_at,
                )

                await conn.execute(
                    """
                    INSERT INTO ome_action_change_events
                        (company_id, action_id, change_type, from_status, to_status, changed_by_user_id)
                    VALUES ($1, $2, 'status', $3, $4, $5)
                    """,
                    company_id,
                    action_id,
                    from_status,
                    to_status,
                    changed_by_user_id,
                )

                return Action.from_row(dict(updated))

    async def change_assignee(
        self,
        *,
        company_id: UUID,
        action_id: UUID,
        to_assigned_user_id: UUID | None,
        changed_by_user_id: UUID,
    ) -> Action:
        """Locked-row reassignment (Sec 24.1's exact eight-step sequence).
        Reads the actual current assignee from a FOR UPDATE row - never
        from a client-supplied prior value - validates non-terminal
        state, rejects a no-op target, validates active same-company
        membership for a non-null target, updates the row, and inserts
        exactly one assignment change event, all in one transaction. A
        rejected reassignment performs no mutation and inserts no event."""
        async with self.db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT * FROM ome_actions WHERE id = $1 AND company_id = $2 FOR UPDATE",
                    action_id,
                    company_id,
                )
                if row is None:
                    raise ActionNotFound(f"action {action_id} not found inside this company")

                if row["status"] in TERMINAL_STATUSES:
                    raise InvalidActionTransition(
                        f"action {action_id} is terminal ({row['status']!r}) and cannot be reassigned"
                    )

                from_assigned_user_id = row["assigned_user_id"]

                if to_assigned_user_id == from_assigned_user_id:
                    raise InvalidActionTransition(
                        "no-op reassignment: target assignee is unchanged"
                    )

                if to_assigned_user_id is not None:
                    membership = await MembershipRepository(conn).get_active_membership(
                        company_id, to_assigned_user_id
                    )
                    if membership is None:
                        raise InvalidAssignee(
                            f"user {to_assigned_user_id} has no active membership in this company"
                        )

                updated = await conn.fetchrow(
                    """
                    UPDATE ome_actions
                    SET assigned_user_id = $3, updated_at = NOW()
                    WHERE id = $1 AND company_id = $2
                    RETURNING *
                    """,
                    action_id,
                    company_id,
                    to_assigned_user_id,
                )

                await conn.execute(
                    """
                    INSERT INTO ome_action_change_events
                        (company_id, action_id, change_type, from_assigned_user_id, to_assigned_user_id, changed_by_user_id)
                    VALUES ($1, $2, 'assignment', $3, $4, $5)
                    """,
                    company_id,
                    action_id,
                    from_assigned_user_id,
                    to_assigned_user_id,
                    changed_by_user_id,
                )

                return Action.from_row(dict(updated))
