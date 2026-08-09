"""M3 Phase 2 acceptance tests (Founder Business Semantics Ruling - M3,
hardened per Codex Round 1 peer review findings 1-8).

All fixtures below are synthetic (fabricated numbers, never real pilot
company data) and are built as in-memory ``ExcelSheet`` objects (or, for the
KAE ingestion-state tests, small temp .xlsx files) so these tests are fully
deterministic and do not depend on the gitignored ``data_sources/``
directory being present.
"""

from __future__ import annotations

from datetime import date

from app.oip.loaders.excel_loader import ExcelSheet
from app.oip.models.feed_mill_inventory_record import FeedMillInventoryRecord
from app.oip.models.operational_record import PoultryOperationalRecord
from app.oip.services.poultry_derivation_service import PoultryDerivationService
from app.oip.services.poultry_situation_service import PoultrySituationService
from app.oip.translators.feed_mill_inventory_translator import (
    REPORT_DATE_AUTHORITATIVE,
    REPORT_DATE_UNRESOLVED,
    FeedMillInventoryTranslator,
)
from app.oip.translators.poultry_report_translator import (
    SHAPE_DAILY_TECHNICAL_AGGREGATE,
    SHAPE_DAILY_TECHNICAL_HALL,
    PoultryReportTranslator,
)
from app.oip.validators.poultry_validator import PoultryValidator


# ---------------------------------------------------------------------------
# Synthetic Family 1 (single hall) fixtures
# ---------------------------------------------------------------------------

FAMILY1_HEADER_ROW = (
    "التاريخ",
    "اليوم",
    "العمر بالأسبوع",
    "العمر باليوم",
    "رصيد الطيور",
    "الهلاكات اليومية",
    "الهلاكات الأسبوعية",
    "نسبة الهلاكات الأسبوعية",
    "الإنتاج اليومي بالطبق",
    "الإنتاج بالصندوق",
    "نسبة الإنتاج اليومية",
    "نسبة الإنتاج القياسية",
    "كسر",
    "متسخ",
    "الماء المستهلك",
)


def _family1_data_row(
    day: int,
    with_water: bool = True,
    daily_rate: str = "75.00%",
    standard_rate: str = "80.00%",
) -> tuple:
    row = [
        date(2026, 6, day),
        "الاثنين",
        10,
        70,
        1000 - day,
        2,
        14,
        "1.00%",
        450,
        37,
        daily_rate,
        standard_rate,
        1,
        1,
    ]
    row.append(6000 if with_water else None)
    return tuple(row)


def _production_hall_sheet(hall_number: int = 2, hall_label: str = "الأحمر") -> ExcelSheet:
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("رقم القاعة", hall_number, "اسم الحقل", hall_label, "عدد الدجاج", 9000),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1),
        _family1_data_row(2),
    ]
    return ExcelSheet(name="القاعة", rows=rows)


def _rearing_hall_sheet() -> ExcelSheet:
    """Authoritative rearing-hall evidence: the value under اسم الحقل itself."""
    rows = [
        ("شركة تجريبية - تقرير حقل التربية",),
        ("رقم القاعة", 5, "اسم الحقل", "حقل التربية الأول"),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1),
    ]
    return ExcelSheet(name="التربية", rows=rows)


def _incidental_rearing_word_sheet() -> ExcelSheet:
    """"تربية" appears only in free-text title prose, never in اسم الحقل.

    This must resolve to production_hall, not rearing_hall (Codex Round 1
    Finding 1: incidental substring occurrence is not structural evidence).
    """
    rows = [
        ("شركة تجريبية - قسم تربية الدواجن - التقرير الفني اليومي",),
        ("رقم القاعة", 2, "اسم الحقل", "الأحمر"),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1),
    ]
    return ExcelSheet(name="القاعة", rows=rows)


def _unresolved_entity_sheet(with_water: bool = True) -> ExcelSheet:
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("بيانات (حقل سابق) تم النقل - نص حر بدون بنية رقم القاعة",),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1, with_water=with_water),
        _family1_data_row(2, with_water=with_water),
    ]
    return ExcelSheet(name="افتراضي", rows=rows)


AGGREGATE_HEADER_ROW = (
    "التاريخ",
    "اليوم",
    "إجمالي أعداد الطيور للحقول",
    "إجمالي الهلاكات اليومية",
    "الهلاكات الأسبوعية",
    "نسبة الهلاكات الأسبوعية",
    "إجمالي الإنتاج اليومي بالطبق",
    "إجمالي الإنتاج (بالصندوق)",
    "نسبة الإنتاج اليومي للحقول",
    "كسر",
    "أشقر",
    "متسخ",
    "S",
    "M",
    "L",
    "XL",
    "خشن XXL",
    "صفارين XXXL",
    "الماء المستهلك",
    "إجمالي العلف المستلم",
    "إجمالي العلف المستهلك",
    "متوسط العلف للطير الواحد",
)


