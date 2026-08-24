"""Repository for ome_reasoning_receipts (M8 Slice 2).

Immutable by repository contract: only create() and get_by_id() exist -
no update, no delete. list_recent_by_company/list_recent_by_session are
deliberately NOT implemented (Founder Correction 1 / Step 5): no current
Slice 2 test or service need requires them, and an existing index is not
by itself a justification for a repository method.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.ome.models import ReasoningReceipt


def _parse_jsonb(value: Any) -> Any:
    """asyncpg returns jsonb columns as raw text unless a codec is
    registered on the pool (none is, here) - same defensive decode
    app/services/memory/repository.py::_parse_jsonb already uses."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


def _row_to_receipt(row: Any) -> ReasoningReceipt:
    data = dict(row)
    data["response_snapshot"] = _parse_jsonb(data["response_snapshot"])
    data["evidence_refs"] = _parse_jsonb(data["evidence_refs"])
    return ReasoningReceipt.from_row(data)


class ReasoningReceiptRepository:
    """Database access for tenant-scoped, immutable reasoning receipts."""

    def __init__(self, db: Any) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create(
        self,
        *,
        company_id: UUID,
        created_by_user_id: UUID,
        session_id: str | None,
        response_snapshot: dict[str, Any],
        evidence_refs: list[dict[str, Any]],
    ) -> ReasoningReceipt:
        """Insert one immutable reasoning receipt scoped to a company."""
        row = await self.db.fetchrow(
            """
            INSERT INTO ome_reasoning_receipts
                (company_id, created_by_user_id, session_id, response_snapshot, evidence_refs)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb)
            RETURNING *
            """,
            company_id,
            created_by_user_id,
            session_id,
            json.dumps(response_snapshot, ensure_ascii=False),
            json.dumps(evidence_refs, ensure_ascii=False),
        )
        return _row_to_receipt(row)

    async def get_by_id(self, *, company_id: UUID, receipt_id: UUID) -> ReasoningReceipt | None:
        """Return one receipt by id, scoped to company_id.

        A receipt belonging to another company resolves to None,
        identically to a receipt that does not exist at all - the two
        cases are never distinguishable from this method's result
        (Founder Correction 3).
        """
        row = await self.db.fetchrow(
            "SELECT * FROM ome_reasoning_receipts WHERE id = $1 AND company_id = $2",
            receipt_id,
            company_id,
        )
        return _row_to_receipt(row) if row is not None else None
