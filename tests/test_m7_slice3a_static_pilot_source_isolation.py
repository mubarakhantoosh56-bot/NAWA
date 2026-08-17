"""M7 Slice 3A: static pilot source isolation.

Proves NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED gates BOTH legacy static
source families - the poultry static workbook scan
(app/services/operational_truth_context.py) and the feed-mill static
workbook scan (app/oce/collectors/feed_mill_context_collector.py) - at
their actual production collector boundaries, not merely as a unit test
of `_env_bool()` in isolation. Also proves the exact Cowork finding: since
PoultryContextCollector.__init__ unconditionally builds a
FeedMillContextCollector, disabling only the poultry directory scan is
insufficient - the flag must additionally gate FeedMillContextCollector's
own static-file read boundary so static feed evidence cannot reach
context through that indirect path either.

Company Brain (knowledge/dairtna) and the M7 Slice 1 uploaded-Truth path
are proven unaffected. Every fixture is synthetic, fabricated data -
never real pilot company files - reusing the exact approved pattern
already established in tests/test_m7_slice1_upload_truth_bridge.py
(duplicated here, not imported, to avoid touching that frozen file - the
same convention already used by tests/test_m7_slice2a_explainability.py
for M6 fixtures).
"""

from __future__ import annotations

import asyncio
import dataclasses
from datetime import date
from pathlib import Path
from uuid import uuid4

import app.api.files as files_api
from app.core.dependencies import AuthContext
from app.oce.collectors import feed_mill_context_collector as fmcc
from app.oce.collectors.feed_mill_context_collector import FeedMillContextCollector
from app.oce.collectors.poultry_context_collector import PoultryContextCollector
from app.oip.models.operational_situation import OperationalSituation
from app.services import operational_truth_context as otc
from app.services.company_brain_context import DAIRTNA_POULTRY_DEPARTMENT_SLUG
from app.services.file_ingestion_service import FileIngestionService
from app.services.openai_client import AIService

FLAG_NAME = "NAWA_STATIC_PILOT_DATA_SOURCES_ENABLED"

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

SUPPORTED_FILENAME = "dairtna_poultry_daily_technical_report.xlsx"


def _family1_data_row(day: int) -> tuple:
    return (
        date(2026, 6, day), "الاثنين", 10, 70, 1000 - day, 2, 14, "1.00%",
        450, 37, "75.00%", "80.00%", 1, 1, 6000,
    )


def _write_supported_workbook(path: Path, *, day: int = 1, hall_number: int = 2, hall_label: str = "Red Hall") -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hall"
    rows = [
        ("Synthetic Test Company - Daily Technical Report",),
        ("رقم القاعة", hall_number, "اسم الحقل", hall_label),
        FAMILY1_HEADER_ROW,
        _family1_data_row(day),
    ]
    for row in rows:
        sheet.append(list(row))
    workbook.save(path)


def _write_synthetic_feed_mill_workbook(path: Path) -> None:
    """Smallest synthetic shape FeedMillContextCollector can read - a
    feed-material term in a header-like row is enough for
    collect_evidence()'s whole-workbook readability summary to succeed.
    Fabricated numbers only, never real pilot inventory data."""
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventory"
    sheet.append(["Material", "Quantity"])
    sheet.append(["corn", 100])
    sheet.append(["soya", 50])
    workbook.save(path)


def _configure_jannat_company_id(monkeypatch, company_id: object) -> None:
    monkeypatch.setattr(
        otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID=str(company_id))
    )


def _jannat_company(company_id) -> dict:
    return {"id": company_id, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}


# ---------------------------------------------------------------------------
# P3A-01..04: poultry static source participation
# ---------------------------------------------------------------------------


def _poultry_truth_result(tmp_path, monkeypatch, company_id):
    _configure_jannat_company_id(monkeypatch, company_id)
    static_dir = tmp_path / "static_pilot"
    static_dir.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(static_dir / "hall2.xlsx")
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)
    company = _jannat_company(company_id)
    return otc.assemble_truth_context(company=company, aimx_department=None)