def _aggregate_data_row(
    feed_received: object = 900,
    feed_consumed: object = 850,
) -> tuple:
    return (
        date(2026, 6, 1),
        "الاثنين",
        5000,
        5,
        35,
        "0.70%",
        4000,
        333,
        "80.00%",
        20,
        10,
        15,
        100,
        200,
        150,
        50,
        10,
        5,
        1200,
        feed_received,
        feed_consumed,
        4,
    )


def _aggregate_sheet(feed_received: object = 900, feed_consumed: object = 850) -> ExcelSheet:
    rows = [
        ("شركة تجريبية - إجمالي الحقول (الإنتاج)",),
        AGGREGATE_HEADER_ROW,
        _aggregate_data_row(feed_received, feed_consumed),
    ]
    return ExcelSheet(name="إجمالي الإنتاج", rows=rows)


def _unsupported_shape_sheet() -> ExcelSheet:
    rows = [
        ("جدول غير مرتبط بأي شكل معتمد",),
        ("عمود1", "عمود2", "عمود3"),
        ("قيمة1", "قيمة2", "قيمة3"),
    ]
    return ExcelSheet(name="Sheet1", rows=rows)


# ---------------------------------------------------------------------------
# T1 / T2: shape-based, filename-independent parsing for Family 1
# ---------------------------------------------------------------------------


def test_t1_family1_hall_shape_parses_independent_of_which_real_file_family_member() -> None:
    translator = PoultryReportTranslator()
    for sheet in (_production_hall_sheet(2, "الأحمر"), _production_hall_sheet(3, "الأبيض")):
        records = translator.translate([sheet], "any_filename.xlsx")
        assert len(records) == 2
        assert all(r.report_shape == SHAPE_DAILY_TECHNICAL_HALL for r in records)


def test_t2_renamed_copy_of_supported_report_still_parses() -> None:
    translator = PoultryReportTranslator()
    sheet = _production_hall_sheet()
    original = translator.translate([sheet], "التقرير_الفني_اليومي_حقول_ديرتنا.xlsx")
    renamed = translator.translate([sheet], "completely_unrelated_name_2099.xlsx")

    assert len(original) == len(renamed) == 2
    for left, right in zip(original, renamed):
        assert left.date == right.date
        assert left.bird_balance == right.bird_balance
        assert left.report_shape == right.report_shape == SHAPE_DAILY_TECHNICAL_HALL
    assert original[0].source_file != renamed[0].source_file


# ---------------------------------------------------------------------------
# T3: aggregate shape parses feed_received and feed_consumed as distinct
# ---------------------------------------------------------------------------


def test_t3_aggregate_shape_parses_distinct_feed_received_and_feed_consumed() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_aggregate_sheet()], "إجمالي_حقول_ديرتنا_الإنتاج.xlsx")

    assert len(records) == 1
    record = records[0]
    assert record.report_shape == SHAPE_DAILY_TECHNICAL_AGGREGATE
    assert record.feed_received == 900
    assert record.feed_consumed == 850
    assert record.feed_received != record.feed_consumed
    assert record.feed_per_bird_average == 4
    assert record.entity_type == "company_aggregate"
    # Egg-size grading columns are deferred - never promoted to canonical fields.
    assert "S" not in record.__dataclass_fields__ or record.raw_values.get("S") == 100


def test_family1_validator_still_accepts_aggregate_records() -> None:
    translator = PoultryReportTranslator()
    validator = PoultryValidator()
    records = translator.translate([_aggregate_sheet()], "إجمالي_حقول_ديرتنا_الإنتاج.xlsx")
    validator.validate_or_raise(records)  # must not raise


# ---------------------------------------------------------------------------
# Finding 7 / T-hardening: feed numeric precision must not be truncated
# ---------------------------------------------------------------------------


def test_finding7_feed_received_and_consumed_preserve_decimal_precision() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate(
        [_aggregate_sheet(feed_received="900.5", feed_consumed="849.75")],
        "a.xlsx",
    )
    assert records[0].feed_received == 900.5
    assert records[0].feed_consumed == 849.75
    # not silently truncated to int
    assert records[0].feed_received != 900
    assert records[0].feed_consumed != 849


# ---------------------------------------------------------------------------
# T4 / T5: Feed Mill inventory snapshot block detector
# ---------------------------------------------------------------------------


