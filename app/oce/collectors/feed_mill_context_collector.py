"""Local feed mill context collection for OCE."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from app.oce.models.evidence import Evidence

REQUESTED_FEED_MILL_PATH = (
    Path("data_sources")
    / "jannat_al_firdaws"
    / "2026_06"
    / "feed_mill"
    / "جرد_المواد_بالجاروشة.xlsx"
)
FEED_MILL_DIR = REQUESTED_FEED_MILL_PATH.parent
FEED_MATERIAL_TERMS = (
    "علف",
    "ذرة",
    "الصويا",
    "نخالة",
    "بريمكس",
    "مثيونين",
    "ملح",
    "corn",
    "soya",
    "soybean",
    "bran",
    "premix",
    "feed",
    "salt",
)


@dataclass(frozen=True)
class FeedMillWorkbookSummary:
    """Basic local summary of a feed mill workbook."""

    path: Path
    sheet_names: list[str]
    detected_columns: list[str]
    row_count: int
    feed_related_row_count: int


class FeedMillContextCollector:
    """Collect local feed mill workbook evidence for operational context."""

    def collect_evidence(
        self,
        date_range: tuple[Any, Any],
    ) -> Evidence | None:
        """Return available feed mill inventory evidence when a workbook can be read."""
        workbook_path = self._resolve_workbook_path()
        if workbook_path is None:
            return None

        try:
            summary = self._summarize_workbook(workbook_path)
        except Exception:
            return None

        description = (
            "Feed mill inventory workbook is available and readable. "
            f"Sheets: {', '.join(summary.sheet_names)}. "
            f"Detected columns/material labels: {', '.join(summary.detected_columns[:12])}. "
            f"Non-empty row count: {summary.row_count}. "
            f"Feed/material-related rows detected: {summary.feed_related_row_count}."
        )
        return Evidence(
            source=summary.path.as_posix(),
            type="feed_mill_inventory",
            status="available",
            description=description,
            date_range=date_range,
        )

    def _resolve_workbook_path(self) -> Path | None:
        if REQUESTED_FEED_MILL_PATH.exists():
            return REQUESTED_FEED_MILL_PATH
        if not FEED_MILL_DIR.exists():
            return None
        candidates = sorted(FEED_MILL_DIR.glob("*.xlsx"))
        return candidates[0] if candidates else None

    def _summarize_workbook(self, path: Path) -> FeedMillWorkbookSummary:
        workbook = load_workbook(io.BytesIO(path.read_bytes()), read_only=True, data_only=True)
        try:
            sheet_names = list(workbook.sheetnames)
            detected_columns: list[str] = []
            row_count = 0
            feed_related_row_count = 0
            for worksheet in workbook.worksheets:
                for row in worksheet.iter_rows(values_only=True):
                    values = [self._normalize_cell(value) for value in row]
                    non_empty = [value for value in values if value]
                    if not non_empty:
                        continue
                    row_count += 1
                    if self._looks_like_header(non_empty):
                        detected_columns.extend(non_empty)
                    if self._has_feed_material_term(non_empty):
                        feed_related_row_count += 1

            return FeedMillWorkbookSummary(
                path=path,
                sheet_names=sheet_names,
                detected_columns=self._dedupe(detected_columns),
                row_count=row_count,
                feed_related_row_count=feed_related_row_count,
            )
        finally:
            workbook.close()

    def _normalize_cell(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _looks_like_header(self, values: list[str]) -> bool:
        material_hits = sum(1 for value in values if self._has_feed_material_term([value]))
        return material_hits >= 2

    def _has_feed_material_term(self, values: list[str]) -> bool:
        text = " ".join(values).lower()
        return any(term.lower() in text for term in FEED_MATERIAL_TERMS)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique.append(value)
        return unique
