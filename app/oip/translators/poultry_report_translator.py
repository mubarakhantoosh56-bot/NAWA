"""Translator for Dairtna daily technical poultry Excel reports."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.oip.loaders.excel_loader import ExcelSheet
from app.oip.models.operational_record import PoultryOperationalRecord


ARABIC_COLUMN_MAP: dict[str, str] = {
    "التاريخ": "date",
    "اليوم": "day_name",
    "العمر بالأسبوع": "age_week",
    "العمر بالاسبوع": "age_week",
    "العمر باليوم": "age_day",
    "رصيد الطيور": "bird_balance",
    "الهلاكات اليومية": "daily_mortality",
    "الهلاكات الأسبوعية": "weekly_mortality",
    "الهلاكات الاسبوعية": "weekly_mortality",
    "نسبة الهلاكات الأسبوعية": "weekly_mortality_rate",
    "نسبة الهلاكات الاسبوعية": "weekly_mortality_rate",
    "الإنتاج اليومي بالطبق": "daily_tray_production",
    "الانتاج اليومي بالطبق": "daily_tray_production",
    "الإنتاج بالصندوق": "box_production",
    "الانتاج بالصندوق": "box_production",
    "نسبة الإنتاج اليومية": "daily_production_rate",
    "نسبة الانتاج اليومية": "daily_production_rate",
    "نسبة الإنتاج القياسية": "standard_production_rate",
    "نسبة الانتاج القياسية": "standard_production_rate",
    "كسر": "broken_eggs",
    "متسخ": "dirty_eggs",
    "الأشر": "unknown_marker_field",
    "\u0627\u0644\u0645\u0627\u0621 \u0627\u0644\u0645\u0633\u062a\u0647\u0644\u0643": "water_consumption",
}

INTEGER_FIELDS = {
    "age_week",
    "age_day",
    "bird_balance",
    "daily_mortality",
    "weekly_mortality",
    "daily_tray_production",
    "box_production",
    "broken_eggs",
    "dirty_eggs",
    "water_consumption",
}
PERCENT_FIELDS = {
    "weekly_mortality_rate",
    "daily_production_rate",
    "standard_production_rate",
}


class PoultryReportTranslator:
    """Translate Arabic daily technical poultry report rows into NAWA fields."""

    def translate(
        self,
        sheets: list[ExcelSheet],
        source_file: str | Path,
    ) -> list[PoultryOperationalRecord]:
        """Translate all parseable rows from workbook sheets."""
        records: list[PoultryOperationalRecord] = []
        for sheet in sheets:
            records.extend(self._translate_sheet(sheet, Path(source_file)))
        return records

    def _translate_sheet(
        self,
        sheet: ExcelSheet,
        source_file: Path,
    ) -> list[PoultryOperationalRecord]:
        header_index, headers = self._find_header_row(sheet.rows)
        if header_index is None:
            return []

        records: list[PoultryOperationalRecord] = []
        for row_offset, row in enumerate(sheet.rows[header_index + 1 :], start=header_index + 2):
            raw_values = self._row_to_raw_values(headers, row)
            if not self._has_record_content(raw_values):
                continue

            translated: dict[str, Any] = {}
            for arabic_header, value in raw_values.items():
                internal_name = ARABIC_COLUMN_MAP.get(_normalize_header(arabic_header))
                if internal_name is None:
                    continue
                translated[internal_name] = self._coerce_value(internal_name, value)

            if not any(key in translated for key in ("date", "bird_balance", "daily_mortality")):
                continue

            records.append(
                PoultryOperationalRecord(
                    date=translated.get("date"),
                    day_name=translated.get("day_name"),
                    age_week=translated.get("age_week"),
                    age_day=translated.get("age_day"),
                    bird_balance=translated.get("bird_balance"),
                    daily_mortality=translated.get("daily_mortality"),
                    weekly_mortality=translated.get("weekly_mortality"),
                    weekly_mortality_rate=translated.get("weekly_mortality_rate"),
                    daily_tray_production=translated.get("daily_tray_production"),
                    box_production=translated.get("box_production"),
                    daily_production_rate=translated.get("daily_production_rate"),
                    standard_production_rate=translated.get("standard_production_rate"),
                    broken_eggs=translated.get("broken_eggs"),
                    dirty_eggs=translated.get("dirty_eggs"),
                    water_consumption=translated.get("water_consumption"),
                    unknown_marker_field=translated.get("unknown_marker_field"),
                    source_file=str(source_file),
                    sheet_name=sheet.name,
                    row_number=row_offset,
                    raw_values=raw_values,
                )
            )
        return records

    def _find_header_row(
        self,
        rows: list[tuple[Any, ...]],
    ) -> tuple[int | None, list[str]]:
        for index, row in enumerate(rows):
            headers = [str(value).strip() if value is not None else "" for value in row]
            normalized = {_normalize_header(header) for header in headers if header}
            if {"التاريخ", "رصيد الطيور"}.issubset(normalized):
                return index, headers
        return None, []

    def _row_to_raw_values(self, headers: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for header, value in zip(headers, row):
            if not header:
                continue
            values[header] = value
        return values

    def _has_record_content(self, raw_values: dict[str, Any]) -> bool:
        return any(value not in (None, "") for value in raw_values.values())

    def _coerce_value(self, field_name: str, value: Any) -> Any:
        if value in (None, ""):
            return None
        if field_name == "date":
            return _parse_date(value)
        if field_name in INTEGER_FIELDS:
            return _parse_int(value)
        if field_name in PERCENT_FIELDS:
            return _parse_percent(value)
        if isinstance(value, str):
            return value.strip()
        return value


def _normalize_header(header: str) -> str:
    return " ".join(header.replace("%", "").strip().split())


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    return None


def _parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if text.endswith(".0"):
            text = text[:-2]
        return int(text)
    return int(value)


def _parse_percent(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return float(value.strip().replace("%", "").replace(",", ""))
    return float(value)
