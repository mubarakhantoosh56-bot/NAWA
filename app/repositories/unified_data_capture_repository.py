"""Repository for NAWA unified data capture records."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import asyncpg

RowDict = dict[str, Any]


class UnifiedDataCaptureRepository:
    """Database access for raw inputs, parsed entities, classifications, and drafts."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        self.db = db

    async def create_raw_input(
        self,
        *,
        company_id: UUID,
        created_by: UUID,
        source_type: str,
        raw_content: str,
        division_id: UUID | None = None,
        department_id: UUID | None = None,
        source_ref: str | None = None,
        file_id: UUID | None = None,
        processing_status: str = "pending",
        language: str | None = None,
    ) -> RowDict:
        row = await self.db.fetchrow(
            """
            INSERT INTO raw_inputs (
                company_id,
                division_id,
                department_id,
                source_type,
                source_ref,
                raw_content,
                file_id,
                created_by,
                processing_status,
                language
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            RETURNING *
            """,
            company_id,
            division_id,
            department_id,
            source_type,
            source_ref,
            raw_content,
            file_id,
            created_by,
            processing_status,
            language,
        )
        return _row_to_dict(row)

    async def update_raw_input_status(
        self,
        *,
        company_id: UUID,
        raw_input_id: UUID,
        processing_status: str,
        language: str | None = None,
    ) -> RowDict | None:
        row = await self.db.fetchrow(
            """
            UPDATE raw_inputs
            SET
                processing_status = $3,
                language = COALESCE($4, language)
            WHERE company_id = $1
              AND id = $2
            RETURNING *
            """,
            company_id,
            raw_input_id,
            processing_status,
            language,
        )
        return _optional_row_to_dict(row)

    async def create_entities(
        self,
        *,
        raw_input_id: UUID,
        entities: list[dict[str, Any]],
    ) -> list[RowDict]:
        if not entities:
            return []

        rows: list[asyncpg.Record] = []
        if hasattr(self.db, "acquire"):
            async with self.db.acquire() as conn:
                for entity in entities:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO parsed_entities (
                            raw_input_id,
                            entity_type,
                            entity_value,
                            confidence,
                            metadata
                        )
                        VALUES ($1,$2,$3,$4,$5::jsonb)
                        RETURNING *
                        """,
                        raw_input_id,
                        entity["entity_type"],
                        entity["entity_value"],
                        int(entity.get("confidence") or 0),
                        json.dumps(entity.get("metadata") or {}, ensure_ascii=False),
                    )
                    rows.append(row)
            return [_row_to_dict(row) for row in rows]

        for entity in entities:
            row = await self.db.fetchrow(
                """
                INSERT INTO parsed_entities (
                    raw_input_id,
                    entity_type,
                    entity_value,
                    confidence,
                    metadata
                )
                VALUES ($1,$2,$3,$4,$5::jsonb)
                RETURNING *
                """,
                raw_input_id,
                entity["entity_type"],
                entity["entity_value"],
                int(entity.get("confidence") or 0),
                json.dumps(entity.get("metadata") or {}, ensure_ascii=False),
            )
            rows.append(row)
        return [_row_to_dict(row) for row in rows]

    async def create_classification(
        self,
        *,
        raw_input_id: UUID,
        classification: dict[str, Any],
    ) -> RowDict:
        row = await self.db.fetchrow(
            """
            INSERT INTO parsed_classifications (
                raw_input_id,
                inferred_department,
                inferred_division,
                category,
                priority,
                severity,
                related_departments,
                operational_signal,
                confidence,
                metadata
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9,$10::jsonb)
            ON CONFLICT (raw_input_id)
            DO UPDATE SET
                inferred_department = EXCLUDED.inferred_department,
                inferred_division = EXCLUDED.inferred_division,
                category = EXCLUDED.category,
                priority = EXCLUDED.priority,
                severity = EXCLUDED.severity,
                related_departments = EXCLUDED.related_departments,
                operational_signal = EXCLUDED.operational_signal,
                confidence = EXCLUDED.confidence,
                metadata = EXCLUDED.metadata
            RETURNING *
            """,
            raw_input_id,
            classification.get("inferred_department"),
            classification.get("inferred_division"),
            classification["category"],
            classification["priority"],
            classification["severity"],
            json.dumps(classification.get("related_departments") or [], ensure_ascii=False),
            classification["operational_signal"],
            int(classification.get("confidence") or 0),
            json.dumps(classification.get("metadata") or {}, ensure_ascii=False),
        )
        return _row_to_dict(row)

    async def create_structured_record_draft(
        self,
        *,
        company_id: UUID,
        raw_input_id: UUID,
        created_by: UUID,
        record_type: str,
        extracted_payload: dict[str, Any],
        division_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> RowDict:
        row = await self.db.fetchrow(
            """
            INSERT INTO structured_record_drafts (
                company_id,
                raw_input_id,
                division_id,
                department_id,
                record_type,
                extracted_payload,
                status,
                created_by
            )
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,'draft',$7)
            RETURNING *
            """,
            company_id,
            raw_input_id,
            division_id,
            department_id,
            record_type,
            json.dumps(extracted_payload, ensure_ascii=False),
            created_by,
        )
        return _row_to_dict(row)

    async def get_debug_snapshot(
        self,
        *,
        company_id: UUID,
        raw_input_id: UUID,
    ) -> dict[str, Any] | None:
        raw_input = await self.db.fetchrow(
            """
            SELECT *
            FROM raw_inputs
            WHERE company_id = $1
              AND id = $2
            LIMIT 1
            """,
            company_id,
            raw_input_id,
        )
        if raw_input is None:
            return None

        entities = await self.db.fetch(
            """
            SELECT *
            FROM parsed_entities
            WHERE raw_input_id = $1
            ORDER BY created_at ASC
            """,
            raw_input_id,
        )
        classification = await self.db.fetchrow(
            """
            SELECT *
            FROM parsed_classifications
            WHERE raw_input_id = $1
            LIMIT 1
            """,
            raw_input_id,
        )
        draft = await self.db.fetchrow(
            """
            SELECT *
            FROM structured_record_drafts
            WHERE company_id = $1
              AND raw_input_id = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            company_id,
            raw_input_id,
        )
        event = await self.db.fetchrow(
            """
            SELECT created_at, event_type, user_message, executive_summary, logic_json, context
            FROM memory_events
            WHERE company_id = $1
              AND context ->> 'raw_input_id' = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            str(company_id),
            str(raw_input_id),
        )
        return {
            "raw_input": _row_to_dict(raw_input),
            "parsed_entities": [_row_to_dict(row) for row in entities],
            "classification": _optional_row_to_dict(classification),
            "structured_draft": _optional_row_to_dict(draft),
            "operational_event": _optional_row_to_dict(event),
        }


def _optional_row_to_dict(row: asyncpg.Record | None) -> RowDict | None:
    if row is None:
        return None
    return _row_to_dict(row)


def _row_to_dict(row: asyncpg.Record) -> RowDict:
    result = dict(row)
    for key, value in list(result.items()):
        if isinstance(value, str) and key in {"metadata", "related_departments", "extracted_payload", "logic_json", "context"}:
            result[key] = json.loads(value)
    return result