def _feed_mill_decoy_sheet() -> ExcelSheet:
    rows = [
        ("سجل غير مرتبط بالبنية المعتمدة",),
        ("الصنف", "مادة1", "مادة2"),
        (date(2026, 6, 1), 10, 20),
        (date(2026, 6, 2), 15, 25),
    ]
    return ExcelSheet(name="تسجيل الوارد", rows=rows)


def _feed_mill_balance_sheet(date_label: str | None = "تاريخ التقرير") -> ExcelSheet:
    date_row = (
        (date_label, date(2026, 6, 15), None, "M1-EN", "M2-EN", "M3-EN")
        if date_label is not None
        else (date(2026, 6, 15), None, None, "M1-EN", "M2-EN", "M3-EN")
    )
    rows = [
        ("جرد المواد بالجاروشة",),
        ("", "", "ديرتنا", 1, 2, 3),
        ("", "", "الصنف", "مادة1", "مادة2", "مادة3"),
        date_row,
        ("", "", "رصيد الجاروشة", 10, 20, 30),
        ("", "", "متوسط الاستهلاك اليومي", 1, 2, 3),
        ("", "", "الكمية تكفي/يوم", 5, 8, 12),
    ]
    return ExcelSheet(name="رصيد الجاروشة", rows=rows)


def test_t4_feed_mill_translator_parses_only_approved_block() -> None:
    translator = FeedMillInventoryTranslator()
    records = translator.translate(
        [_feed_mill_decoy_sheet(), _feed_mill_balance_sheet()],
        "جرد الجاروشة.xlsx",
    )

    assert len(records) == 3
    assert all(r.sheet_name == "رصيد الجاروشة" for r in records)
    assert all(r.report_shape == "feed_mill_raw_material_inventory_snapshot" for r in records)
    assert all(r.entity_type == "feed_mill" for r in records)
    assert {r.material_name for r in records} == {"مادة1", "مادة2", "مادة3"}
    assert all(r.report_date == date(2026, 6, 15) for r in records)
    assert all(r.report_date_status == REPORT_DATE_AUTHORITATIVE for r in records)


def test_t5_raw_material_inventory_and_days_coverage_remain_distinct() -> None:
    translator = FeedMillInventoryTranslator()
    records = translator.translate([_feed_mill_balance_sheet()], "جرد الجاروشة.xlsx")
    by_material = {r.material_name: r for r in records}

    assert by_material["مادة1"].raw_material_inventory == 10
    assert by_material["مادة1"].source_reported_days_coverage == 5
    assert by_material["مادة2"].raw_material_inventory == 20
    assert by_material["مادة2"].source_reported_days_coverage == 8
    assert by_material["مادة3"].raw_material_inventory == 30
    assert by_material["مادة3"].source_reported_days_coverage == 12
    for record in records:
        assert record.raw_material_inventory != record.source_reported_days_coverage


# ---------------------------------------------------------------------------
# Finding 2 adversarial tests: coherent contiguous block only
# ---------------------------------------------------------------------------


def _filler_row(width: int = 6) -> tuple:
    return tuple([None] * width)


