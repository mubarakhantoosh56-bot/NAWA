"""Service for creating and operating human-governed Actions (M9 Slice 2).

An AI recommendation can never automatically become an Action: there is
no code path here that reads a reasoning response and writes an Action
on its own - title/instructions/decision_memory_id only ever come from
an explicit caller-supplied human action (Architecture Contract Sec 5).

decision_memory_id company-ownership is validated here, before the
repository is ever called - the same pattern DecisionMemoryService uses
for reasoning_receipt_id/situation_id. Assignee membership validation,
by contrast, lives inside ActionRepository's own locked transactions
(Sec 24.1) - it cannot safely happen ahead of the lock.
"""

from __future__ import annotations

from uuid import UUID

from app.ome.errors import ActionNotFound, DecisionNotFound, InvalidMemoryInput
from app.ome.models import ACTION_STATUSES, Action, ActionChangeEvent
from app.ome.repositories.action_repository import ActionRepository
from app.ome.repositories.decision_memory_repository import DecisionMemoryRepository


class ActionService:
    """Business logic for human-governed Action creation, listing, and
    status/assignment mutation."""

    def __init__(self, db) -> None:
        """Initialize the service with its repositories."""
        self.action_repo = ActionRepository(db)
        self.decision_repo = DecisionMemoryRepository(db)

    async def create_action(
        self,
        *,
        company_id: UUID,
        acting_user_id: UUID,
        decision_memory_id: UUID,
        title: str,
        instructions: str | None = None,
        assigned_user_id: UUID | None = None,
    ) -> Action:
        """Record one human-authorized Action against a decision."""
        decision = await self.decision_repo.get_by_id(
            company_id=company_id, decision_id=decision_memory_id
        )
        if decision is None:
            raise DecisionNotFound(f"decision {decision_memory_id} not found inside this company")

        cleaned_title = _require_text(title, field_name="title")
        cleaned_instructions = _clean_optional_text(instructions)

        return await self.action_repo.create(
            company_id=company_id,
            decision_memory_id=decision_memory_id,
            title=cleaned_title,
            instructions=cleaned_instructions,
            created_by_user_id=acting_user_id,
            assigned_user_id=assigned_user_id,
        )

    async def list_actions(
        self,
        *,
        company_id: UUID,
        decision_memory_id: UUID,
        status: str | None = None,
        assigned_user_id: UUID | None = None,
    ) -> list[Action]:
        """List Actions for one decision, optionally filtered by status
        and/or assignee. decision_memory_id is required (Sec 22): an
        unfiltered company-wide list is out of MVP scope."""
        if status is not None and status not in ACTION_STATUSES:
            raise InvalidMemoryInput(f"invalid status filter: {status!r}")
        return await self.action_repo.list_by_decision(
            company_id=company_id,
            decision_memory_id=decision_memory_id,
            status=status,
            assigned_user_id=assigned_user_id,
        )

    async def get_action(
        self, *, company_id: UUID, action_id: UUID
    ) -> tuple[Action, list[ActionChangeEvent]]:
        """Return one Action together with its full change-event history
        (Sec 22: "one action, optionally with its status history")."""
        action = await self.action_repo.get_by_id(company_id=company_id, action_id=action_id)
        if action is None:
            raise ActionNotFound(f"action {action_id} not found inside this company")
        events = await self.action_repo.list_change_events(company_id=company_id, action_id=action_id)
        return action, events

    async def change_status(
        self,
        *,
        company_id: UUID,
        action_id: UUID,
        to_status: str,
        acting_user_id: UUID,
    ) -> Action:
        """Transition an Action's execution state. Transition validity
        and terminal-state enforcement live in the repository, where the
        locked current row is actually read."""
        if to_status not in ACTION_STATUSES:
            raise InvalidMemoryInput(f"invalid status: {to_status!r}")
        return await self.action_repo.change_status(
            company_id=company_id,
            action_id=action_id,
            to_status=to_status,
            changed_by_user_id=acting_user_id,
        )

    async def change_assignee(
        self,
        *,
        company_id: UUID,
        action_id: UUID,
        assigned_user_id: UUID | None,
        acting_user_id: UUID,
    ) -> Action:
        """Set, change, or clear an Action's responsible human. No-op and
        terminal-state rejection, and membership validation, all live in
        the repository's locked transaction."""
        return await self.action_repo.change_assignee(
            company_id=company_id,
            action_id=action_id,
            to_assigned_user_id=assigned_user_id,
            changed_by_user_id=acting_user_id,
        )


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidMemoryInput(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise InvalidMemoryInput(f"{field_name} cannot be blank")
    return cleaned


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidMemoryInput("instructions must be a string")
    cleaned = value.strip()
    return cleaned or None
