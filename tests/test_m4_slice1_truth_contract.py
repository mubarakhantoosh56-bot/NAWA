"""M4 Slice 1 (Truth Contract Hardening) acceptance tests.

Founder Core Trust Principle: OBSERVED != DERIVED != INFERRED != RECOMMENDED.
No downstream transformation may silently promote one epistemic origin into
another. These tests prove that classification holds end to end through the
existing M3 KAE -> derived artifacts -> OCE evidence contract, without any
new Runtime Component, migration, or parallel TruthClaim model.

All fixtures are synthetic (fabricated numbers, never real pilot company
data), built as in-memory ``ExcelSheet`` objects, kept in a separate module
from tests/test_oip_m3_phase2.py so the M3-frozen suite stays untouched and
easy to diff against this new one.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.oce.collectors.feed_mill_context_collector import FeedMillContextCollector
from app.oce.collectors.poultry_context_collector import PoultryContextCollector
from app.oce.models.evidence import Evidence
from app.oip.loaders.excel_loader import ExcelSheet
from app.oip.models.derived_artifacts import OperationalEvent, OperationalMetric, OperationalSignal
from app.oip.models.feed_mill_inventory_record import FeedMillInventoryRecord
from app.oip.models.operational_record import PoultryOperationalRecord, validate_epistemic_origin
from app.oip.models.operational_situation import OperationalSituation
from app.oip.services.poultry_derivation_service import (
    PoultryDerivationService,
    _metric_epistemic_origin,
)
from app.oip.services.poultry_situation_service import PoultrySituationService
from app.oip.translators.feed_mill_inventory_translator import FeedMillInventoryTranslator
from app.oip.translators.poultry_report_translator import PoultryReportTranslator
from app.repositories.operational_event_repository import to_intelligence_event


# ---------------------------------------------------------------------------
# Shared synthetic fixtures (mirroring tests/test_oip_m3_phase2.py patterns)
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


def _production_hall_sheet(hall_number: int = 4, hall_label: str = "الأخضر") -> ExcelSheet:
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("رقم القاعة", hall_number, "اسم الحقل", hall_label),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1),
    ]
    return ExcelSheet(name="القاعة", rows=rows)


def _declining_production_sheet(hall_number: int = 8) -> ExcelSheet:
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("رقم القاعة", hall_number, "اسم الحقل", "الوردي"),
        FAMILY1_HEADER_ROW,
        _family1_data_row(1, daily_rate="80.00%", standard_rate="90.00%"),
        _family1_data_row(2, daily_rate="75.00%", standard_rate="90.00%"),
        _family1_data_row(3, daily_rate="70.00%", standard_rate="90.00%"),
        _family1_data_row(4, daily_rate="65.00%", standard_rate="90.00%"),
    ]
    return ExcelSheet(name="القاعة 8", rows=rows)


def _no_water_hall_sheet(hall_number: int = 9) -> ExcelSheet:
    header_row_without_water = FAMILY1_HEADER_ROW[:-1]
    data_row_without_water = _family1_data_row(1)[:-1]
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("رقم القاعة", hall_number, "اسم الحقل", "الرمادي"),
        header_row_without_water,
        data_row_without_water,
    ]
    return ExcelSheet(name="بدون ماء", rows=rows)


def _feed_mill_balance_sheet(date_label: str | None = None) -> ExcelSheet:
    """Mirrors the real workbook's unresolved-date shape by default: a real
    date value exists in the block but is not paired with any allowlisted
    snapshot/report-date label - exactly the Golden Pilot Feed Mill case.
    """
    date_row = (
        (date_label, date(2026, 6, 20), None, "M1-EN", "M2-EN", "M3-EN")
        if date_label is not None
        else (date(2026, 6, 20), None, None, "M1-EN", "M2-EN", "M3-EN")
    )
    rows = [
        ("جرد المواد بالجاروشة",),
        ("", "", "ديرتنا", 1, 2, 3),
        ("", "", "الصنف", "مادة1", "مادة2", "مادة3"),
        date_row,
        ("", "", "رصيد الجاروشة", 10, 20, 30),
        ("", "", "الكمية تكفي/يوم", 5, 8, 12),
    ]
    return ExcelSheet(name="رصيد الجاروشة", rows=rows)


def _build_situation_context(sheet: ExcelSheet, source_file: str) -> tuple:
    """Run sheet -> records -> artifacts -> situations -> OperationalContext,
    returning (records, artifacts, situations, contexts).
    """
    translator = PoultryReportTranslator()
    records = translator.translate([sheet], source_file)
    artifacts = PoultryDerivationService().derive(records)
    situations = PoultrySituationService().generate_situations(artifacts.signals)
    contexts = [
        PoultryContextCollector(feed_mill_collector=_NullFeedMillCollector()).collect(
            situation=situation,
            metrics=artifacts.metrics,
            events=artifacts.events,
            signals=artifacts.signals,
            records=records,
        )
        for situation in situations
    ]
    return records, artifacts, situations, contexts


class _NullFeedMillCollector:
    def collect_evidence(self, date_range):
        return None

    def collect_raw_material_inventory_evidence(self, date_range):
        return None


# ---------------------------------------------------------------------------
# T1 - observed source value remains OBSERVED
# ---------------------------------------------------------------------------


def test_t1_observed_source_value_remains_observed() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_production_hall_sheet()], "t1.xlsx")
    record = records[0]
    assert record.epistemic_origin == "observed"

    artifacts = PoultryDerivationService().derive(records)
    bird_balance_metric = next(
        m for m in artifacts.metrics if m.metric_name == "bird_balance"
    )
    assert bird_balance_metric.epistemic_origin == "observed"
    assert bird_balance_metric.value == record.bird_balance
    assert bird_balance_metric.source_label == "رصيد الطيور"


# ---------------------------------------------------------------------------
# T2 - deterministic derived value remains DERIVED
# ---------------------------------------------------------------------------


def test_t2_deterministic_derived_value_remains_derived() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_declining_production_sheet()], "t2.xlsx")
    artifacts = PoultryDerivationService().derive(records)

    trend_signals = [
        s for s in artifacts.signals if s.signal_type == "production_declining_trend"
    ]
    assert trend_signals
    assert all(s.epistemic_origin == "derived" for s in trend_signals)

    below_standard = [
        s for s in artifacts.signals if s.signal_type == "production_below_standard"
    ]
    assert below_standard
    assert all(s.epistemic_origin == "derived" for s in below_standard)

    # The whole-record summary event is a deterministic reformatting of
    # multiple observed fields, not one direct source claim - DERIVED.
    assert all(e.epistemic_origin == "derived" for e in artifacts.events)


# ---------------------------------------------------------------------------
# T3 - inferred information cannot masquerade as OBSERVED
# ---------------------------------------------------------------------------


def test_t3_inferred_cannot_masquerade_as_observed_in_oip_signals() -> None:
    """Nothing PoultryDerivationService produces is ever "observed" for a
    signal, nor "inferred" for a metric - this service performs no AI/
    non-deterministic reasoning, so its signals are DERIVED, never INFERRED
    OR OBSERVED (a signal is never a direct, unmodified source value)."""
    translator = PoultryReportTranslator()
    records = translator.translate([_declining_production_sheet()], "t3.xlsx")
    artifacts = PoultryDerivationService().derive(records)

    for signal in artifacts.signals:
        assert signal.epistemic_origin == "derived"
        assert signal.epistemic_origin != "observed"


def test_t3_ai_proposed_operational_event_is_inferred_never_observed() -> None:
    ai_drafted_row = {
        "id": "evt-1",
        "source_type": "file_draft",
        "metadata": {"ai_proposed": True, "confidence": 72},
    }
    result = to_intelligence_event(ai_drafted_row)
    assert result["context"]["origin"] == "inferred"
    assert result["context"]["origin"] != "observed"


# ---------------------------------------------------------------------------
# T4 - recommended information cannot masquerade as fact
# ---------------------------------------------------------------------------


def test_t4_recommended_never_appears_on_fact_bearing_artifacts() -> None:
    """RECOMMENDED is reserved for proposed actions (situation.
    recommended_next_checks / CEOBrief.recommended_next_actions), which are
    plain string lists never wrapped as Metric/Event/Signal/Evidence claims
    in this pipeline. No fact-bearing artifact this slice touches may ever
    carry epistemic_origin="recommended"."""
    translator = PoultryReportTranslator()
    records = translator.translate([_declining_production_sheet()], "t4.xlsx")
    artifacts = PoultryDerivationService().derive(records)

    for metric in artifacts.metrics:
        assert metric.epistemic_origin != "recommended"
    for event in artifacts.events:
        assert event.epistemic_origin != "recommended"
    for signal in artifacts.signals:
        assert signal.epistemic_origin != "recommended"

    situations = PoultrySituationService().generate_situations(artifacts.signals)
    for situation in situations:
        # recommended_next_checks is a plain list[str] - a proposed action
        # list, structurally incapable of being confused with an
        # epistemic-origin-tagged claim.
        assert isinstance(situation.recommended_next_checks, list)
        assert all(isinstance(item, str) for item in situation.recommended_next_checks)
        for item in situation.evidence:
            assert item.get("epistemic_origin") != "recommended"


# ---------------------------------------------------------------------------
# T5 / T6 - semantic provenance + authoritative source time survive into
# OCE evidence
# ---------------------------------------------------------------------------


def test_t5_t6_provenance_and_authoritative_time_survive_into_evidence() -> None:
    _, _, situations, contexts = _build_situation_context(
        _declining_production_sheet(), "t5.xlsx"
    )
    assert situations and contexts

    trend_evidence = next(
        e
        for context in contexts
        for e in context.available_evidence
        if e.type == "production_trend"
    )
    assert trend_evidence.epistemic_origin == "derived"
    assert trend_evidence.canonical_field == "daily_production_rate"
    assert trend_evidence.source_label == "نسبة الإنتاج اليومية"
    assert trend_evidence.raw_source_value is not None
    assert trend_evidence.source_file == "t5.xlsx"
    assert trend_evidence.entity_type == "production_hall"
    assert trend_evidence.entity_reference == "8"
    # T6: authoritative source time survives distinctly from date_range
    assert trend_evidence.source_time is not None
    assert trend_evidence.source_time_status == "authoritative"


# ---------------------------------------------------------------------------
# T7 / T8 - unresolved source time remains unresolved, never replaced by
# situation/window time (Feed Mill Golden Case groundwork)
# ---------------------------------------------------------------------------


def test_t7_t8_unresolved_feed_mill_time_is_not_replaced_by_situation_window() -> None:
    translator = FeedMillInventoryTranslator()
    records = translator.translate([_feed_mill_balance_sheet(date_label=None)], "t7.xlsx")
    assert records
    assert all(r.report_date is None for r in records)
    assert all(r.report_date_status == "unresolved" for r in records)

    collector = FeedMillContextCollector(inventory_translator=translator)
    window = (date(2026, 6, 1), date(2026, 6, 10))
    evidence = collector.collect_raw_material_inventory_evidence(date_range=window)
    assert evidence is not None

    # T7: source_time stays unresolved
    assert evidence.source_time is None
    assert evidence.source_time_status == "unresolved"
    # T8: never silently backfilled with the reasoning window's bounds
    assert evidence.source_time != window[0]
    assert evidence.source_time != window[1]
    assert evidence.date_range == window  # the window itself is untouched/distinct


# ---------------------------------------------------------------------------
# T9 - missing value is not converted to zero
# ---------------------------------------------------------------------------


def test_t9_missing_water_is_not_converted_to_zero() -> None:
    _, artifacts, situations, contexts = _build_situation_context(
        _no_water_hall_sheet(), "t9.xlsx"
    )
    water_metrics = [m for m in artifacts.metrics if m.metric_name == "water_consumption"]
    assert all(m.value is None for m in water_metrics)

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
        situation=situation,
        metrics=artifacts.metrics,
        events=artifacts.events,
        signals=artifacts.signals,
        records=[],
    )
    available_types = {e.type for e in context.available_evidence}
    missing_types = {e.type for e in context.missing_evidence}
    assert "water_consumption" not in available_types
    assert "water_consumption" in missing_types
    # No Evidence anywhere claims a water_consumption value of 0.
    assert not any(
        e.type == "water_consumption" and e.normalized_value == 0
        for e in context.available_evidence
    )


# ---------------------------------------------------------------------------
# T10 - entity scope survives
# ---------------------------------------------------------------------------


def test_t10_entity_scope_survives_on_evidence_object() -> None:
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
        entity_reference="A",
    )
    matching_metric = OperationalMetric(
        metric_name="feed_consumed",
        value=500,
        date=date(2026, 6, 2),
        source_file="hall_a.xlsx",
        source_row_number=3,
        entity_type="production_hall",
        entity_reference="A",
        source_label="إجمالي العلف المستهلك",
        raw_source_value="500",
        epistemic_origin="observed",
    )
    other_hall_metric = OperationalMetric(
        metric_name="feed_consumed",
        value=900,
        date=date(2026, 6, 2),
        source_file="hall_b.xlsx",
        source_row_number=4,
        entity_type="production_hall",
        entity_reference="B",
        epistemic_origin="observed",
    )
    context = collector.collect(
        situation=situation,
        metrics=[matching_metric, other_hall_metric],
        events=[],
        signals=[],
        records=[],
    )
    feed_evidence = next(
        e for e in context.available_evidence if e.type == "feed_consumption"
    )
    assert feed_evidence.entity_type == "production_hall"
    assert feed_evidence.entity_reference == "A"
    assert feed_evidence.raw_source_value == "500"
    assert context.related_entities == ["production_hall:A"]


# ---------------------------------------------------------------------------
# T11 - Feed Mill Golden Case: OBSERVED + report date unresolved, no
# contradiction
# ---------------------------------------------------------------------------


def test_t11_feed_mill_golden_case_observed_and_unresolved_date_together() -> None:
    translator = FeedMillInventoryTranslator()
    records = translator.translate([_feed_mill_balance_sheet(date_label=None)], "golden.xlsx")
    assert len(records) == 3
    assert all(isinstance(r, FeedMillInventoryRecord) for r in records)
    assert all(r.epistemic_origin == "observed" for r in records)
    assert all(r.report_date is None for r in records)
    assert all(r.report_date_status == "unresolved" for r in records)
    assert all(r.raw_material_inventory is not None for r in records)

    collector = FeedMillContextCollector(inventory_translator=translator)
    evidence = collector.collect_raw_material_inventory_evidence(
        date_range=(date(2026, 6, 1), date(2026, 6, 30))
    )
    assert evidence is not None
    assert evidence.status == "available"
    assert evidence.epistemic_origin == "observed"
    assert evidence.entity_type == "feed_mill"
    assert evidence.source_time is None
    assert evidence.source_time_status == "unresolved"
    assert evidence.provenance_warnings
    # No contradiction: an OBSERVED inventory claim with an unresolved
    # source date is exactly the required, non-contradictory Golden Case.


# ---------------------------------------------------------------------------
# T13 - M2 Operational Event origin metadata is not incorrectly promoted
# ---------------------------------------------------------------------------


def test_t13_manual_event_origin_is_unresolved_not_observed() -> None:
    manual_row = {"id": "evt-2", "source_type": "manual", "metadata": {}}
    result = to_intelligence_event(manual_row)
    assert result["context"]["origin"] is None


def test_t13_unknown_source_type_origin_is_unresolved() -> None:
    unknown_row = {"id": "evt-3", "source_type": "some_future_type", "metadata": {}}
    result = to_intelligence_event(unknown_row)
    assert result["context"]["origin"] is None


def test_t13_file_draft_without_ai_proposed_flag_is_not_promoted() -> None:
    # Metadata present but the authoritative ai_proposed flag is absent -
    # must not be guessed as inferred OR observed.
    ambiguous_row = {"id": "evt-4", "source_type": "file_draft", "metadata": {}}
    result = to_intelligence_event(ambiguous_row)
    assert result["context"]["origin"] is None


# ---------------------------------------------------------------------------
# T14 - existing OCE consumers remain backward-compatible
# ---------------------------------------------------------------------------


def test_t14_evidence_old_style_construction_still_works() -> None:
    evidence = Evidence(
        source="s",
        type="t",
        status="available",
        description="d",
        date_range=(None, None),
    )
    assert evidence.epistemic_origin is None
    assert evidence.source_time is None
    assert evidence.source_time_status is None
    assert evidence.provenance_warnings == ()
    payload = evidence.to_dict()
    assert payload["source"] == "s"
    assert payload["source_time"] is None  # present but unresolved, never fabricated


def test_t14_legacy_multi_claim_evidence_paths_still_construct() -> None:
    """mortality_trend/daily_report/company_decision_rules/
    operational_semantics/previous_production_history are legacy multi-claim
    paths deliberately left without new-field hydration in Slice 1 - they
    must still construct and behave exactly as before."""
    _, artifacts, situations, contexts = _build_situation_context(
        _declining_production_sheet(), "t14.xlsx"
    )
    assert contexts
    context = contexts[0]
    legacy_types = {
        "mortality_trend",
        "daily_report",
        "company_decision_rules",
        "operational_semantics",
    }
    present_legacy = {e.type for e in context.available_evidence} & legacy_types
    for evidence in context.available_evidence:
        if evidence.type in present_legacy:
            assert evidence.status == "available"
            # Untouched legacy fields default cleanly - no crash, no
            # fabricated provenance.
            assert evidence.canonical_field is None
    # Full context still serializes end to end (existing consumers expect this).
    serialized = context.to_dict()
    assert serialized["context_type"] == "poultry_production_drop"


# ---------------------------------------------------------------------------
# Codex Round 1 (M4 Slice 1 review) Finding 1: MISSING != OBSERVED
# ---------------------------------------------------------------------------


def _empty_water_cell_hall_sheet(hall_number: int = 11) -> ExcelSheet:
    """Water column is structurally present but the cell itself is an empty
    string - a different absence shape than a missing column entirely
    (Finding 1 test requirement 3: "empty source value")."""
    row = list(_family1_data_row(1))
    row[-1] = ""  # water_consumption cell present but empty
    rows = [
        ("شركة تجريبية - التقرير الفني اليومي",),
        ("رقم القاعة", hall_number, "اسم الحقل", "البنفسجي"),
        FAMILY1_HEADER_ROW,
        tuple(row),
    ]
    return ExcelSheet(name="خلية فارغة", rows=rows)


def test_finding1_source_backed_nonnull_metric_is_observed() -> None:
    """Requirement 1: a metric with an actual source-backed value -> OBSERVED."""
    translator = PoultryReportTranslator()
    records = translator.translate([_production_hall_sheet()], "f1_a.xlsx")
    artifacts = PoultryDerivationService().derive(records)
    bird_balance = next(m for m in artifacts.metrics if m.metric_name == "bird_balance")
    assert bird_balance.value is not None
    assert bird_balance.epistemic_origin == "observed"
    assert bird_balance.source_label is not None
    assert bird_balance.raw_source_value is not None


def test_finding1_absent_water_column_is_never_observed() -> None:
    """Requirement 2: water column structurally absent -> metric value is
    None and epistemic_origin is never "observed"."""
    translator = PoultryReportTranslator()
    records = translator.translate([_no_water_hall_sheet()], "f1_b.xlsx")
    artifacts = PoultryDerivationService().derive(records)
    water_metrics = [m for m in artifacts.metrics if m.metric_name == "water_consumption"]
    assert water_metrics  # the metric object still exists (missing-evidence detection needs it)
    for metric in water_metrics:
        assert metric.value is None
        assert metric.epistemic_origin is None
        assert metric.epistemic_origin != "observed"


def test_finding1_empty_source_cell_is_never_observed() -> None:
    """Requirement 3: water column present but the cell is an empty string
    -> coerces to None, and must never be classified OBSERVED."""
    translator = PoultryReportTranslator()
    records = translator.translate([_empty_water_cell_hall_sheet()], "f1_c.xlsx")
    assert records[0].water_consumption is None
    artifacts = PoultryDerivationService().derive(records)
    water_metrics = [m for m in artifacts.metrics if m.metric_name == "water_consumption"]
    assert water_metrics
    for metric in water_metrics:
        assert metric.value is None
        assert metric.epistemic_origin is None


def test_finding1_missing_metric_never_carries_a_fully_source_backed_claim() -> None:
    """Requirement 4: a metric with no value cannot masquerade as a fully
    source-backed OBSERVED claim - epistemic_origin must be None whenever
    value is None, with no partial/fabricated promotion."""
    translator = PoultryReportTranslator()
    records = translator.translate([_no_water_hall_sheet()], "f1_d.xlsx")
    artifacts = PoultryDerivationService().derive(records)
    for metric in artifacts.metrics:
        if metric.value is None:
            assert metric.epistemic_origin is None
        else:
            assert metric.epistemic_origin == "observed"


def test_finding1_existing_missing_evidence_detection_still_works() -> None:
    """Requirement 5: PoultryContextCollector's water-consumption
    missing-evidence detection (which filters on ``metric.value is not
    None``, unrelated to epistemic_origin) is unaffected by the Finding 1
    fix - it already ignores null metrics and continues to."""
    _, artifacts, _, _ = _build_situation_context(_no_water_hall_sheet(), "f1_e.xlsx")
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
        situation=situation,
        metrics=artifacts.metrics,
        events=artifacts.events,
        signals=artifacts.signals,
        records=[],
    )
    assert "water_consumption" not in {e.type for e in context.available_evidence}
    assert "water_consumption" in {e.type for e in context.missing_evidence}


# ---------------------------------------------------------------------------
# Codex Round 1 (M4 Slice 1 review) Finding 2: runtime validation of the
# epistemic-origin vocabulary
# ---------------------------------------------------------------------------


def test_finding2_all_four_valid_values_accepted_on_evidence() -> None:
    for origin in ("observed", "derived", "inferred", "recommended"):
        evidence = Evidence(
            source="s",
            type="t",
            status="available",
            description="d",
            date_range=(None, None),
            epistemic_origin=origin,
        )
        assert evidence.epistemic_origin == origin


def test_finding2_none_accepted_on_every_model_that_declares_it_optional() -> None:
    """Every model's epistemic_origin field is typed ``EpistemicOrigin |
    None`` with default None (metrics with no source-backed value, and
    legacy/unresolved evidence paths, both legitimately need it) - None is
    therefore valid everywhere this validator guards, by design."""
    validate_epistemic_origin(None)  # must not raise
    metric = OperationalMetric(
        metric_name="x", value=None, date=None, source_file="a", source_row_number=1
    )
    assert metric.epistemic_origin is None
    evidence = Evidence(
        source="s", type="t", status="missing", description="d", date_range=(None, None)
    )
    assert evidence.epistemic_origin is None


def test_finding2_bogus_value_raises_on_shared_validator_and_on_models() -> None:
    with pytest.raises(ValueError):
        validate_epistemic_origin("bogus")
    with pytest.raises(ValueError):
        Evidence(
            source="s",
            type="t",
            status="available",
            description="d",
            date_range=(None, None),
            epistemic_origin="bogus",
        )
    with pytest.raises(ValueError):
        OperationalMetric(
            metric_name="x",
            value=1,
            date=None,
            source_file="a",
            source_row_number=1,
            epistemic_origin="bogus",
        )
    with pytest.raises(ValueError):
        OperationalSignal(
            signal_type="x",
            severity="watch",
            message="m",
            date=None,
            source_file="a",
            source_row_number=1,
            epistemic_origin="bogus",
        )


def test_finding2_empty_string_raises() -> None:
    with pytest.raises(ValueError):
        validate_epistemic_origin("")
    with pytest.raises(ValueError):
        Evidence(
            source="s",
            type="t",
            status="available",
            description="d",
            date_range=(None, None),
            epistemic_origin="",
        )


def test_finding2_wrong_case_raises() -> None:
    """No case normalization - "Observed"/"OBSERVED" are not silently
    accepted as aliases for "observed"."""
    with pytest.raises(ValueError):
        validate_epistemic_origin("Observed")
    with pytest.raises(ValueError):
        validate_epistemic_origin("OBSERVED")
    with pytest.raises(ValueError):
        Evidence(
            source="s",
            type="t",
            status="available",
            description="d",
            date_range=(None, None),
            epistemic_origin="Observed",
        )


def test_finding2_feed_mill_record_rejects_invalid_origin() -> None:
    with pytest.raises(ValueError):
        FeedMillInventoryRecord(
            material_name="m",
            raw_material_inventory=1.0,
            source_reported_days_coverage=None,
            report_date=None,
            source_file="a",
            sheet_name="s",
            row_number=1,
            entity_type="feed_mill",
            entity_reference=None,
            report_shape="feed_mill_raw_material_inventory_snapshot",
            raw_values={},
            epistemic_origin="bogus",
        )


def test_finding2_operational_event_rejects_invalid_origin() -> None:
    with pytest.raises(ValueError):
        OperationalEvent(
            event_type="poultry_daily_report",
            entity_type=None,
            source_file="a",
            date=None,
            summary="s",
            source_row_number=1,
            epistemic_origin="bogus",
        )


def test_finding2_poultry_operational_record_rejects_invalid_origin() -> None:
    with pytest.raises(ValueError):
        PoultryOperationalRecord(
            date=None,
            day_name=None,
            age_week=None,
            age_day=None,
            bird_balance=None,
            daily_mortality=None,
            weekly_mortality=None,
            weekly_mortality_rate=None,
            daily_tray_production=None,
            box_production=None,
            daily_production_rate=None,
            standard_production_rate=None,
            broken_eggs=None,
            dirty_eggs=None,
            water_consumption=None,
            feed_received=None,
            feed_consumed=None,
            feed_per_bird_average=None,
            unknown_marker_field=None,
            source_file="a",
            sheet_name="s",
            row_number=1,
            report_shape="poultry_daily_technical_hall",
            entity_type=None,
            entity_reference=None,
            raw_values={},
            epistemic_origin="bogus",
        )


def test_finding2_invalid_origin_never_reaches_a_serialized_payload() -> None:
    """Construction fails loudly before any object - and therefore any
    to_dict() payload - can ever exist with an invalid origin."""
    with pytest.raises(ValueError):
        evidence = Evidence(
            source="s",
            type="t",
            status="available",
            description="d",
            date_range=(None, None),
            epistemic_origin="not-a-real-origin",
        )
        evidence.to_dict()  # unreachable - construction already raised above


# ---------------------------------------------------------------------------
# Codex Round 2 (M4 Slice 1 review): OBSERVED requires source-backed
# evidence, not merely a non-null normalized value. A malformed or
# manually-constructed PoultryOperationalRecord could otherwise carry a
# non-null value with no resolvable source_label/raw_source_value at all.
# ---------------------------------------------------------------------------


def _manual_record(**overrides) -> PoultryOperationalRecord:
    """Build a PoultryOperationalRecord directly (bypassing the translator)
    so tests can inject a canonical value with arbitrary/absent provenance -
    exactly the malformed-construction shape Codex proved is possible.
    """
    fields = dict(
        date=date(2026, 6, 1),
        day_name=None,
        age_week=None,
        age_day=None,
        bird_balance=None,
        daily_mortality=None,
        weekly_mortality=None,
        weekly_mortality_rate=None,
        daily_tray_production=None,
        box_production=None,
        daily_production_rate=None,
        standard_production_rate=None,
        broken_eggs=None,
        dirty_eggs=None,
        water_consumption=None,
        feed_received=None,
        feed_consumed=None,
        feed_per_bird_average=None,
        unknown_marker_field=None,
        source_file="manual.xlsx",
        sheet_name="manual",
        row_number=1,
        report_shape="poultry_daily_technical_hall",
        entity_type=None,
        entity_reference=None,
        raw_values={},
        epistemic_origin="observed",
    )
    fields.update(overrides)
    return PoultryOperationalRecord(**fields)


def test_round2_a_full_provenance_is_observed() -> None:
    assert _metric_epistemic_origin(500, "رصيد الطيور", 500) == "observed"


def test_round2_b_missing_source_label_is_not_observed() -> None:
    assert _metric_epistemic_origin(500, None, 500) is None


def test_round2_c_missing_raw_source_value_is_not_observed() -> None:
    assert _metric_epistemic_origin(500, "رصيد الطيور", None) is None


def test_round2_d_both_provenance_fields_missing_is_not_observed() -> None:
    assert _metric_epistemic_origin(500, None, None) is None


def test_round2_e_raw_source_value_zero_int_may_be_observed() -> None:
    """0 is a legitimate source value (e.g. zero mortality) - presence must
    be checked with `is not None`, never truthiness."""
    assert _metric_epistemic_origin(0, "الهلاكات اليومية", 0) == "observed"


def test_round2_f_raw_source_value_zero_float_may_be_observed() -> None:
    assert _metric_epistemic_origin(0.0, "نسبة الإنتاج اليومية", 0.0) == "observed"


def test_round2_g_empty_source_cell_yields_no_authoritative_claim() -> None:
    """An empty-string source cell coerces to value=None upstream in the
    translator, so it never reaches this function with a non-null value -
    existing M3 empty-cell semantics are preserved, and the end-to-end
    result is still never OBSERVED."""
    translator = PoultryReportTranslator()
    records = translator.translate([_empty_water_cell_hall_sheet()], "round2_g.xlsx")
    assert records[0].water_consumption is None
    artifacts = PoultryDerivationService().derive(records)
    water_metric = next(m for m in artifacts.metrics if m.metric_name == "water_consumption")
    assert water_metric.value is None
    assert water_metric.epistemic_origin is None
    assert water_metric.epistemic_origin != "observed"


def test_round2_h_manual_record_with_injected_value_but_no_provenance_is_not_observed() -> None:
    """The exact vulnerability Codex proved: a non-null canonical value with
    no resolvable source claim (raw_values is empty, so resolve_source_label
    finds nothing) must never be classified OBSERVED."""
    record = _manual_record(bird_balance=999999, raw_values={})
    metrics = PoultryDerivationService().generate_metrics([record])
    bird_balance_metric = next(m for m in metrics if m.metric_name == "bird_balance")
    assert bird_balance_metric.value == 999999
    assert bird_balance_metric.source_label is None
    assert bird_balance_metric.raw_source_value is None
    assert bird_balance_metric.epistemic_origin is None
    assert bird_balance_metric.epistemic_origin != "observed"


def test_round2_i_real_translator_records_continue_to_classify_observed() -> None:
    translator = PoultryReportTranslator()
    records = translator.translate([_production_hall_sheet()], "round2_i.xlsx")
    artifacts = PoultryDerivationService().derive(records)
    bird_balance_metric = next(m for m in artifacts.metrics if m.metric_name == "bird_balance")
    assert bird_balance_metric.value is not None
    assert bird_balance_metric.source_label is not None
    assert bird_balance_metric.raw_source_value is not None
    assert bird_balance_metric.epistemic_origin == "observed"


def test_round2_j_null_value_stays_unresolved_via_helper() -> None:
    assert _metric_epistemic_origin(None, "رصيد الطيور", 500) is None
    assert _metric_epistemic_origin(None, None, None) is None