def test_finding2_unrelated_material_header_before_real_block_is_not_cross_matched() -> None:
    rows = [
        ("سجل غير مرتبط",),
        ("الصنف", "ديكوي1", "ديكوي2"),  # decoy header - no balance row nearby
        *[_filler_row(3) for _ in range(10)],  # gap far beyond MAX_BLOCK_GAP
        ("", "", "الصنف", "مادة1", "مادة2"),  # real header
        ("", "", "رصيد الجاروشة", 10, 20),  # real balance, close to real header
        ("", "", "الكمية تكفي/يوم", 5, 8),  # real coverage
    ]
    sheet = ExcelSheet(name="مختلط", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    assert {r.material_name for r in records} == {"مادة1", "مادة2"}
    assert len(records) == 2
    by_material = {r.material_name: r for r in records}
    assert by_material["مادة1"].raw_material_inventory == 10
    assert by_material["مادة2"].raw_material_inventory == 20


def test_finding2_unrelated_balance_label_far_outside_block_is_not_cross_matched() -> None:
    rows = [
        ("", "", "الصنف", "مادة1", "مادة2"),
        ("", "", "رصيد الجاروشة", 10, 20),
        ("", "", "الكمية تكفي/يوم", 5, 8),
        *[_filler_row(3) for _ in range(15)],
        ("ملاحظة غير مرتبطة", "رصيد الجاروشة", "قيمة عشوائية"),  # unrelated stray label
    ]
    sheet = ExcelSheet(name="مختلط", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    # Only the real, nearest balance row is used - the stray one is never
    # combined into a second/duplicate block.
    assert len(records) == 2
    assert {r.raw_material_inventory for r in records} == {10, 20}


def test_finding2_coverage_from_a_different_block_never_leaks_across() -> None:
    rows = [
        ("", "", "الصنف", "بلوك1-مادة1"),  # block 1: header
        ("", "", "رصيد الجاروشة", 100),  # block 1: balance, no coverage nearby
        *[_filler_row(2) for _ in range(15)],
        ("", "", "الصنف", "بلوك2-مادة1"),  # block 2: header
        ("", "", "رصيد الجاروشة", 200),  # block 2: balance
        ("", "", "الكمية تكفي/يوم", 9),  # block 2: coverage
    ]
    sheet = ExcelSheet(name="مختلط", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")
    by_material = {r.material_name: r for r in records}

    assert by_material["بلوك1-مادة1"].raw_material_inventory == 100
    assert by_material["بلوك1-مادة1"].source_reported_days_coverage is None
    assert by_material["بلوك2-مادة1"].raw_material_inventory == 200
    assert by_material["بلوك2-مادة1"].source_reported_days_coverage == 9


# ---------------------------------------------------------------------------
# Round 2 Finding 2: material-column boundary - a column is a material only
# when it is not a known non-material term AND the balance row holds a valid
# numeric value for it
# ---------------------------------------------------------------------------


def test_round2f2_trailing_notes_and_entered_by_columns_are_not_materials() -> None:
    rows = [
        ("", "", "الصنف", "مادة1", "ملاحظات", "أدخل بواسطة"),
        ("", "", "رصيد الجاروشة", 10, "ملاحظة نصية", "أحمد"),
    ]
    sheet = ExcelSheet(name="رصيد الجاروشة", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    assert {r.material_name for r in records} == {"مادة1"}
    assert len(records) == 1


def test_round2f2_material_header_with_missing_inventory_produces_no_record() -> None:
    rows = [
        ("", "", "الصنف", "مادة1", "مادة2"),
        ("", "", "رصيد الجاروشة", 10, None),
    ]
    sheet = ExcelSheet(name="رصيد الجاروشة", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    assert {r.material_name for r in records} == {"مادة1"}
    assert len(records) == 1


def test_round2f2_partially_populated_region_emits_only_valid_aligned_materials() -> None:
    rows = [
        ("", "", "الصنف", "مادة1", "مادة2", "مادة3"),
        ("", "", "رصيد الجاروشة", 10, None, 30),
    ]
    sheet = ExcelSheet(name="رصيد الجاروشة", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    assert {r.material_name for r in records} == {"مادة1", "مادة3"}
    assert len(records) == 2


def test_round2f2_totals_column_is_never_emitted_as_a_material() -> None:
    rows = [
        ("", "", "الصنف", "مادة1", "مادة2", "الإجمالي"),
        ("", "", "رصيد الجاروشة", 10, 20, 30),
    ]
    sheet = ExcelSheet(name="رصيد الجاروشة", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    assert {r.material_name for r in records} == {"مادة1", "مادة2"}
    assert "الإجمالي" not in {r.material_name for r in records}
    assert len(records) == 2


# ---------------------------------------------------------------------------
# Round 2 Finding 1: Feed Mill report_date is promoted only from an
# explicit allowlist of snapshot/report-date labels
# ---------------------------------------------------------------------------


def test_finding3_authoritative_labeled_date_is_promoted() -> None:
    records = FeedMillInventoryTranslator().translate(
        [_feed_mill_balance_sheet(date_label="تاريخ التقرير")], "a.xlsx"
    )
    assert all(r.report_date == date(2026, 6, 15) for r in records)
    assert all(r.report_date_status == REPORT_DATE_AUTHORITATIVE for r in records)
    assert all(r.provenance_warnings == () for r in records)


def test_round2f1_receipt_date_label_is_not_authoritative() -> None:
    records = FeedMillInventoryTranslator().translate(
        [_feed_mill_balance_sheet(date_label="تاريخ الاستلام")], "a.xlsx"
    )
    assert all(r.report_date is None for r in records)
    assert all(r.report_date_status == REPORT_DATE_UNRESOLVED for r in records)
    assert all(r.provenance_warnings for r in records)
    assert all(
        {"label": "تاريخ الاستلام", "date": "2026-06-15"} in r.raw_values["date_candidates"]
        for r in records
    )


def test_round2f1_last_supply_date_label_is_not_authoritative() -> None:
    records = FeedMillInventoryTranslator().translate(
        [_feed_mill_balance_sheet(date_label="تاريخ آخر توريد")], "a.xlsx"
    )
    assert all(r.report_date is None for r in records)
    assert all(r.report_date_status == REPORT_DATE_UNRESOLVED for r in records)


def test_finding3_arbitrary_unlabeled_date_inside_block_is_not_promoted() -> None:
    records = FeedMillInventoryTranslator().translate(
        [_feed_mill_balance_sheet(date_label=None)], "a.xlsx"
    )
    assert all(r.report_date is None for r in records)
    assert all(r.report_date_status == REPORT_DATE_UNRESOLVED for r in records)
    assert all(r.provenance_warnings for r in records)
    assert all(
        {"label": "unlabeled", "date": "2026-06-15"} in r.raw_values["date_candidates"]
        for r in records
    )


def test_finding3_no_date_at_all_is_unresolved_with_absent_warning() -> None:
    rows = [
        ("جرد المواد بالجاروشة",),
        ("", "", "الصنف", "مادة1"),
        ("", "", "رصيد الجاروشة", 10),
        ("", "", "الكمية تكفي/يوم", 5),
    ]
    sheet = ExcelSheet(name="رصيد الجاروشة", rows=rows)
    records = FeedMillInventoryTranslator().translate([sheet], "a.xlsx")

    assert all(r.report_date is None for r in records)
    assert all(r.report_date_status == REPORT_DATE_UNRESOLVED for r in records)
    assert all(r.raw_values.get("date_candidates") == [] for r in records)
    assert all("report_date_absent" in w for r in records for w in r.provenance_warnings)


# ---------------------------------------------------------------------------
# T6: field_feed_consumption is never mapped as feed-mill raw-material data
# ---------------------------------------------------------------------------


def test_t6_feed_mill_record_has_no_poultry_consumption_concept() -> None:
    feed_mill_fields = set(FeedMillInventoryRecord.__dataclass_fields__)
    assert "feed_consumed" not in feed_mill_fields
    assert "feed_received" not in feed_mill_fields

    poultry_fields = set(PoultryOperationalRecord.__dataclass_fields__)
    assert "raw_material_inventory" not in poultry_fields
    assert "source_reported_days_coverage" not in poultry_fields

    # The feed mill balance/coverage labels must never appear in the poultry
    # translator's canonical column map.
    from app.oip.translators.poultry_report_translator import ARABIC_COLUMN_MAP

    assert "رصيد الجاروشة" not in ARABIC_COLUMN_MAP
    assert "الكمية تكفي/يوم" not in ARABIC_COLUMN_MAP


# ---------------------------------------------------------------------------
# Finding 1 / T7 / T8: entity semantics - structural evidence only
# ---------------------------------------------------------------------------


def test_finding1a_authoritative_rearing_hall_structure_resolves_rearing_hall() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_rearing_hall_sheet()], "a.xlsx")
    assert all(r.entity_type == "rearing_hall" for r in records)


def test_finding1b_incidental_prose_mentioning_rearing_is_not_rearing_hall() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_incidental_rearing_word_sheet()], "a.xlsx")
    assert all(r.entity_type == "production_hall" for r in records)
    assert all(r.entity_reference == "2" for r in records)


def test_finding1c_production_hall_remains_production_hall() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_production_hall_sheet(2, "الأحمر")], "a.xlsx")
    assert all(r.entity_type == "production_hall" for r in records)


def test_finding1d_report_without_structural_entity_stays_unresolved() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_unresolved_entity_sheet()], "a.xlsx")
    assert all(r.entity_type is None for r in records)
    assert all(r.entity_reference is None for r in records)


