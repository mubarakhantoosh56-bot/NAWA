"""Repository for NAWA operational situations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg

RowDict = dict[str, Any]


class OperationalSituationRepository:
    """Database access for tenant-scoped operational situations."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the repository with an asyncpg connection or pool."""
        self.db = db

    async def list_recent_events_for_grouping(
        self,
        *,
        company_id: UUID,
        since: datetime,
        limit: int = 500,
    ) -> list[RowDict]:
        """Return recent operational events for one company."""
        rows = await self.db.fetch(
            """
            SELECT *
            FROM operational_events
            WHERE company_id = $1
              AND event_timestamp >= $2
              AND deleted_at IS NULL
            ORDER BY event_timestamp ASC, created_at ASC
            LIMIT $3
            """,
            company_id,
            since,
            limit,
        )
        return [_row_to_dict(row) for row in rows]

    async def create_situation(
        self,
        *,
        company_id: UUID,
        title: str,
        summary: str,
        situation_type: str,
        severity: str,
        status: str,
        time_window_start: datetime,
        time_window_end: datetime,
        department_id: UUID | None,
        detection_method: str,
        source_type: str,
    ) -> RowDict:
        """Insert one operational situation scoped to a company."""
        row = await self.db.fetchrow(
            """
            INSERT INTO operational_situations (
                company_id,
                title,
                summary,
                situation_type,
                severity,
                status,
                time_window_start,
                time_window_end,
                department_id,
                detection_method,
                source_type
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
            """,
            company_id,
            title,
            summary,
            situation_type,
            severity,
            status,
            time_window_start,
            time_window_end,
            department_id,
            detection_method,
            source_type,
        )
        return _row_to_dict(row)

    async def link_situation_events(
        self,
        *,
        company_id: UUID,
        situation_id: UUID,
        event_links: list[dict[str, object]],
    ) -> None:
        """Link operational events to one situation."""
        for link in event_links:
            await self.db.execute(
                """
                INSERT INTO situation_events (
                    company_id,
                    situation_id,
                    event_id,
                    role
                )
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (company_id, situation_id, event_id) DO NOTHING
                """,
                company_id,
                situation_id,
                link["event_id"],
                link.get("role"),
            )

    async def find_active_situations_for_events(
        self,
        *,
        company_id: UUID,
        event_ids: list[UUID],
    ) -> list[RowDict]:
        """Return active or monitoring situations already linked to events."""
        if not event_ids:
            return []

        rows = await self.db.fetch(
            """
            SELECT DISTINCT s.*
            FROM operational_situations s
            JOIN situation_events se
              ON se.company_id = s.company_id
             AND se.situation_id = s.id
            WHERE s.company_id = $1
              AND se.company_id = $1
              AND se.event_id = ANY($2::uuid[])
              AND s.status IN ('active', 'monitoring')
              AND s.deleted_at IS NULL
            ORDER BY s.time_window_end DESC
            """,
            company_id,
            event_ids,
        )
        return [_row_to_dict(row) for row in rows]

    async def list_situations(
        self,
        *,
        company_id: UUID,
        status: str | None = None,
        department_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RowDict]:
        """Return situations for one company with optional filters."""
        query = """
            SELECT
                s.*,
                COUNT(se.id)::integer AS event_count
            FROM operational_situations s
            LEFT JOIN situation_events se
              ON se.company_id = s.company_id
             AND se.situation_id = s.id
            WHERE s.company_id = $1
              AND s.deleted_at IS NULL
        """
        values: list[Any] = [company_id]

        if status is not None:
            values.append(status)
            query += f"\n              AND s.status = ${len(values)}"
        if department_id is not None:
            values.append(department_id)
            query += f"\n              AND s.department_id = ${len(values)}"

        values.extend([limit, offset])
        query += f"""
            GROUP BY s.id
            ORDER BY s.time_window_end DESC, s.created_at DESC
            LIMIT ${len(values) - 1}
            OFFSET ${len(values)}
        """

        rows = await self.db.fetch(query, *values)
        return [_row_to_dict(row) for row in rows]

    async def get_situation(
        self,
        *,
        company_id: UUID,
        situation_id: UUID,
    ) -> RowDict | None:
        """Return one situation by company and situation ID."""
        row = await self.db.fetchrow(
            """
            SELECT
                s.*,
                COUNT(se.id)::integer AS event_count
            FROM operational_situations s
            LEFT JOIN situation_events se
              ON se.company_id = s.company_id
             AND se.situation_id = s.id
            WHERE s.company_id = $1
              AND s.id = $2
              AND s.deleted_at IS NULL
            GROUP BY s.id
            LIMIT 1
            """,
            company_id,
            situation_id,
        )
        if row is None:
            return None
        return _row_to_dict(row)

    async def list_situation_events(
        self,
        *,
        company_id: UUID,
        situation_id: UUID,
    ) -> list[RowDict]:
        """Return linked operational events for one situation."""
        rows = await self.db.fetch(
            """
            SELECT e.*, se.role AS situation_role
            FROM situation_events se
            JOIN operational_events e
              ON e.company_id = se.company_id
             AND e.id = se.event_id
            WHERE se.company_id = $1
              AND se.situation_id = $2
              AND e.deleted_at IS NULL
            ORDER BY e.event_timestamp ASC, e.created_at ASC
            """,
            company_id,
            situation_id,
        )
        return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: asyncpg.Record) -> RowDict:
    result = dict(row)
    for key in ("payload", "metadata"):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = json.loads(value)
    return result
