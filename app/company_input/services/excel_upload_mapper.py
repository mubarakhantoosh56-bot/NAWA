"""Mapper from Excel upload metadata to CompanyInput."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from app.company_input.models import CompanyInput


def map_excel_upload_to_company_input(
    *,
    company_id: UUID,
    user_id: UUID | None,
    source_path: str | Path,
    original_filename: str,
    department_id: UUID | None = None,
    mime_type: str | None = None,
    language: str | None = None,
    confidence: str = "high",
    received_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> CompanyInput:
    """Create CompanyInput metadata for an uploaded Excel file.

    This mapper does not route the input or invoke NAWA engines. It only wraps
    upload metadata in the canonical intake contract.
    """
    source = Path(source_path)
    return CompanyInput(
        company_id=company_id,
        department_id=department_id,
        user_id=user_id,
        source="upload",
        source_type="excel_upload",
        media_type="file",
        mime_type=mime_type
        or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        original_filename=original_filename,
        language=language,
        confidence=confidence,
        raw_storage_path=str(source),
        received_at=received_at or datetime.now(timezone.utc),
        metadata={
            "extension": Path(original_filename).suffix.lower(),
            **(metadata or {}),
        },
    )