def test_p3a_01_flag_unset_preserves_default_static_poultry_behavior(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(FLAG_NAME, raising=False)
    result = _poultry_truth_result(tmp_path, monkeypatch, uuid4())
    assert result.status == otc.STATUS_OK
    assert result.evidence_count > 0


def test_p3a_02_flag_explicit_truthy_keeps_static_poultry_scan_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(FLAG_NAME, "true")
    result = _poultry_truth_result(tmp_path, monkeypatch, uuid4())
    assert result.status == otc.STATUS_OK
    assert result.evidence_count > 0


def test_p3a_03_flag_false_disables_static_poultry_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(FLAG_NAME, "false")
    result = _poultry_truth_result(tmp_path, monkeypatch, uuid4())
    assert result.status == otc.STATUS_NO_EVIDENCE
    assert result.evidence_count == 0
    assert result.items == []


def test_p3a_04_flag_malformed_disables_static_poultry_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(FLAG_NAME, "banana")
    result = _poultry_truth_result(tmp_path, monkeypatch, uuid4())
    assert result.status == otc.STATUS_NO_EVIDENCE
    assert result.evidence_count == 0
    assert result.items == []


# ---------------------------------------------------------------------------
# P3A-05..08: feed-mill static source participation (independent of the
# poultry directory entirely - exercises FeedMillContextCollector directly).
# ---------------------------------------------------------------------------


def _feed_mill_evidence(tmp_path, monkeypatch):
    feed_dir = tmp_path / "feed_mill"
    feed_dir.mkdir(parents=True, exist_ok=True)
    _write_synthetic_feed_mill_workbook(feed_dir / "feed_inventory.xlsx")
    monkeypatch.setattr(fmcc, "FEED_MILL_DIR", feed_dir)
    collector = FeedMillContextCollector()
    return collector.collect_evidence(date_range=(None, None))


def test_p3a_05_flag_unset_preserves_default_feed_mill_static_behavior(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(FLAG_NAME, raising=False)
    evidence = _feed_mill_evidence(tmp_path, monkeypatch)
    assert evidence is not None
    assert evidence.type == "feed_mill_inventory"


def test_p3a_06_flag_explicit_truthy_keeps_feed_mill_static_evidence_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(FLAG_NAME, "true")
    evidence = _feed_mill_evidence(tmp_path, monkeypatch)
    assert evidence is not None
    assert evidence.type == "feed_mill_inventory"


def test_p3a_07_flag_false_disables_static_feed_mill_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(FLAG_NAME, "false")
    evidence = _feed_mill_evidence(tmp_path, monkeypatch)
    assert evidence is None


def test_p3a_08_flag_malformed_disables_static_feed_mill_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(FLAG_NAME, "banana")
    evidence = _feed_mill_evidence(tmp_path, monkeypatch)
    assert evidence is None


# ---------------------------------------------------------------------------
# P3A-09: the exact Cowork finding - PoultryContextCollector.__init__
# unconditionally builds a FeedMillContextCollector, so the flag must gate
# BOTH static families even when reached only through the poultry
# collector's own unconditional relationship, not just via the top-level
# directory-scan loop.
# ---------------------------------------------------------------------------


def test_p3a_09_poultry_collector_never_leaks_static_feed_evidence_when_disabled(tmp_path, monkeypatch) -> None:
    poultry_dir = tmp_path / "poultry_operations"
    poultry_dir.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(poultry_dir / "hall2.xlsx")

    feed_dir = tmp_path / "feed_mill"
    feed_dir.mkdir(parents=True, exist_ok=True)
    _write_synthetic_feed_mill_workbook(feed_dir / "feed_inventory.xlsx")
    monkeypatch.setattr(fmcc, "FEED_MILL_DIR", feed_dir)

    # Sanity: with the flag enabled, PoultryContextCollector's own
    # unconditional feed_mill_collector DOES surface feed evidence -
    # proving the fixtures are real and the absence below is a genuine
    # effect of the flag, not an accident of the fixture shape.
    monkeypatch.setenv(FLAG_NAME, "true")
    enabled_collector = PoultryContextCollector()
    enabled_situation = OperationalSituation(
        situation_type="operational_snapshot", severity="info", title="t", summary="s",
        evidence=[], recommended_next_checks=[], start_date=None, end_date=None,
    )
    enabled_context = enabled_collector.collect(
        situation=enabled_situation, metrics=[], events=[], signals=[], records=[],
    )
    enabled_types = {evidence.type for evidence in enabled_context.available_evidence}
    assert "feed_mill_inventory" in enabled_types

    # The actual proof: flag disabled - PoultryContextCollector is used
    # completely normally (fresh instance, same unconditional
    # self.feed_mill_collector relationship), but NO feed-mill evidence
    # may leak through it.
    monkeypatch.setenv(FLAG_NAME, "false")
    disabled_collector = PoultryContextCollector()
    disabled_situation = OperationalSituation(
        situation_type="operational_snapshot", severity="info", title="t", summary="s",
        evidence=[], recommended_next_checks=[], start_date=None, end_date=None,
    )
    disabled_context = disabled_collector.collect(
        situation=disabled_situation, metrics=[], events=[], signals=[], records=[],
    )
    disabled_types = {evidence.type for evidence in disabled_context.available_evidence}
    assert "feed_mill_inventory" not in disabled_types
    assert "raw_material_inventory" not in disabled_types

    # And end-to-end through the real production entry point: with the
    # poultry static directory ALSO present, disabling the flag must
    # produce NO poultry static evidence AND no feed-mill evidence.
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", poultry_dir)
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    result = otc.assemble_truth_context(company=_jannat_company(company_id), aimx_department=None)
    assert result.status == otc.STATUS_NO_EVIDENCE
    assert result.evidence_count == 0
    result_types = {item.get("type") for item in result.items}
    assert "feed_mill_inventory" not in result_types
    assert "raw_material_inventory" not in result_types


# ---------------------------------------------------------------------------
# P3A-10: disabling static pilot sources must NOT disable the M7 Slice 1
# uploaded-Truth path. Reuses the real upload -> structured-persistence ->
# Truth pipeline exactly as tests/test_m7_slice1_upload_truth_bridge.py
# does - never a hand-built Truth item.
# ---------------------------------------------------------------------------


class _FakeDB:
    """Minimal in-memory stand-in for an asyncpg pool/connection - the
    exact same shape as test_m7_slice1_upload_truth_bridge.py's _FakeDB,
    duplicated here to avoid importing from that frozen test file."""

    def __init__(self) -> None:
        import json

        self._json = json
        self.companies: dict[str, dict] = {}
        self.departments: list[dict] = []
        self.raw_inputs: list[dict] = []
        self.structured_record_drafts: list[dict] = []
        self._clock_counter = 0

    def _next_created_at(self) -> str:
        from datetime import datetime, timedelta, timezone

        self._clock_counter += 1
        moment = datetime(2026, 6, 1, tzinfo=timezone.utc) + timedelta(seconds=self._clock_counter)
        return moment.isoformat()

    async def fetchrow(self, query: str, *args):
        q = query
        if "FROM companies" in q:
            return self.companies.get(str(args[0]))
        if "FROM departments" in q and "id = $2" in q:
            company_id, department_id = args
            for row in self.departments:
                if str(row["company_id"]) == str(company_id) and str(row["id"]) == str(department_id):
                    return dict(row)
            return None
        if "FROM departments" in q and "slug = $2" in q:
            company_id, slug = args
            for row in self.departments:
                if str(row["company_id"]) == str(company_id) and row["slug"] == slug:
                    return dict(row)
            return None
        if "INSERT INTO raw_inputs" in q:
            (
                company_id, division_id, department_id, source_type, source_ref,
                raw_content, file_id, created_by, processing_status, language,
            ) = args
            row = {
                "id": uuid4(), "company_id": company_id, "division_id": division_id,
                "department_id": department_id, "source_type": source_type,
                "source_ref": source_ref, "raw_content": raw_content, "file_id": file_id,
                "created_by": created_by, "processing_status": processing_status,
                "language": language, "created_at": self._next_created_at(),
            }
            self.raw_inputs.append(row)
            return dict(row)
        if "INSERT INTO structured_record_drafts" in q:
            (
                company_id, raw_input_id, division_id, department_id, record_type,
                extracted_payload, created_by,
            ) = args
            row = {
                "id": uuid4(), "company_id": company_id, "raw_input_id": raw_input_id,
                "division_id": division_id, "department_id": department_id,
                "record_type": record_type, "extracted_payload": extracted_payload,
                "status": "draft", "created_by": created_by, "created_at": self._next_created_at(),
            }
            self.structured_record_drafts.append(row)
            return dict(row)
        if "FROM structured_record_drafts" in q and "file_id" in q:
            company_id, file_id_str, record_type = args
            matches = [
                row for row in self.structured_record_drafts
                if str(row["company_id"]) == str(company_id)
                and self._json.loads(row["extracted_payload"]).get("file_id") == file_id_str
                and row["record_type"] == record_type
            ]
            return dict(matches[-1]) if matches else None
        raise AssertionError(f"_FakeDB.fetchrow received an unexpected query: {q[:200]!r}")

    async def fetch(self, query: str, *args):
        q = query
        if "FROM structured_record_drafts" in q and "record_type = $3" in q:
            company_id, department_id, record_type = args
            matches = [
                dict(row) for row in self.structured_record_drafts
                if str(row["company_id"]) == str(company_id)
                and str(row["department_id"]) == str(department_id)
                and row["record_type"] == record_type
                and row["status"] != "rejected"
            ]
            matches.sort(key=lambda row: (row["created_at"], str(row["id"])), reverse=True)
            return matches
        raise AssertionError(f"_FakeDB.fetch received an unexpected query: {q[:200]!r}")


def _seed_tenant(fake_db: _FakeDB, *, company_id, department_slug: str, department_id=None):
    fake_db.companies[str(company_id)] = {
        "id": company_id, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {},
    }
    department_id = department_id or uuid4()
    fake_db.departments.append({
        "id": department_id, "company_id": company_id, "slug": department_slug,
        "name": department_slug, "department_type": "custom",
    })
    return department_id


def _run_upload_gate(*, fake_db, auth_context, department_id, xlsx_path):
    file_service = FileIngestionService(fake_db)
    file_id = uuid4()
    file_record = {
        "id": file_id,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    summary = asyncio.run(
        files_api._run_nco_lite_after_upload_if_applicable(
            file_service=file_service,
            auth_context=auth_context,
            department_id=department_id,
            file_record=file_record,
            source_path=xlsx_path,
            filename=xlsx_path.name,
        )
    )
    return summary, file_id


def test_p3a_10_disabling_static_sources_does_not_disable_uploaded_truth(tmp_path, monkeypatch) -> None:
    """The M7 Slice 1 upload -> Truth bridge must keep working, with real
    source_file_id provenance, even with static pilot sources fully
    disabled - and a static poultry fixture AND a static feed-mill fixture
    both present (proving their absence from the result is the flag's
    doing, not merely an empty directory)."""
    monkeypatch.setenv(FLAG_NAME, "false")

    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    static_dir.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(static_dir / "static_hall.xlsx", hall_number=2, hall_label="Static Hall")
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

    feed_dir = tmp_path / "feed_mill"
    feed_dir.mkdir(parents=True, exist_ok=True)
    _write_synthetic_feed_mill_workbook(feed_dir / "feed_inventory.xlsx")
    monkeypatch.setattr(fmcc, "FEED_MILL_DIR", feed_dir)

    upload_path = tmp_path / "upload" / SUPPORTED_FILENAME
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(upload_path, hall_number=99, hall_label="Fresh Upload Hall")
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=upload_path,
    )
    assert summary["structured_ingestion_status"] == "succeeded"

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="p3a-10")
    )
    assert uploaded_records, "the real upload pipeline must produce uploaded records"

    truth_result = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )

    assert truth_result.status == otc.STATUS_OK
    upload_items = [item for item in truth_result.items if item.get("source_file_id") == str(file_id)]
    assert upload_items, "the upload must still produce Truth with its source_file_id provenance"

    # Static poultry evidence (from the static hall workbook, a DIFFERENT
    # file with no source_file_id) and feed-mill evidence must both be
    # absent - proving the flag, not just directory absence, is the cause.
    item_types = {item.get("type") for item in truth_result.items}
    assert "feed_mill_inventory" not in item_types
    assert "raw_material_inventory" not in item_types
    non_upload_items = [item for item in truth_result.items if item.get("source_file_id") != str(file_id)]
    for item in non_upload_items:
        assert item.get("source_file") != str(static_dir / "static_hall.xlsx"), (
            "static-file-sourced evidence must not appear alongside the upload"
        )


# ---------------------------------------------------------------------------
# Company Brain non-regression: knowledge/dairtna documents are never
# gated by this flag - they are M5 Company Brain material, not legacy
# operational static Truth.
# ---------------------------------------------------------------------------


def test_company_brain_knowledge_documents_are_never_gated_by_the_static_flag(monkeypatch) -> None:
    """PoultryContextCollector._knowledge_evidence resolves
    knowledge/dairtna/*.md availability via a plain Path.exists() check -
    it never calls _env_bool at all, so the same items are returned
    whether the static-pilot flag is enabled or disabled."""
    collector = PoultryContextCollector()

    monkeypatch.setenv(FLAG_NAME, "true")
    enabled_types = {evidence.type for evidence in collector._knowledge_evidence(None, None)}

    monkeypatch.setenv(FLAG_NAME, "false")
    disabled_types = {evidence.type for evidence in collector._knowledge_evidence(None, None)}

    assert enabled_types == disabled_types