def test_t7_production_and_rearing_halls_stay_distinct() -> None:
    translator = PoultryReportTranslator()
    production_records = translator.translate([_production_hall_sheet(2, "الأحمر")], "a.xlsx")
    rearing_records = translator.translate([_rearing_hall_sheet()], "b.xlsx")

    assert all(r.entity_type == "production_hall" for r in production_records)
    assert all(r.entity_type == "rearing_hall" for r in rearing_records)
    assert {r.entity_type for r in production_records}.isdisjoint(
        {r.entity_type for r in rearing_records}
    )


def test_t8_entity_identity_extracted_when_supported_left_unresolved_when_not() -> None:
    translator = PoultryReportTranslator()

    resolved = translator.translate([_production_hall_sheet(2, "الأحمر")], "a.xlsx")
    assert resolved[0].entity_type == "production_hall"
    assert resolved[0].entity_reference == "2"

    unresolved = translator.translate([_unresolved_entity_sheet()], "b.xlsx")
    assert unresolved[0].entity_type is None
    assert unresolved[0].entity_reference is None


# ---------------------------------------------------------------------------
# T9: water present is parsed; absent source field is NOT REPORTED (never 0)
# ---------------------------------------------------------------------------


def test_t9_water_present_is_parsed_and_absent_is_not_reported_as_zero() -> None:
    translator = PoultryReportTranslator()

    present = translator.translate([_production_hall_sheet()], "a.xlsx")
    assert present[0].water_consumption == 6000

    header_row_without_water = FAMILY1_HEADER_ROW[:-1]
    data_row_without_water = _family1_data_row(1)[:-1]
    sheet_without_water_column = ExcelSheet(
        name="بدون ماء",
        rows=[
            ("عنوان",),
            header_row_without_water,
            data_row_without_water,
        ],
    )
    absent = translator.translate([sheet_without_water_column], "b.xlsx")
    assert absent[0].water_consumption is None
    assert absent[0].water_consumption != 0


