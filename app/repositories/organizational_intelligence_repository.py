"""Repository for NAWA organizational intelligence context."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import asyncpg

RowDict = dict[str, Any]


class OrganizationalIntelligenceRepository:
    """Reads tenant-scoped organizational structure and relationship data."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        self.db = db

    async def get_snapshot(self, *, company_id: UUID, user_id: UUID | None = None) -> dict[str, Any]:
        """Return a compact organization snapshot. Missing MVP tables degrade to empty lists."""
        try:
            divisions = await self._fetch(
                """
                SELECT id, parent_division_id, name, slug, division_type, description, metadata
                FROM company_divisions
                WHERE company_id = $1
                  AND deleted_at IS NULL
                ORDER BY parent_division_id NULLS FIRST, name ASC
                """,
                company_id,
            )
            units = await self._fetch(
                """
                SELECT id, division_id, department_id, name, unit_type, location, capacity_label, metadata
                FROM operational_units
                WHERE company_id = $1
                  AND deleted_at IS NULL
                ORDER BY name ASC
                """,
                company_id,
            )
            relationships = await self._fetch(
                """
                SELECT
                    source_department_key,
                    target_department_key,
                    relationship_type,
                    dependency_direction,
                    description,
                    strength,
                    risk_if_broken,
                    metadata
                FROM department_relationships
                WHERE company_id = $1
                  AND deleted_at IS NULL
                ORDER BY strength DESC, source_department_key ASC
                """,
                company_id,
            )
            workflows = await self._fetch(
                """
                SELECT
                    id,
                    division_id,
                    owning_department_id,
                    name,
                    workflow_type,
                    description,
                    trigger_source,
                    input_sources,
                    kpi_keys,
                    status,
                    metadata
                FROM operational_workflows
                WHERE company_id = $1
                  AND deleted_at IS NULL
                ORDER BY name ASC
                """,
                company_id,
            )
            kpis = await self._fetch(
                """
                SELECT
                    division_id,
                    department_id,
                    user_id,
                    workflow_id,
                    kpi_key,
                    kpi_label,
                    ownership_type,
                    target_label,
                    cadence,
                    metadata
                FROM kpi_ownerships
                WHERE company_id = $1
                  AND deleted_at IS NULL
                ORDER BY kpi_label ASC
                """,
                company_id,
            )
            integrations = await self._fetch(
                """
                SELECT provider_key, provider_type, source_system, status, native_fallback_enabled, sync_mode, mapped_entities, metadata
                FROM integration_sources
                WHERE company_id = $1
                  AND deleted_at IS NULL
                ORDER BY provider_type ASC, provider_key ASC
                """,
                company_id,
            )
            user_profile = await self._fetch_user_profile(company_id=company_id, user_id=user_id)
        except asyncpg.UndefinedTableError:
            return _empty_snapshot()

        return {
            "divisions": divisions,
            "operational_units": units,
            "department_relationships": relationships,
            "operational_workflows": workflows,
            "kpi_ownerships": kpis,
            "integration_sources": integrations,
            "current_user_profile": user_profile,
        }

    async def _fetch(self, query: str, *args: Any) -> list[RowDict]:
        rows = await self.db.fetch(query, *args)
        return [_row_to_dict(row) for row in rows]

    async def _fetch_user_profile(self, *, company_id: UUID, user_id: UUID | None) -> RowDict | None:
        if user_id is None:
            return None
        row = await self.db.fetchrow(
            """
            SELECT
                user_id,
                role_id,
                department_id,
                division_id,
                operational_impact,
                kpi_ownership,
                related_workflows,
                issues_history,
                activity_summary,
                metadata
            FROM user_operational_profiles
            WHERE company_id = $1
              AND user_id = $2
              AND deleted_at IS NULL
            LIMIT 1
            """,
            company_id,
            user_id,
        )
        return _optional_row_to_dict(row)


def _empty_snapshot() -> dict[str, Any]:
    return {
        "divisions": [],
        "operational_units": [],
        "department_relationships": [],
        "operational_workflows": [],
        "kpi_ownerships": [],
        "integration_sources": [],
        "current_user_profile": None,
    }


def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
    if row is None:
        return None
    return _row_to_dict(row)


def _row_to_dict(row: asyncpg.Record) -> RowDict:
    result = dict(row)
    for key in (
        "metadata",
        "input_sources",
        "kpi_keys",
        "mapped_entities",
        "kpi_ownership",
        "related_workflows",
        "issues_history",
        "activity_summary",
    ):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = json.loads(value)
    return result
