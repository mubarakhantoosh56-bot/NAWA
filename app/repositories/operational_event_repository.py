"""Repository for NAWA Live Operational Timeline events."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg

RowDict = dict[str, Any]


class OperationalEventRepository:
    """Database access for tenant-scoped operational timeline events."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def create_event(
        self,
        *,
        company_id: UUID,
        created_by_user_id: UUID,
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
    ) -> RowDict:
        """Insert one operational event scoped to a company."""
        row = await self.db.fetchrow(
            """
            INSERT INTO operational_events (
                company_id,
                department_id,
                created_by_user_id,
                event_type,
                category,
                priority,
                title,
                summary,
                event_timestamp,
                source_type,
                source_ref,
                payload,
                metadata
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                COALESCE($9, NOW()), $10, $11, $12::jsonb, $13::jsonb
            )
            RETURNING *
            """,
            company_id,
            department_id,
            created_by_user_id,
            event_type,
            category,
            priority,
            title,
            summary,
            event_timestamp,
            source_type,
            source_ref,
            json.dumps(payload or {}, ensure_ascii=False),
            json.dumps(metadata or {}, ensure_ascii=False),
        )
        return _row_to_dict(row)

    async def list_events(
        self,
        *,
        company_id: UUID,
        department_id: UUID | None = None,
        category: str | None = None,
        priority: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RowDict]:
        """Return operational events for one company with optional filters."""
        query = """
            SELECT *
            FROM operational_events
            WHERE company_id = $1
              AND deleted_at IS NULL
        """
        values: list[Any] = [company_id]

        if department_id is not None:
            values.append(department_id)
            query += f"\n              AND department_id = ${len(values)}"
        if category is not None:
            values.append(category)
            query += f"\n              AND category = ${len(values)}"
        if priority is not None:
            values.append(priority)
            query += f"\n              AND priority = ${len(values)}"

        values.extend([limit, offset])
        query += f"""
            ORDER BY event_timestamp DESC, created_at DESC
            LIMIT ${len(values) - 1}
            OFFSET ${len(values)}
        """

        rows = await self.db.fetch(query, *values)
        return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: asyncpg.Record) -> RowDict:
    result = dict(row)
    for key in ("payload", "metadata"):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = json.loads(value)
    return result