# ---------------------------------------------------------------------------
# T10 / Finding 5: unsupported/ambiguous shape is never force-fit, and KAE
# exposes a truthful three-state ingestion status
# ---------------------------------------------------------------------------


def test_t10_unsupported_shape_is_not_force_fit() -> None:
    translator = PoultryReportTranslator()
    sheet = _unsupported_shape_sheet()

    assert translator.detect_shape([sheet]) is None
    assert translator.translate([sheet], "ambiguous.xlsx") == []


def test_t10_recognized_shape_is_explicitly_identifiable() -> None:
    translator = PoultryReportTranslator()
    assert translator.detect_shape([_production_hall_sheet()]) == SHAPE_DAILY_TECHNICAL_HALL
    assert translator.detect_shape([_aggregate_sheet()]) == SHAPE_DAILY_TECHNICAL_AGGREGATE


def _write_workbook(path, rows_by_sheet: dict[str, list[tuple]]) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    default_sheet = workbook.active
    first = True
    for sheet_name, rows in rows_by_sheet.items():
        worksheet = default_sheet if first else workbook.create_sheet()
        worksheet.title = sheet_name
        for row in rows:
            worksheet.append(list(row))
        first = False
    workbook.save(path)


def test_finding5_kae_supported_with_data(tmp_path) -> None:
    from app.nco.pipeline import KAE_STATE_SUPPORTED_WITH_DATA, NCOLitePipeline

    path = tmp_path / "supported.xlsx"
    _write_workbook(
        path,
        {"القاعة": [("title",), ("رقم القاعة", 2, "اسم الحقل", "الأحمر"), FAMILY1_HEADER_ROW, _family1_data_row(1)]},
    )
    output = NCOLitePipeline().run_kae(path)
    assert output.ingestion_state == KAE_STATE_SUPPORTED_WITH_DATA
    assert output.structured_ingestion_supported is True
    assert len(output.records) == 1


def test_finding5_kae_recognized_but_no_structured_records(tmp_path) -> None:
    from app.nco.pipeline import KAE_STATE_RECOGNIZED_NO_RECORDS, NCOLitePipeline

    path = tmp_path / "empty.xlsx"
    _write_workbook(path, {"القاعة": [("title",), FAMILY1_HEADER_ROW]})
    output = NCOLitePipeline().run_kae(path)
    assert output.ingestion_state == KAE_STATE_RECOGNIZED_NO_RECORDS
    assert output.structured_ingestion_supported is False
    assert output.records == []
    assert output.report_shape == SHAPE_DAILY_TECHNICAL_HALL


def test_finding5_kae_unsupported_or_ambiguous(tmp_path) -> None:
    from app.nco.pipeline import KAE_STATE_UNSUPPORTED_OR_AMBIGUOUS, NCOLitePipeline

    path = tmp_path / "ambiguous.xlsx"
    _write_workbook(path, {"Sheet1": [("col1", "col2"), ("v1", "v2")]})
    output = NCOLitePipeline().run_kae(path)
    assert output.ingestion_state == KAE_STATE_UNSUPPORTED_OR_AMBIGUOUS
    assert output.structured_ingestion_supported is False
    assert output.report_shape is None


# ---------------------------------------------------------------------------
# Entity plumbing through derived artifacts (supports T7/T8 downstream)
# ---------------------------------------------------------------------------


def test_derivation_service_carries_entity_through_to_metrics_and_events() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_production_hall_sheet(2, "الأحمر")], "a.xlsx")
    artifacts = PoultryDerivationService().derive(records)

    assert all(m.entity_type == "production_hall" for m in artifacts.metrics)
    assert all(m.entity_reference == "2" for m in artifacts.metrics)
    assert all(e.entity_type == "production_hall" for e in artifacts.events)


def test_derivation_service_leaves_metrics_unresolved_when_source_does() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_unresolved_entity_sheet()], "a.xlsx")
    artifacts = PoultryDerivationService().derive(records)

    assert all(m.entity_type is None for m in artifacts.metrics)


