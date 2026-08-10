"""Translator for the Feed Mill raw-material inventory snapshot block.

Per the Founder Business Semantics Ruling - M3, only the specific
"رصيد الجاروشة" (feed mill balance) block is approved for structured
ingestion. Detection is shape/label-based (never sheet-name or
filename-based), so other sheets in the same workbook - and other blocks in
the same sheet, such as "يومي العلف"'s "الرصيد الحالي" row - are never
force-fit into this shape.

Codex Round 1 Finding 2 hardening: a material header, a balance row, and an
optional days-coverage row are only combined into one record set when they
form ONE coherent, bounded, column-aligned block - not merely because each
label independently occurs somewhere in the sheet. False structured
ingestion is treated as worse than rejection.

Codex Round 2 Finding 1 hardening: report_date is promoted only from an
explicit ALLOWLIST of snapshot/report-date labels
(AUTHORITATIVE_DATE_LABELS) - a generic "تاريخ" substring is no longer
sufficient, since receipt/update/entry/last-supply/transaction/issue dates
are semantically different from the inventory snapshot date and must never
be promoted.

Codex Round 2 Finding 2 hardening: a column is only promoted to a material
identity when its header is not a known non-material term (totals/notes/
entered-by) AND its balance-row cell holds a valid numeric value. A header
present with a missing/non-numeric balance value produces no record for that
column, rather than a false raw-material row.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.oip.loaders.excel_loader import ExcelSheet
from app.oip.models.feed_mill_inventory_record import FeedMillInventoryRecord

REPORT_SHAPE = "feed_mill_raw_material_inventory_snapshot"
ENTITY_TYPE = "feed_mill"

MATERIAL_HEADER_LABEL = "الصنف"
BALANCE_ROW_LABEL = "رصيد الجاروشة"
DAYS_COVERAGE_ROW_LABEL = "الكمية تكفي/يوم"

# Explicit allowlist of labels that are semantically the inventory
# snapshot/report date itself - never a receipt/update/entry/last-supply/
# transaction/issue date, which are different business events. Only labels
# defensible from source semantics we can name are included; nothing is
# inferred by generic "تاريخ" substring matching.
AUTHORITATIVE_DATE_LABELS = {
    "تاريخ التقرير",
    "تاريخ الجرد",
    "تاريخ الرصيد",
}

# Column header terms that are never a material identity, even when a
# numeric value happens to sit beneath them (e.g. a totals column).
NON_MATERIAL_HEADER_TERMS = {
    "الإجمالي",
    "الاجمالي",
    "المجموع",
    "ملاحظات",
    "الملاحظات",
    "ملاحظة",
    "أدخل بواسطة",
    "ادخل بواسطة",
    "تم الإدخال بواسطة",
    "تم الادخال بواسطة",
    "المدخل",
}

# A balance/coverage row must be found within this many rows of its material
# header (and coverage within this many rows of its balance row) to count as
# part of the SAME block. This keeps the block bounded and contiguous rather
# than scanning the whole sheet, so a same-labeled row belonging to an
# unrelated section cannot be cross-matched. The real workbook's block has a
# balance row 2 rows after the material header and a coverage row 2 rows
# after that; this bound leaves comfortable margin without being unbounded.
MAX_BLOCK_GAP = 6

REPORT_DATE_AUTHORITATIVE = "authoritative"
REPORT_DATE_UNRESOLVED = "unresolved"


class FeedMillInventoryTranslator:
    """Translate the feed mill raw-material inventory snapshot block."""

    def translate(
        self,
        sheets: list[ExcelSheet],
        source_file: str | Path,
    ) -> list[FeedMillInventoryRecord]:
        """Translate the approved inventory block from any matching sheet."""
        records: list[FeedMillInventoryRecord] = []
        for sheet in sheets:
            records.extend(self._translate_sheet(sheet, Path(source_file)))
        return records

    def _translate_sheet(
        self,
        sheet: ExcelSheet,
        source_file: Path,
    ) -> list[FeedMillInventoryRecord]:
        rows = sheet.rows
        records: list[FeedMillInventoryRecord] = []
        consumed_balance_rows: set[int] = set()

        for header_row_index, header_col_index in self._find_all_label_positions(
            rows, MATERIAL_HEADER_LABEL
        ):
            candidate_columns = self._candidate_material_columns(
                rows[header_row_index], header_col_index
            )
            if not candidate_columns:
                continue

            balance_match = self._find_nearest_labeled_row(
                rows,
                BALANCE_ROW_LABEL,
                start=header_row_index + 1,
                end=header_row_index + MAX_BLOCK_GAP,
                required_column=header_col_index,
            )
            if balance_match is None:
                continue
            balance_row_index, _ = balance_match
            if balance_row_index in consumed_balance_rows:
                continue

            balance_row = rows[balance_row_index]
            # Codex Round 2 Finding 2: a column is only a material when the
            # balance row actually holds a valid numeric value for it - a
            # present header with a missing/non-numeric value is omitted
            # rather than emitted as a false raw-material record.
            material_columns = {
                column_index: material_name
                for column_index, material_name in candidate_columns.items()
                if column_index < len(balance_row)
                and _parse_float(balance_row[column_index]) is not None
            }
            if not material_columns:
                continue
            consumed_balance_rows.add(balance_row_index)

            coverage_match = self._find_nearest_labeled_row(
                rows,
                DAYS_COVERAGE_ROW_LABEL,
                start=balance_row_index + 1,
                end=balance_row_index + MAX_BLOCK_GAP,
                required_column=header_col_index,
            )
            coverage_row_index = coverage_match[0] if coverage_match else None
            coverage_row = rows[coverage_row_index] if coverage_row_index is not None else None

            block_end = coverage_row_index if coverage_row_index is not None else balance_row_index
            report_date, date_status, date_candidates = self._resolve_report_date(
                rows, header_row_index, block_end
            )
            warnings: tuple[str, ...] = ()
            if date_status == REPORT_DATE_UNRESOLVED:
                warnings = (
                    (
                        f"report_date_not_authoritative: {len(date_candidates)} "
                        "candidate date(s) found in block, none paired with an "
                        "approved snapshot/report-date label "
                        f"({sorted(AUTHORITATIVE_DATE_LABELS)})"
                    )
                    if date_candidates
                    else "report_date_absent: no date value found in the block"
                ,)

            row_range = (
                f"{header_row_index + 1}-{coverage_row_index + 1}"
                if coverage_row_index is not None
                else f"{header_row_index + 1}-{balance_row_index + 1}"
            )

            for column_index, material_name in material_columns.items():
                balance_value = balance_row[column_index]
                coverage_value = (
                    coverage_row[column_index]
                    if coverage_row is not None and column_index < len(coverage_row)
                    else None
                )
                records.append(
                    FeedMillInventoryRecord(
                        material_name=material_name,
                        raw_material_inventory=_parse_float(balance_value),
                        source_reported_days_coverage=_parse_float(coverage_value),
                        report_date=report_date,
                        source_file=str(source_file),
                        sheet_name=sheet.name,
                        row_number=balance_row_index + 1,
                        entity_type=ENTITY_TYPE,
                        entity_reference=None,
                        report_shape=REPORT_SHAPE,
                        report_date_status=date_status,
                        provenance_warnings=warnings,
                        epistemic_origin="observed",
                        raw_values={
                            "material_header_label": MATERIAL_HEADER_LABEL,
                            "material_name": material_name,
                            "balance_row_label": BALANCE_ROW_LABEL,
                            "balance_value": balance_value,
                            "coverage_row_label": (
                                DAYS_COVERAGE_ROW_LABEL if coverage_row is not None else None
                            ),
                            "coverage_value": coverage_value,
                            "row_range": row_range,
                            "date_candidates": [
                                {
                                    "label": label,
                                    "date": candidate.isoformat(),
                                }
                                for label, candidate in date_candidates
                            ],
                        },
                    )
                )
        return records

    def _find_all_label_positions(
        self,
        rows: list[tuple[Any, ...]],
        label: str,
    ) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                if value is not None and _normalize(str(value)) == label:
                    positions.append((row_index, col_index))
        return positions

    def _find_nearest_labeled_row(
        self,
        rows: list[tuple[Any, ...]],
        label: str,
        start: int,
        end: int,
        required_column: int,
    ) -> tuple[int, int] | None:
        """Find the nearest row in [start, end] whose label sits at the SAME
        column as the material header's label column (Codex Round 1 Finding
        2: compatible column alignment), not merely anywhere in the row.
        """
        bounded_end = min(end, len(rows) - 1)
        for row_index in range(max(start, 0), bounded_end + 1):
            row = rows[row_index]
            if required_column >= len(row):
                continue
            value = row[required_column]
            if value is not None and _normalize(str(value)) == label:
                return row_index, required_column
        return None

    def _candidate_material_columns(
        self,
        header_row: tuple[Any, ...],
        label_index: int,
    ) -> dict[int, str]:
        """Columns to the right of الصنف with a non-empty, non-metadata label.

        This is only a CANDIDATE set - Codex Round 2 Finding 2 additionally
        requires each candidate to have a valid numeric balance-row value
        before it is treated as a real material column; that check happens
        in the caller once the balance row is known.
        """
        columns: dict[int, str] = {}
        for index in range(label_index + 1, len(header_row)):
            value = header_row[index]
            if value is None or not str(value).strip():
                continue
            text = str(value).strip()
            if _normalize(text) in NON_MATERIAL_HEADER_TERMS:
                continue
            columns[index] = text
        return columns

    def _resolve_report_date(
        self,
        rows: list[tuple[Any, ...]],
        start: int,
        end: int,
    ) -> tuple[date | None, str, list[tuple[str, date]]]:
        """Resolve report_date using ONLY an allowlisted authoritative label.

        Codex Round 2 Finding 1: a date is promoted to canonical report_date
        only when it is paired with a label that is explicitly allowlisted
        as the inventory snapshot/report date itself
        (AUTHORITATIVE_DATE_LABELS) - a generic "تاريخ" substring is not
        enough, since labels such as "تاريخ الاستلام" (receipt),
        "تاريخ التحديث" (update), "تاريخ الإدخال" (entry), "تاريخ آخر توريد"
        (last supply), "تاريخ الحركة" (transaction), or "تاريخ الصرف"
        (issue) refer to different business events, not the snapshot date.
        Every other labeled-or-unlabeled date found in the block is
        preserved only as a provenance candidate, never promoted.
        """
        candidates: list[tuple[str, date]] = []
        authoritative: date | None = None
        for row_index in range(start, min(end, len(rows) - 1) + 1):
            row = rows[row_index]
            consumed_columns: set[int] = set()

            # Pass 1: label -> value pairs (a string cell immediately
            # followed by a date cell). The value's column is marked
            # consumed so pass 2 never double-counts it as unlabeled.
            for col_index, value in enumerate(row):
                if not isinstance(value, str) or col_index + 1 >= len(row):
                    continue
                parsed = _as_date(row[col_index + 1])
                if parsed is None:
                    continue
                consumed_columns.add(col_index + 1)
                if _normalize(value) in AUTHORITATIVE_DATE_LABELS:
                    if authoritative is None:
                        authoritative = parsed
                else:
                    candidates.append((value.strip(), parsed))

            # Pass 2: any remaining date cell not already paired with a label.
            for col_index, value in enumerate(row):
                if col_index in consumed_columns:
                    continue
                parsed_unlabeled = _as_date(value)
                if parsed_unlabeled is not None:
                    candidates.append(("unlabeled", parsed_unlabeled))

        if authoritative is not None:
            return authoritative, REPORT_DATE_AUTHORITATIVE, []
        return None, REPORT_DATE_UNRESOLVED, candidates


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        try:
            return float(text)
        except ValueError:
            return None
    return None
