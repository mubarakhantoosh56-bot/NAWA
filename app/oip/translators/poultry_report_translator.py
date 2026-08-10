"""Translator for Dairtna daily technical poultry Excel reports."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.oip.loaders.excel_loader import ExcelSheet
from app.oip.models.operational_record import PoultryOperationalRecord

# Shape identifiers. Shape is detected from header co-occurrence, never from
# filename (Founder Business Semantics Ruling - M3: "Filename is NOT
# authoritative. Supported ingestion must be detected from report
# shape/business semantics.").
SHAPE_DAILY_TECHNICAL_HALL = "poultry_daily_technical_hall"
SHAPE_DAILY_TECHNICAL_AGGREGATE = "poultry_daily_technical_aggregate"

# Each shape is anchored by a pair of Arabic headers that must co-occur in
# the same row. Family 2 (aggregate) uses different literal header text than
# Family 1 (single hall), so both signatures are checked independently.
SHAPE_HEADER_SIGNATURES: dict[str, tuple[str, str]] = {
    SHAPE_DAILY_TECHNICAL_HALL: ("التاريخ", "رصيد الطيور"),
    SHAPE_DAILY_TECHNICAL_AGGREGATE: ("التاريخ", "إجمالي أعداد الطيور للحقول"),
}

ARABIC_COLUMN_MAP: dict[str, str] = {
    "التاريخ": "date",
    "اليوم": "day_name",
    "العمر بالأسبوع": "age_week",
    "العمر بالاسبوع": "age_week",
    "العمر باليوم": "age_day",
    "رصيد الطيور": "bird_balance",
    "إجمالي أعداد الطيور للحقول": "bird_balance",
    "الهلاكات اليومية": "daily_mortality",
    "إجمالي الهلاكات اليومية": "daily_mortality",
    "الهلاكات الأسبوعية": "weekly_mortality",
    "الهلاكات الاسبوعية": "weekly_mortality",
    "نسبة الهلاكات الأسبوعية": "weekly_mortality_rate",
    "نسبة الهلاكات الاسبوعية": "weekly_mortality_rate",
    "الإنتاج اليومي بالطبق": "daily_tray_production",
    "الانتاج اليومي بالطبق": "daily_tray_production",
    "إجمالي الإنتاج اليومي بالطبق": "daily_tray_production",
    "الإنتاج بالصندوق": "box_production",
    "الانتاج بالصندوق": "box_production",
    "إجمالي الإنتاج (بالصندوق)": "box_production",
    "نسبة الإنتاج اليومية": "daily_production_rate",
    "نسبة الانتاج اليومية": "daily_production_rate",
    "نسبة الإنتاج اليومي للحقول": "daily_production_rate",
    "نسبة الإنتاج القياسية": "standard_production_rate",
    "نسبة الانتاج القياسية": "standard_production_rate",
    "كسر": "broken_eggs",
    "متسخ": "dirty_eggs",
    "الأشر": "unknown_marker_field",
    "الماء المستهلك": "water_consumption",
    # Company-wide aggregate feed fields (poultry hall/field stage - never
    # the feed mill's raw-material concepts, per Founder ruling).
    "إجمالي العلف المستلم": "feed_received",
    "إجمالي العلف المستهلك": "feed_consumed",
    "متوسط العلف للطير الواحد": "feed_per_bird_average",
    # Egg-size grading columns (أشقر, S, M, L, XL, ...) are deliberately NOT
    # mapped here - deferred per Founder ruling. They remain visible only in
    # raw_values.
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
# feed_received/feed_consumed are kept as floats rather than truncated to
# int: the source contract does not prove these quantities are always
# whole-unit (Codex Round 1 Finding 7), so source precision is preserved.
FLOAT_FIELDS = {
    "feed_per_bird_average",
    "feed_received",
    "feed_consumed",
}

HALL_NUMBER_LABEL = "رقم القاعة"
HALL_NAME_LABEL = "اسم الحقل"
REARING_HALL_TERM = "تربية"


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

    def detect_shape(self, sheets: list[ExcelSheet]) -> str | None:
        """Return the first recognized report shape across all sheets, or None."""
        for sheet in sheets:
            _, _, shape = self._find_header_row(sheet.rows)
            if shape is not None:
                return shape
        return None

    def _translate_sheet(
        self,
        sheet: ExcelSheet,
        source_file: Path,
    ) -> list[PoultryOperationalRecord]:
        header_index, headers, shape = self._find_header_row(sheet.rows)
        if header_index is None or shape is None:
            return []

        entity_type, entity_reference = self._extract_entity(
            sheet.rows[:header_index],
            shape,
        )

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
                    feed_received=translated.get("feed_received"),
                    feed_consumed=translated.get("feed_consumed"),
                    feed_per_bird_average=translated.get("feed_per_bird_average"),
                    unknown_marker_field=translated.get("unknown_marker_field"),
                    source_file=str(source_file),
                    sheet_name=sheet.name,
                    row_number=row_offset,
                    report_shape=shape,
                    entity_type=entity_type,
                    entity_reference=entity_reference,
                    raw_values=raw_values,
                    epistemic_origin="observed",
                )
            )
        return records

    def _find_header_row(
        self,
        rows: list[tuple[Any, ...]],
    ) -> tuple[int | None, list[str], str | None]:
        for index, row in enumerate(rows):
            headers = [str(value).strip() if value is not None else "" for value in row]
            normalized = {_normalize_header(header) for header in headers if header}
            for shape, signature in SHAPE_HEADER_SIGNATURES.items():
                if set(signature).issubset(normalized):
                    return index, headers, shape
        return None, [], None

    def _extract_entity(
        self,
        pre_header_rows: list[tuple[Any, ...]],
        shape: str,
    ) -> tuple[str | None, str | None]:
        """Extract hall/entity identity only when structurally present.

        Per the Founder Business Semantics Ruling - M3 and Codex Round 1
        Finding 1: entity identity must never be guessed from free text.
        The ONLY authoritative signal is the value paired with the explicit
        "اسم الحقل" (field/hall name) key - the same structural key-value
        pair already proven across the real Family-1 report family. A
        "تربية" (rearing) marker occurring anywhere else in pre-header prose
        (titles, notes, company descriptions) is NOT structural evidence and
        must never flip the entity kind.
        """
        hall_number: str | None = None
        hall_label: str | None = None

        for row in pre_header_rows:
            cells = [value for value in row if value is not None]
            for position, value in enumerate(cells):
                text = str(value).strip()
                normalized = _normalize_header(text)
                if normalized == HALL_NUMBER_LABEL and position + 1 < len(cells):
                    hall_number = str(cells[position + 1]).strip()
                if normalized == HALL_NAME_LABEL and position + 1 < len(cells):
                    hall_label = str(cells[position + 1]).strip()

        if hall_label is not None and REARING_HALL_TERM in _normalize_header(hall_label):
            return "rearing_hall", hall_number or hall_label

        if hall_number is not None or hall_label is not None:
            return "production_hall", hall_number or hall_label

        if shape == SHAPE_DAILY_TECHNICAL_AGGREGATE:
            return "company_aggregate", None

        return None, None

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
        if field_name in FLOAT_FIELDS:
            return _parse_float(value)
        if isinstance(value, str):
            return value.strip()
        return value


def resolve_source_label(raw_values: dict[str, Any], canonical_field: str) -> tuple[str | None, Any]:
    """Return (original source header, pre-normalization raw value) for a
    canonical field, from a record's raw_values.

    Codex Round 2 Finding 3 (semantic claim provenance): derived artifacts
    must be able to prove not just WHERE a value came from (file/sheet/row)
    but WHICH source field/claim it came from. ``raw_values`` is keyed by
    the exact original Arabic header text that was present in that specific
    workbook, so this performs the reverse lookup against
    ``ARABIC_COLUMN_MAP`` to find the one header (if any) that produced the
    given canonical field on this record. Returns (None, None) when the
    field is not present in this record's source (e.g. a metric field the
    shape does not carry).
    """
    for header, value in raw_values.items():
        if ARABIC_COLUMN_MAP.get(_normalize_header(header)) == canonical_field:
            return header, value
    return None, None


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


def _parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return float(value.strip().replace(",", ""))
    return float(value)