# ---------------------------------------------------------------------------
# Finding 4: provenance survives normalized record -> metric/event -> evidence
# ---------------------------------------------------------------------------


def _declining_production_sheet() -> ExcelSheet:
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("رقم القاعة", 7, "اسم الحقل", "الأصفر"),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1, daily_rate="80.00%", standard_rate="90.00%"),
        _family1_data_row(2, daily_rate="75.00%", standard_rate="90.00%"),
        _family1_data_row(3, daily_rate="70.00%", standard_rate="90.00%"),
        _family1_data_row(4, daily_rate="65.00%", standard_rate="90.00%"),
    ]
    return ExcelSheet(name="القاعة 7", rows=rows)


def test_finding4_provenance_survives_record_to_metric_and_event() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_declining_production_sheet()], "provenance_source.xlsx")
    artifacts = PoultryDerivationService().derive(records)

    source_record = records[0]
    matching_metrics = [
        m for m in artifacts.metrics if m.source_row_number == source_record.row_number
    ]
    assert matching_metrics
    for metric in matching_metrics:
        assert metric.source_file == source_record.source_file
        assert metric.sheet_name == source_record.sheet_name == "القاعة 7"
        assert metric.report_shape == source_record.report_shape == SHAPE_DAILY_TECHNICAL_HALL
        assert metric.entity_type == "production_hall"
        assert metric.entity_reference == "7"

    matching_events = [
        e for e in artifacts.events if e.source_row_number == source_record.row_number
    ]
    assert matching_events
    for event in matching_events:
        assert event.sheet_name == "القاعة 7"
        assert event.report_shape == SHAPE_DAILY_TECHNICAL_HALL
        assert event.entity_type == "production_hall"
        assert event.entity_reference == "7"


def test_finding4_provenance_survives_into_situation_evidence() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_declining_production_sheet()], "provenance_source.xlsx")
    artifacts = PoultryDerivationService().derive(records)
    situations = PoultrySituationService().generate_situations(artifacts.signals)

    assert situations, "fixture must trigger at least one production_drop situation"
    situation = situations[0]
    assert situation.entity_type == "production_hall"
    assert situation.entity_reference == "7"
    assert situation.evidence
    for item in situation.evidence:
        assert item["source_file"] == "provenance_source.xlsx"
        assert item["sheet_name"] == "القاعة 7"
        assert item["report_shape"] == SHAPE_DAILY_TECHNICAL_HALL
        assert item["source_row_number"] is not None


# ---------------------------------------------------------------------------
# Round 2 Finding 3: semantic claim provenance - not just WHERE a value came
# from, but WHICH source field/claim produced it, and its pre-normalization
# raw value. Two independent fields are proven (feed + production) so the
# mechanism is general, not hardcoded to one field.
# ---------------------------------------------------------------------------


def test_round2f3_feed_claim_provenance_from_source_label_to_metric() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate(
        [_aggregate_sheet(feed_received="900.5", feed_consumed="849.75")],
        "feed_provenance_source.xlsx",
    )
    artifacts = PoultryDerivationService().derive(records)

    feed_metric = next(m for m in artifacts.metrics if m.metric_name == "feed_consumed")
    assert feed_metric.source_label == "إجمالي العلف المستهلك"
    assert feed_metric.raw_source_value == "849.75"  # pre-normalization, still a string
    assert feed_metric.value == 849.75  # normalized
    assert feed_metric.raw_source_value != feed_metric.value
    assert feed_metric.source_file == "feed_provenance_source.xlsx"
    assert feed_metric.report_shape == SHAPE_DAILY_TECHNICAL_AGGREGATE
    assert feed_metric.entity_type == "company_aggregate"


def test_round2f3_production_claim_provenance_survives_record_to_metric_signal_and_evidence() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate(
        [_declining_production_sheet()], "production_provenance_source.xlsx"
    )
    artifacts = PoultryDerivationService().derive(records)
    situations = PoultrySituationService().generate_situations(artifacts.signals)

    # 1) record -> metric
    first_record = records[0]
    rate_metric = next(
        m
        for m in artifacts.metrics
        if m.metric_name == "daily_production_rate"
        and m.source_row_number == first_record.row_number
    )
    assert rate_metric.source_label == "نسبة الإنتاج اليومية"
    assert rate_metric.raw_source_value == "80.00%"
    assert rate_metric.value == 80.0
    assert rate_metric.raw_source_value != rate_metric.value

    # 2) record -> signal (production_below_standard has one direct claim)
    below_standard_signals = [
        s for s in artifacts.signals if s.signal_type == "production_below_standard"
    ]
    assert below_standard_signals
    for signal in below_standard_signals:
        assert signal.source_label == "نسبة الإنتاج اليومية"
        assert signal.raw_source_value is not None
        assert "%" in str(signal.raw_source_value)  # still the raw source string form

    # 3) signal -> situation.evidence
    assert situations
    situation = situations[0]
    trend_evidence = [
        item for item in situation.evidence if item["signal_type"] == "production_declining_trend"
    ]
    assert trend_evidence
    for item in trend_evidence:
        assert item["source_label"] == "نسبة الإنتاج اليومية"
        assert item["raw_source_value"] is not None


# ---------------------------------------------------------------------------
# OCE plumbing: related_entities and entity-scoped feed evidence (Finding 6)
# ---------------------------------------------------------------------------


class _NullFeedMillCollector:
    def collect_evidence(self, date_range):
        return None

    def collect_raw_material_inventory_evidence(self, date_range):
        return None


def test_context_collector_related_entities_reflects_resolved_entity() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector
    from app.oip.models.operational_situation import OperationalSituation

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    situation = OperationalSituation(
        situation_type="poultry_production_drop",
        severity="warning",
        title="t",
        summary="s",
        evidence=[],
        recommended_next_checks=[],
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        entity_type="production_hall",
        entity_reference="2",
    )
    context = collector.collect(
        situation=situation, metrics=[], events=[], signals=[], records=[]
    )
    assert context.related_entities == ["production_hall:2"]


def test_context_collector_related_entities_unresolved_when_entity_unknown() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector
    from app.oip.models.operational_situation import OperationalSituation

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    situation = OperationalSituation(
        situation_type="poultry_production_drop",
        severity="warning",
        title="t",
        summary="s",
        evidence=[],
        recommended_next_checks=[],
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
    )
    context = collector.collect(
        situation=situation, metrics=[], events=[], signals=[], records=[]
    )
    assert context.related_entities == ["unresolved"]


def _feed_metric(entity_type, entity_reference, value=850):
    from app.oip.models.derived_artifacts import OperationalMetric

    return OperationalMetric(
        metric_name="feed_consumed",
        value=value,
        date=date(2026, 6, 2),
        source_file="a.xlsx",
        source_row_number=3,
        entity_type=entity_type,
        entity_reference=entity_reference,
    )


def _situation(entity_type, entity_reference):
    from app.oip.models.operational_situation import OperationalSituation

    return OperationalSituation(
        situation_type="poultry_production_drop",
        severity="warning",
        title="t",
        summary="s",
        evidence=[],
        recommended_next_checks=[],
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        entity_type=entity_type,
        entity_reference=entity_reference,
    )


def test_finding6_hall_situation_with_matching_hall_feed_metric_is_available() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    context = collector.collect(
        situation=_situation("production_hall", "A"),
        metrics=[_feed_metric("production_hall", "A")],
        events=[],
        signals=[],
        records=[],
    )
    assert "feed_consumption" in {e.type for e in context.available_evidence}


def test_finding6_hall_situation_with_other_hall_feed_metric_is_not_satisfied() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    context = collector.collect(
        situation=_situation("production_hall", "A"),
        metrics=[_feed_metric("production_hall", "B")],
        events=[],
        signals=[],
        records=[],
    )
    assert "feed_consumption" not in {e.type for e in context.available_evidence}
    assert "feed_consumption" in {e.type for e in context.missing_evidence}


def test_finding6_hall_situation_with_company_aggregate_metric_is_not_satisfied() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    context = collector.collect(
        situation=_situation("production_hall", "A"),
        metrics=[_feed_metric("company_aggregate", None)],
        events=[],
        signals=[],
        records=[],
    )
    assert "feed_consumption" not in {e.type for e in context.available_evidence}
    assert "feed_consumption" in {e.type for e in context.missing_evidence}


def test_finding6_company_level_situation_with_company_aggregate_metric_is_valid() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    context = collector.collect(
        situation=_situation("company_aggregate", None),
        metrics=[_feed_metric("company_aggregate", None)],
        events=[],
        signals=[],
        records=[],
    )
    assert "feed_consumption" in {e.type for e in context.available_evidence}


def test_finding6_unresolved_situation_entity_cannot_claim_feed_evidence() -> None:
    from app.oce.collectors.poultry_context_collector import PoultryContextCollector

    collector = PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector())
    context = collector.collect(
        situation=_situation(None, None),
        metrics=[_feed_metric("production_hall", "A")],
        events=[],
        signals=[],
        records=[],
    )
    assert "feed_consumption" not in {e.type for e in context.available_evidence}
