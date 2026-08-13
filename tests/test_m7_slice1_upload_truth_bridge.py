"""M7 Slice 1 acceptance tests: Pilot Runtime Activation + User Upload ->
Truth Bridge.

Proves the real Golden Journey: a real uploaded Dairtna daily technical
report -> the real shape-based translator/validator (KAE) -> the real
structured-record-draft persistence (app/api/files.py) -> the real
Operational Truth Context assembly (app/services/operational_truth_context.py)
-> the real Decision Context / M6 reasoning reference catalog
(app/services/decision_context.py) -> the real M6 provenance validator
(app/services/reasoning_validation.py).

Only the database CONNECTION is faked (a plain in-memory stand-in
implementing asyncpg's fetchrow/fetch, matching the existing
_FakeDbPool/_FakeChatDbPool convention used throughout the M4/M5/M6 test
suites) - every repository, service, translator, and validator function
under test runs for real, unmocked. Excel fixtures are synthetic (fabricated
numbers), never real pilot company data.
"""

from __future__ import annotations

import asyncio
import dataclasses
import inspect
import json
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import pytest

import app.api.files as files_api
from app.core.dependencies import AuthContext
from app.nco.pipeline import NCOLitePipeline
from app.oip.models.operational_record import PoultryOperationalRecord
from app.services import operational_truth_context as otc
from app.services.company_brain_context import DAIRTNA_POULTRY_DEPARTMENT_SLUG
from app.services.decision_context import build_decision_context
from app.services.file_ingestion_service import FileIngestionService
from app.services.openai_client import AIService
from app.services.reasoning_validation import validate_reasoning_assessment

# ---------------------------------------------------------------------------
# Shared fixtures / fakes
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


def _write_unsupported_workbook(path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    for row in [("col1", "col2", "col3"), ("v1", "v2", "v3")]:
        sheet.append(list(row))
    workbook.save(path)


def _configure_jannat_company_id(monkeypatch, company_id: object) -> None:
    monkeypatch.setattr(
        otc, "settings", dataclasses.replace(otc.settings, JANNAT_COMPANY_ID=str(company_id))
    )


class _FakeDB:
    """Minimal in-memory stand-in for an asyncpg pool/connection - supports
    only the exact query shapes the real repositories under test issue.
    Any unexpected query raises loudly rather than silently returning None,
    so a test never passes by accident on a query it didn't intend to hit.
    """

    def __init__(self) -> None:
        self.companies: dict[str, dict] = {}
        self.departments: list[dict] = []
        self.raw_inputs: list[dict] = []
        self.structured_record_drafts: list[dict] = []
        # Monotonically increasing synthetic timestamps so insertion order
        # is always distinguishable - real Postgres created_at has
        # microsecond precision and effectively never ties in practice for
        # sequential test inserts, and this fake needs a deterministic
        # equivalent to exercise the real ORDER BY created_at DESC, id DESC
        # in list_structured_drafts_by_record_type faithfully.
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
                and json.loads(row["extracted_payload"]).get("file_id") == file_id_str
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
            # Mirrors the real query's ORDER BY created_at DESC, id DESC
            # exactly (M7-02 Correction Round 2 / M7-09) - newest draft
            # first, UUID id as a deterministic (not temporal) tie-breaker.
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


# ---------------------------------------------------------------------------
# U1: supported upload is recognized and persisted as structured Truth
# ---------------------------------------------------------------------------


def test_u1_supported_upload_recognized_persists_structured_truth(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )

    assert summary is not None
    assert summary["structured_ingestion_status"] == "succeeded"
    assert len(fake_db.structured_record_drafts) == 1
    payload = json.loads(fake_db.structured_record_drafts[0]["extracted_payload"])
    assert payload["file_id"] == str(file_id)
    assert payload["filename"] == SUPPORTED_FILENAME
    assert payload["ingestion_state"] == "supported_with_data"
    assert len(payload["records"]) == 1
    assert payload["records"][0]["epistemic_origin"] == "observed"


# ---------------------------------------------------------------------------
# U2 / U12: unsupported spreadsheet never fabricates structured Truth, and
# cannot produce a T# merely because RAG/file upload otherwise succeeded.
# ---------------------------------------------------------------------------


def test_u2_unsupported_spreadsheet_produces_no_structured_truth(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_unsupported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )

    assert summary is not None
    assert summary["structured_ingestion_status"] == "unsupported"
    assert fake_db.structured_record_drafts == []


def test_u12_unsupported_file_cannot_produce_t_ref_via_rag(tmp_path, monkeypatch) -> None:
    """Even though the file itself uploads successfully and could be used by
    RAG, no structured_record_drafts row exists for it - so it can never be
    read back as Operational Truth by _load_uploaded_truth_records, and no
    T# can ever trace to it."""
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_unsupported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    _run_upload_gate(fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path)

    drafts = asyncio.run(fake_db.fetch(
        "SELECT * FROM structured_record_drafts WHERE company_id = $1 AND department_id = $2 AND record_type = $3 AND status != 'rejected'",
        company_id, department_id, otc.POULTRY_DAILY_REPORT_RECORD_TYPE,
    ))
    assert drafts == []


# ---------------------------------------------------------------------------
# U3 / U4 / U5: tenant, department, and no-department scope isolation
# ---------------------------------------------------------------------------


def test_u3_tenant_isolation_non_jannat_company_no_persistence(tmp_path, monkeypatch) -> None:
    """A non-pilot tenant, even with a perfectly-shaped supported file and a
    department slug that happens to match, never gets persisted structured
    Truth - JANNAT_COMPANY_ID is configured for a DIFFERENT company."""
    other_company_id = uuid4()
    configured_company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(
        fake_db, company_id=other_company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG
    )
    _configure_jannat_company_id(monkeypatch, configured_company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(other_company_id), user_id=str(uuid4()), permissions=[])

    summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )

    assert summary is None
    assert fake_db.structured_record_drafts == []


def test_u4_caesar_department_isolation_no_persistence(tmp_path, monkeypatch) -> None:
    """The real Jannat tenant, uploading into its Caesar Beverage department
    (not Dairtna Poultry), never gets persisted structured Truth - Caesar
    cannot feed Dairtna Truth."""
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug="caesar-beverage")
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )

    assert summary is None
    assert fake_db.structured_record_drafts == []


def test_u5_no_department_scope_cannot_acquire_dairtna_truth(tmp_path, monkeypatch) -> None:
    """A CEO/no-department upload (department_id=None) - the RBAC-verified
    absence of a department scope - must never accidentally acquire Dairtna
    structured Truth, even with a perfectly Dairtna-shaped supported file."""
    company_id = uuid4()
    fake_db = _FakeDB()
    _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=None, xlsx_path=xlsx_path,
    )

    assert summary is None
    assert fake_db.structured_record_drafts == []


# ---------------------------------------------------------------------------
# U6: provenance
# ---------------------------------------------------------------------------


def test_u6_persisted_evidence_carries_full_provenance(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    _summary, file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )

    draft = fake_db.structured_record_drafts[0]
    assert str(draft["company_id"]) == str(company_id)
    assert str(draft["department_id"]) == str(department_id)
    payload = json.loads(draft["extracted_payload"])
    assert payload["file_id"] == str(file_id)
    assert payload["filename"] == SUPPORTED_FILENAME
    record = payload["records"][0]
    assert record["report_shape"] == "poultry_daily_technical_hall"
    assert record["entity_type"] == "production_hall"
    assert record["entity_reference"] == "2"
    assert record["date"] == "2026-06-01"
    assert record["source_file"] == SUPPORTED_FILENAME or Path(record["source_file"]).name == xlsx_path.name


# ---------------------------------------------------------------------------
# U7: freshness / unresolved source time is preserved, never faked current
# ---------------------------------------------------------------------------


def _jannat_company(company_id) -> dict:
    return {"id": company_id, "slug": "jannat-al-firdaws", "name": "Jannat Al-Firdaws", "metadata": {}}


def _translated_records(tmp_path: Path, *, filename: str = SUPPORTED_FILENAME) -> list[PoultryOperationalRecord]:
    """Run the real shape-based translator/validator (KAE) on a real
    supported .xlsx, exactly as app/api/files.py does after a real upload -
    never a hand-built record, so raw_values/source_label provenance is
    genuinely populated (a hand-built record with raw_values={} would make
    every metric's epistemic_origin unresolved, not observed - see
    PoultryDerivationService._metric_epistemic_origin)."""
    path = tmp_path / filename
    _write_supported_workbook(path)
    return NCOLitePipeline().run_kae(path).records


def test_u7_missing_date_record_is_unresolved_source_time(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))

    record = dataclasses.replace(_translated_records(tmp_path)[0], date=None)
    result = otc.assemble_truth_context(
        company=_jannat_company(company_id), aimx_department=None, uploaded_records=[record],
    )

    assert result.status == "ok"
    matching = [item for item in result.items if item.get("source_file") == record.source_file]
    assert matching
    for item in matching:
        assert item["source_time_status"] == "unresolved"
        assert item["source_time"] is None


# ---------------------------------------------------------------------------
# U8: epistemic origin correctness
# ---------------------------------------------------------------------------


def test_u8_uploaded_record_epistemic_origin_is_observed_and_usable(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))

    record = _translated_records(tmp_path)[0]
    result = otc.assemble_truth_context(
        company=_jannat_company(company_id), aimx_department=None, uploaded_records=[record],
    )

    matching = [
        item for item in result.items
        if item.get("source_file") == record.source_file and item.get("type") == "bird_balance"
    ]
    assert matching
    for item in matching:
        assert item["epistemic_origin"] == "observed"
        assert item["status"] == "available"


# ---------------------------------------------------------------------------
# U9: idempotency - reprocessing the same file_id never multiplies Truth
# ---------------------------------------------------------------------------


def test_u9_idempotent_reprocessing_does_not_duplicate_structured_truth(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    file_service = FileIngestionService(fake_db)
    file_id = uuid4()
    file_record = {
        "id": file_id,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    for _ in range(2):
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
        assert summary["structured_ingestion_status"] == "succeeded"

    assert len(fake_db.structured_record_drafts) == 1


def test_u9_unrelated_generic_capture_draft_does_not_block_poultry_persistence(tmp_path, monkeypatch) -> None:
    """Regression test for a real bug caught by the M7 Golden structural
    probe against the live pilot DB: the generic UnifiedDataCaptureService/
    FileOperationalAnalyzer capture path can independently create its own
    structured_record_drafts row for the SAME file_id (e.g. record_type
    "issue", from unrelated free-text classification of the same upload).
    The idempotency lookup used by _persist_structured_ingestion_result
    must be scoped by record_type, or it wrongly treats that unrelated
    draft as "this poultry ingestion already ran" and silently skips real
    persistence - which is exactly what happened before this fix."""
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    file_service = FileIngestionService(fake_db)
    file_id = uuid4()
    file_record = {
        "id": file_id,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    # Simulate the generic capture path already having written an unrelated
    # draft for this exact file_id, as the real pilot DB showed happens.
    fake_db.structured_record_drafts.append({
        "id": uuid4(), "company_id": company_id, "raw_input_id": uuid4(),
        "division_id": None, "department_id": department_id, "record_type": "issue",
        "extracted_payload": json.dumps({"file_id": str(file_id)}, ensure_ascii=False),
        "status": "draft", "created_by": uuid4(), "created_at": "2026-06-01T00:00:00Z",
    })

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

    assert summary["structured_ingestion_status"] == "succeeded"
    poultry_drafts = [
        row for row in fake_db.structured_record_drafts
        if row["record_type"] == otc.POULTRY_DAILY_REPORT_RECORD_TYPE
    ]
    assert len(poultry_drafts) == 1, "the unrelated 'issue' draft must not block real poultry persistence"


# ---------------------------------------------------------------------------
# M7-01 (Correction Round 1): stable end-to-end upload provenance. Every
# step is real - real upload gate, real KAE, real persistence, real
# AIService._load_uploaded_truth_records reconstruction, real Truth
# assembly, real Decision Context / reasoning reference catalog. No T# is
# ever injected by hand.
# ---------------------------------------------------------------------------


def _upload_and_reach_truth_refs(tmp_path, monkeypatch, *, filename: str = SUPPORTED_FILENAME):
    """Shared P1-P6 helper: real upload gate -> real fake-DB persistence ->
    real AIService._load_uploaded_truth_records reconstruction -> real
    assemble_truth_context -> real build_decision_context. Returns
    (file_id, department_id, truth_refs, truth_items) so each test asserts
    on the exact provenance fields it cares about."""
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))

    xlsx_path = tmp_path / filename
    _write_supported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )
    assert summary["structured_ingestion_status"] == "succeeded"

    # The temp upload file is gone now (P6) - proves reconstruction never
    # depends on the transient parser path still existing.
    xlsx_path.unlink()

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-01-probe")
    )

    truth_result = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]
    return file_id, department_id, company_id, truth_refs, truth_result.items


def _refs_for_file(truth_refs: dict, truth_items: list[dict], file_id) -> list[str]:
    return [
        ref for index, ref in enumerate(truth_refs, start=1)
        if truth_items[index - 1].get("source_file_id") == str(file_id)
    ]


def test_p1_upload_derived_t_ref_retains_exact_source_file_uuid(tmp_path, monkeypatch) -> None:
    file_id, _department_id, _company_id, truth_refs, truth_items = _upload_and_reach_truth_refs(tmp_path, monkeypatch)
    refs = _refs_for_file(truth_refs, truth_items, file_id)
    assert refs, "expected at least one T# carrying this upload's exact file_id"
    for ref in refs:
        assert truth_refs[ref]["is_usable_evidence"] is True


def test_p2_original_filename_survives_to_final_truth_item(tmp_path, monkeypatch) -> None:
    file_id, _department_id, _company_id, truth_refs, truth_items = _upload_and_reach_truth_refs(tmp_path, monkeypatch)
    refs = _refs_for_file(truth_refs, truth_items, file_id)
    assert refs
    matching_items = [truth_items[int(ref[1:]) - 1] for ref in refs]
    assert all(item.get("source_filename") == SUPPORTED_FILENAME for item in matching_items)


def test_p3_validated_department_id_survives_to_final_truth_item(tmp_path, monkeypatch) -> None:
    file_id, department_id, _company_id, truth_refs, truth_items = _upload_and_reach_truth_refs(tmp_path, monkeypatch)
    refs = _refs_for_file(truth_refs, truth_items, file_id)
    assert refs
    matching_items = [truth_items[int(ref[1:]) - 1] for ref in refs]
    assert all(item.get("source_department_id") == str(department_id) for item in matching_items)


def test_p4_company_identity_survives_to_final_truth_item(tmp_path, monkeypatch) -> None:
    file_id, _department_id, company_id, truth_refs, truth_items = _upload_and_reach_truth_refs(tmp_path, monkeypatch)
    refs = _refs_for_file(truth_refs, truth_items, file_id)
    assert refs
    matching_items = [truth_items[int(ref[1:]) - 1] for ref in refs]
    assert all(item.get("source_company_id") == str(company_id) for item in matching_items)


def test_p5_identical_filenames_different_file_ids_stay_distinguishable(tmp_path, monkeypatch) -> None:
    """Two uploads sharing the exact same filename must remain distinguishable
    at final T# provenance, since real users will re-upload same-named
    daily reports on different days."""
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    # Same filename both times (the exact scenario under test), but
    # different halls - a real Dairtna user uploads one file per hall per
    # day, conventionally named the same way each time. Same hall+day would
    # be a genuine conflicting-claim scenario where M4's existing
    # multi-claim-disagreement discipline (never fabricate a single-file
    # link when several source claims disagree - see
    # PoultryContextCollector._metric_provenance_fields, unrelated to this
    # provenance fix) legitimately leaves the aggregated evidence entry's
    # source_file_id unset rather than guessing - not what this test proves.
    file_ids = []
    for index, (hall_number, hall_label) in enumerate(((2, "Red Hall"), (3, "White Hall"))):
        xlsx_path = tmp_path / f"upload_{index}" / SUPPORTED_FILENAME
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)
        _write_supported_workbook(xlsx_path, hall_number=hall_number, hall_label=hall_label)
        summary, file_id = _run_upload_gate(
            fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
        )
        assert summary["structured_ingestion_status"] == "succeeded"
        file_ids.append(file_id)

    assert file_ids[0] != file_ids[1]

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-01-p5")
    )
    truth_result = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]

    refs_by_file = {
        str(fid): _refs_for_file(truth_refs, truth_result.items, fid) for fid in file_ids
    }
    assert refs_by_file[str(file_ids[0])], "first same-named upload must still be traceable"
    assert refs_by_file[str(file_ids[1])], "second same-named upload must still be traceable"
    assert set(refs_by_file[str(file_ids[0])]).isdisjoint(refs_by_file[str(file_ids[1])])


def test_p6_provenance_resolves_after_temp_parser_path_is_gone(tmp_path, monkeypatch) -> None:
    """The helper already deletes the temp upload file before reconstruction
    runs (see _upload_and_reach_truth_refs) - this test just makes that
    guarantee explicit and asserts it did not silently degrade to
    'no_evidence'."""
    file_id, _department_id, _company_id, truth_refs, truth_items = _upload_and_reach_truth_refs(tmp_path, monkeypatch)
    refs = _refs_for_file(truth_refs, truth_items, file_id)
    assert refs


def test_p7_unsupported_file_has_no_structured_truth_provenance(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_unsupported_workbook(xlsx_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=xlsx_path,
    )
    assert summary["structured_ingestion_status"] == "unsupported"
    assert fake_db.structured_record_drafts == []

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-01-p7")
    )
    assert uploaded_records == []


# ---------------------------------------------------------------------------
# M7-02 (Correction Round 1): a fresh upload must survive the bounded
# available-evidence cap even when static pilot volume alone exceeds it.
# Both the static volume AND the upload go through the real KAE/Truth
# pipeline - no hand-built Evidence/operational_truth_context objects.
# ---------------------------------------------------------------------------


def _write_static_pilot_volume(directory: Path, *, count: int = 25) -> None:
    """Write `count` distinct real supported hall workbooks (real KAE parses
    every one of them) into `directory`, standing in for a large volume of
    legacy static pilot evidence - large enough that available evidence
    alone exceeds MAX_AVAILABLE_EVIDENCE_ITEMS (30) once collected."""
    directory.mkdir(parents=True, exist_ok=True)
    for hall_number in range(1, count + 1):
        _write_supported_workbook(
            directory / f"static_hall_{hall_number}.xlsx",
            hall_number=hall_number,
            hall_label=f"Static Hall {hall_number}",
        )


def test_t1_fresh_upload_survives_truncation_against_large_static_volume(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

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
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-02-t1")
    )
    truth_result = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )

    available = [item for item in truth_result.items if item.get("status") == "available"]
    assert len(available) <= otc.MAX_AVAILABLE_EVIDENCE_ITEMS, "bound must still be enforced"
    upload_items = [item for item in available if item.get("source_file_id") == str(file_id)]
    assert upload_items, "the fresh upload must survive the bound and appear in available evidence"

    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]
    upload_refs = _refs_for_file(truth_refs, truth_result.items, file_id)
    assert upload_refs, "the fresh upload must receive a T#"
    assert any(truth_refs[ref]["is_usable_evidence"] for ref in upload_refs)


def test_t2_multiple_uploads_receive_deterministic_precedence_under_cap(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])
    file_ids = []
    for index, (hall_number, hall_label) in enumerate(((97, "Upload Hall A"), (98, "Upload Hall B"))):
        upload_path = tmp_path / f"upload_{index}" / SUPPORTED_FILENAME
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        _write_supported_workbook(upload_path, hall_number=hall_number, hall_label=hall_label)
        summary, file_id = _run_upload_gate(
            fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=upload_path,
        )
        assert summary["structured_ingestion_status"] == "succeeded"
        file_ids.append(file_id)

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-02-t2")
    )
    truth_result = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )
    available = [item for item in truth_result.items if item.get("status") == "available"]
    assert len(available) <= otc.MAX_AVAILABLE_EVIDENCE_ITEMS

    for file_id in file_ids:
        matching = [item for item in available if item.get("source_file_id") == str(file_id)]
        assert matching, f"upload {file_id} must survive the bound"

    # Determinism: re-running assembly with the identical inputs produces
    # the identical surviving set/order.
    truth_result_again = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )
    assert truth_result_again.items == truth_result.items


def test_t3_unsupported_upload_receives_no_precedence(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

    upload_path = tmp_path / "upload" / SUPPORTED_FILENAME
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    _write_unsupported_workbook(upload_path)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])
    summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=upload_path,
    )
    assert summary["structured_ingestion_status"] == "unsupported"

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-02-t3")
    )
    assert uploaded_records == []

    truth_result_with_no_upload = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=uploaded_records,
    )
    truth_result_without_call = otc.assemble_truth_context(
        company=company, aimx_department=None, uploaded_records=None,
    )
    assert truth_result_with_no_upload.items == truth_result_without_call.items


def test_t4_no_uploaded_records_preserves_existing_m4_ordering(tmp_path, monkeypatch) -> None:
    """With no uploaded_records at all, output must be byte-for-byte the
    same as it always was - the M7-02 partition is a no-op when there is
    nothing upload-derived to prioritize."""
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

    company = _jannat_company(company_id)
    result_no_arg = otc.assemble_truth_context(company=company, aimx_department=None)
    result_none = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=None)
    result_empty = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=[])

    assert result_no_arg.items == result_none.items == result_empty.items
    assert len(result_no_arg.items) <= otc.MAX_AVAILABLE_EVIDENCE_ITEMS + otc.MAX_MISSING_EVIDENCE_ITEMS


def test_t5_missing_evidence_semantics_unchanged(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

    upload_path = tmp_path / "upload" / SUPPORTED_FILENAME
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(upload_path, hall_number=99, hall_label="Fresh Upload Hall")
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])
    _summary, _file_id = _run_upload_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id, xlsx_path=upload_path,
    )

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-02-t5")
    )
    with_upload = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=uploaded_records)
    without_upload = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=None)

    missing_with = [item for item in with_upload.items if item.get("status") == "missing"]
    missing_without = [item for item in without_upload.items if item.get("status") == "missing"]
    assert missing_with == missing_without, "missing-evidence set must be unaffected by upload precedence"


def test_t6_m6_accepts_surviving_upload_t_ref_under_large_static_volume(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

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
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="m7-02-t6")
    )
    truth_result = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=uploaded_records)
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]
    usable_upload_refs = [
        ref for ref in _refs_for_file(truth_refs, truth_result.items, file_id)
        if truth_refs[ref]["is_usable_evidence"]
    ]
    assert usable_upload_refs

    parsed = {
        "raw_decision": {
            "reasoning_assessment": {
                "reasoning_state": "aligned",
                "operational_assessment": "Fresh upload hall readings observed.",
                "company_brain_alignment": "n/a",
                "tensions": [],
                "evidence_gaps": [],
                "risk_assessment": "n/a",
                "confidence": 70,
                "recommendation_basis": {
                    "evidence_basis": [usable_upload_refs[0]],
                    "company_basis": [],
                    "missing_evidence": [],
                },
            }
        }
    }
    ok, errors = validate_reasoning_assessment(parsed, decision_context)
    assert ok, errors


# ---------------------------------------------------------------------------
# M7-02 Correction Round 2 (M7-09): a fresh upload must reliably survive
# bounding even when OLDER upload-derived evidence alone already exceeds the
# cap - not just older STATIC evidence (Round 1's T1-T6). Fixed by ordering
# app.repositories.unified_data_capture_repository.
# list_structured_drafts_by_record_type newest-draft-first
# (created_at DESC, id DESC) - a context-selection ordering only, never a
# change to source report date / source_time_status / epistemic origin.
# ---------------------------------------------------------------------------


def _upload_supported_via_gate(*, fake_db, auth_context, department_id, tmp_path, subdir, hall_number, hall_label):
    """Real gate call (files_api._run_nco_lite_after_upload_if_applicable) -
    the same "lowest honest persistence layer" every other test in this file
    uses, never a hand-inserted draft row. Used to seed many distinct older
    uploads without the weight of 30+ full HTTP round trips - the CURRENT/
    newest upload in every Golden-path test still goes through the real
    endpoint (see test_m7_04_full_golden_journey_through_real_endpoints)."""
    path = tmp_path / subdir / SUPPORTED_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(path, hall_number=hall_number, hall_label=hall_label)
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
            source_path=path,
            filename=path.name,
        )
    )
    assert summary["structured_ingestion_status"] == "succeeded"
    return file_id


def _seed_many_older_uploads(*, fake_db, auth_context, department_id, tmp_path, count: int, hall_start: int = 100) -> list:
    """Seed `count` distinct older supported uploads (distinct halls, so
    none collide with M4's existing per-entity headline-metric dedup),
    oldest-seeded first. Returns their file_ids in seed order."""
    file_ids = []
    for index in range(count):
        file_id = _upload_supported_via_gate(
            fake_db=fake_db, auth_context=auth_context, department_id=department_id,
            tmp_path=tmp_path, subdir=f"older_{index}",
            hall_number=hall_start + index, hall_label=f"Older Hall {index}",
        )
        file_ids.append(file_id)
    return file_ids


def test_fresh1_newest_upload_survives_over_31_older_uploads(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    _seed_many_older_uploads(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, count=31,
    )
    newest_file_id = _upload_supported_via_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, subdir="newest", hall_number=999, hall_label="Newest Fresh Hall",
    )

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="fresh1")
    )
    assert len(uploaded_records) == 32

    truth_result = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=uploaded_records)
    available = [item for item in truth_result.items if item.get("status") == "available"]
    assert len(available) <= otc.MAX_AVAILABLE_EVIDENCE_ITEMS

    newest_items = [item for item in available if item.get("source_file_id") == str(newest_file_id)]
    assert newest_items, "the newest upload must survive bounding even though 31 older uploads exist"


def test_fresh2_newest_upload_t_ref_maps_to_newest_source_file_id(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    _seed_many_older_uploads(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, count=31,
    )
    newest_file_id = _upload_supported_via_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, subdir="newest", hall_number=999, hall_label="Newest Fresh Hall",
    )

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="fresh2")
    )
    truth_result = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=uploaded_records)
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]
    newest_refs = [
        ref for index, ref in enumerate(truth_refs, start=1)
        if truth_result.items[index - 1].get("source_file_id") == str(newest_file_id)
    ]
    assert newest_refs, "at least one T# must map to the newest upload's file_id"
    assert any(truth_refs[ref]["is_usable_evidence"] for ref in newest_refs)


def test_fresh3_newest_upload_survives_older_uploads_and_large_static_volume(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)

    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=25)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    _seed_many_older_uploads(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, count=31,
    )
    newest_file_id = _upload_supported_via_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, subdir="newest", hall_number=999, hall_label="Newest Fresh Hall",
    )

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="fresh3")
    )
    truth_result = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=uploaded_records)
    available = [item for item in truth_result.items if item.get("status") == "available"]
    assert len(available) <= otc.MAX_AVAILABLE_EVIDENCE_ITEMS
    newest_items = [item for item in available if item.get("source_file_id") == str(newest_file_id)]
    assert newest_items, "the fresh runtime upload must survive against older uploads AND large static volume combined"


def test_fresh4_two_recent_uploads_deterministic_newest_first_precedence(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    older_id = _upload_supported_via_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, subdir="older", hall_number=61, hall_label="Older Recent Hall",
    )
    newer_id = _upload_supported_via_gate(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, subdir="newer", hall_number=62, hall_label="Newer Recent Hall",
    )
    assert older_id != newer_id

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="fresh4")
    )
    # Deterministic: the repository query orders by created_at DESC, id DESC
    # and _load_uploaded_truth_records preserves that order untouched.
    assert str(uploaded_records[0].source_file_id) == str(newer_id)
    assert str(uploaded_records[1].source_file_id) == str(older_id)

    # Re-running produces byte-identical ordering (determinism, not a race).
    uploaded_records_again = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="fresh4b")
    )
    assert [r.source_file_id for r in uploaded_records_again] == [r.source_file_id for r in uploaded_records]


def test_fresh5_no_runtime_uploads_preserves_existing_static_only_behavior(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    static_dir = tmp_path / "static_pilot"
    _write_static_pilot_volume(static_dir, count=5)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", static_dir)

    company = _jannat_company(company_id)
    result_no_upload = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=None)
    result_empty_upload = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=[])
    assert result_no_upload.items == result_empty_upload.items
    assert result_no_upload.status in {"ok", "no_evidence"}


def test_fresh6_older_upload_remains_valid_evidence_if_capacity_remains(tmp_path, monkeypatch) -> None:
    """The newest-first fix must not discard ALL historical runtime
    evidence - only apply selection priority. With few uploads (well under
    the bound), every upload's evidence should still be present."""
    company_id = uuid4()
    fake_db = _FakeDB()
    department_id = _seed_tenant(fake_db, company_id=company_id, department_slug=DAIRTNA_POULTRY_DEPARTMENT_SLUG)
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))
    auth_context = AuthContext(company_id=str(company_id), user_id=str(uuid4()), permissions=[])

    file_ids = _seed_many_older_uploads(
        fake_db=fake_db, auth_context=auth_context, department_id=department_id,
        tmp_path=tmp_path, count=3, hall_start=70,
    )

    service = AIService()
    service.db_pool = fake_db
    company = _jannat_company(company_id)
    uploaded_records = asyncio.run(
        service._load_uploaded_truth_records(company=company, company_id=str(company_id), session_id="fresh6")
    )
    truth_result = otc.assemble_truth_context(company=company, aimx_department=None, uploaded_records=uploaded_records)
    available = [item for item in truth_result.items if item.get("status") == "available"]

    for file_id in file_ids:
        matching = [item for item in available if item.get("source_file_id") == str(file_id)]
        assert matching, f"older upload {file_id} must remain valid evidence when capacity is not exceeded"


# ---------------------------------------------------------------------------
# U10: real Truth assembly -> real Decision Context -> real M6 reference
# catalog produces a real T# derived from the newly uploaded file. No direct
# construction of operational_truth_context, no injected T# items.
# ---------------------------------------------------------------------------


def test_u10_real_truth_assembly_reaches_decision_context_reference_catalog(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))

    record = _translated_records(tmp_path)[0]
    truth_result = otc.assemble_truth_context(
        company=_jannat_company(company_id), aimx_department=None, uploaded_records=[record],
    )
    assert truth_result.status == "ok"

    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]

    upload_derived_refs = [
        ref for index, ref in enumerate(truth_refs, start=1)
        if truth_result.items[index - 1].get("source_file") == record.source_file
    ]
    assert upload_derived_refs, "expected at least one T# derived from the uploaded file"
    for ref in upload_derived_refs:
        assert truth_refs[ref]["epistemic_origin"] == "observed"
        assert truth_refs[ref]["is_usable_evidence"] is True


# ---------------------------------------------------------------------------
# U11: M6 provenance validation accepts a real uploaded T# as evidence_basis
# ---------------------------------------------------------------------------


def test_u11_m6_provenance_validation_accepts_real_uploaded_t_ref(tmp_path, monkeypatch) -> None:
    company_id = uuid4()
    _configure_jannat_company_id(monkeypatch, company_id)
    monkeypatch.setattr(otc, "POULTRY_OPERATIONS_DIR", Path("does_not_exist_m7_probe"))

    record = _translated_records(tmp_path)[0]
    truth_result = otc.assemble_truth_context(
        company=_jannat_company(company_id), aimx_department=None, uploaded_records=[record],
    )
    decision_context = build_decision_context(
        context={}, response_language="en", operational_truth_context=truth_result.items,
    )
    truth_refs = decision_context["reasoning_reference_catalog"]["truth"]
    usable_upload_refs = [
        ref for index, ref in enumerate(truth_refs, start=1)
        if truth_result.items[index - 1].get("source_file") == record.source_file
        and truth_refs[ref]["is_usable_evidence"]
    ]
    assert usable_upload_refs
    chosen_ref = usable_upload_refs[0]

    parsed = {
        "raw_decision": {
            "reasoning_assessment": {
                "reasoning_state": "aligned",
                "operational_assessment": "Hall 2 bird balance and water consumption observed from the uploaded report.",
                "company_brain_alignment": "n/a",
                "tensions": [],
                "evidence_gaps": [],
                "risk_assessment": "n/a",
                "confidence": 70,
                "recommendation_basis": {
                    "evidence_basis": [chosen_ref],
                    "company_basis": [],
                    "missing_evidence": [],
                },
            }
        }
    }
    ok, errors = validate_reasoning_assessment(parsed, decision_context)
    assert ok, errors


# ---------------------------------------------------------------------------
# M7-04 (Correction Round 1): the permanent Golden proof, through the REAL
# FastAPI routes end to end - real upload endpoint, real server-side
# department validation, real FileIngestionService, real KAE, real
# structured persistence, real AIService._load_uploaded_truth_records, real
# Truth assembly, real Decision Context, real operational-response
# enforcement, real legacy validator, real M6 validator, real formatted
# ChatResponse. Runs against the real local dev Postgres instance
# (DATABASE_URL) - a fake pool cannot exercise the real FK-constrained
# schema or the real route/auth layer, matching the established convention
# in tests/test_operational_event_intelligence.py. Only two things are
# faked, both legitimate test boundaries: (1) permission/role resolution
# (matching tests/test_tenant_isolation.py's _PermissionAuthService
# pattern) and (2) the external LLM call. No product validator
# (_validate_execution_structure, _operational_response_missing_elements,
# validate_reasoning_assessment) is monkeypatched or bypassed.
# ---------------------------------------------------------------------------


def _raw_decision(reasoning_assessment: dict) -> dict:
    return {
        "context_lock": {"missing_fields": [], "is_locked": False, "confidence": 0, "why": ""},
        "problem_classification": {"type": "", "confidence": 0, "why": ""},
        "truth_validation": {"contradictions": [], "trust_score": 0, "notes": ""},
        "root_cause_engine": {"root_causes": [], "why_chain": []},
        "solution_generator": {"urgent_30_days": [], "mid_term_90_days": [], "long_term_6_12_months": []},
        "execution_engine": {
            "priority_order": [], "quick_wins": [], "high_impact_moves": [], "dependencies": [], "risks": []
        },
        "reasoning_assessment": reasoning_assessment,
    }


class _FakeChatCompletions:
    def __init__(self, response_text: str) -> None:
        self.messages: list = []
        self._response_text = response_text

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        from types import SimpleNamespace

        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._response_text))])


class _FakeOpenAIClient:
    def __init__(self, response_text: str) -> None:
        from types import SimpleNamespace

        self.chat_completions = _FakeChatCompletions(response_text)
        self.chat = SimpleNamespace(completions=self.chat_completions)


class _GoldenPermissionAuthService:
    """Fakes only role/permission resolution - a legitimate test-identity
    boundary (JWT itself is real and really verified; company_id/user_id
    really flow from it), matching tests/test_tenant_isolation.py's
    _PermissionAuthService. Never fakes department lookup, KAE, persistence,
    Truth assembly, or any validator - those all run for real."""

    def __init__(self, permissions: list[str]) -> None:
        self._permissions = permissions

    async def get_current_context(self, company_id: str, user_id: str) -> dict:
        return {
            "company": {"id": company_id},
            "user": {"id": user_id},
            "membership": {
                "id": str(uuid4()), "company_id": company_id, "user_id": user_id,
                "role_id": str(uuid4()), "status": "active",
            },
            "role": {"id": str(uuid4()), "slug": "dairtna_operator", "permissions": self._permissions},
        }


def _reset_stale_db_bindings(app, ai_engine) -> None:
    """TestClient does not keep one persistent event loop alive across
    separate .post() calls in this environment. Two real asyncpg pools get
    lazily cached and reused across requests/tests once created: the app
    -level one (request.app.state.auth_db_pool, used by files.py/chat.py/
    permissions.py) and AIService's own instance-level one (ai_engine.
    db_pool / ai_engine.repo, memoized by AIService._ensure_db() - "if
    self.repo is not None: return"). Either one, once bound to a now
    -closed loop, breaks the NEXT real request/test that reuses the same
    `app`/`ai_engine` singletons on a different loop. Clearing both to None
    (never closing - their loop is already gone) forces a fresh pool bound
    to whichever loop is current, exactly as a cold process start would do.
    This is a TestClient-only concern; no product code path is changed."""
    if getattr(app.state, "auth_db_pool", None) is not None:
        app.state.auth_db_pool = None
    if ai_engine.repo is not None:
        ai_engine.db_pool = None
        ai_engine.repo = None


class _CitationAwareFakeChatCompletions:
    """M7-04 Correction Round 2 (M7-10): constructs its JSON response
    DYNAMICALLY, inside create(), by reading the REAL Decision Context the
    actual chat() call just built - via the existing DECISION_CONTEXT_DEBUG
    snapshot mechanism (app.services.decision_debug), which
    AIService.chat() populates immediately before this exact call (see
    start_decision_debug_snapshot in app/services/openai_client.py). This
    removes the pre-chat dry-run determinism assumption entirely: there is
    no "assume assemble_truth_context is a pure function and re-run it
    separately" step left anywhere - the T# cited is read directly out of
    the one real chat request's own generated catalog.

    This class only OBSERVES (list_decision_debug_snapshots is read-only,
    returns deep copies) - it never constructs, injects, or mutates
    operational_truth_context, the reference catalog, or any validator.
    """

    def __init__(self, *, company_id: str, session_id: str, target_file_id: str) -> None:
        self.messages: list = []
        self.company_id = company_id
        self.session_id = session_id
        self.target_file_id = target_file_id
        self.captured_decision_context: dict | None = None
        self.chosen_ref: str | None = None
        self.call_count = 0
        self.reasoning_call_count = 0

    async def create(self, **kwargs):
        from types import SimpleNamespace

        self.call_count += 1
        self.messages.append(kwargs["messages"])

        # AIService._extract_and_upsert_facts (an existing, separate
        # subsystem - see app/services/openai_client.py) legitimately
        # issues its own LLM call after the main reasoning response is
        # accepted, using a fixed FACT_EXTRACTOR_SYSTEM prompt distinct
        # from the reasoning system prompt this class otherwise expects.
        # Only the real reasoning call resolves/cites a T#; the fact
        # extractor gets a harmless empty-facts response so it no-ops
        # (app/services/openai_client.py:729 already treats an empty/
        # missing "facts" list as "nothing extracted").
        from app.services.openai_client import FACT_EXTRACTOR_SYSTEM

        is_fact_extraction_call = any(
            message.get("role") == "system" and message.get("content") == FACT_EXTRACTOR_SYSTEM
            for message in kwargs["messages"]
        )
        if is_fact_extraction_call:
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"facts": []})))]
            )

        self.reasoning_call_count += 1

        from app.services.decision_debug import list_decision_debug_snapshots

        snapshots = list_decision_debug_snapshots(company_id=self.company_id, session_id=self.session_id)
        assert snapshots, (
            "no DECISION_CONTEXT_DEBUG snapshot found - DECISION_CONTEXT_DEBUG "
            "must be enabled for this test"
        )
        # Most recent first (list_decision_debug_snapshots reverses the
        # deque) - this call's own snapshot.
        decision_context = snapshots[0]["decision_context"]
        self.captured_decision_context = decision_context
        truth_items = decision_context.get("operational_truth_context") or []
        truth_refs = decision_context["reasoning_reference_catalog"]["truth"]

        usable_refs = [
            ref for index, ref in enumerate(truth_refs, start=1)
            if truth_items[index - 1].get("source_file_id") == self.target_file_id
            and truth_refs[ref]["is_usable_evidence"]
        ]
        assert usable_refs, (
            "the ACTUAL chat-generated reference catalog must contain a usable "
            f"T# mapped to source_file_id={self.target_file_id!r}"
        )
        self.chosen_ref = usable_refs[0]

        reasoning_assessment = {
            "reasoning_state": "aligned",
            "operational_assessment": "Golden journey hall readings observed from the uploaded report.",
            "company_brain_alignment": "n/a",
            "tensions": [],
            "evidence_gaps": [],
            "risk_assessment": "n/a",
            "confidence": 65,
            "recommendation_basis": {
                "evidence_basis": [self.chosen_ref], "company_basis": [], "missing_evidence": [],
            },
        }
        ai_json = json.dumps({
            "executive_summary": (
                "Executive Summary\n- Golden journey hall status reviewed from the uploaded "
                "daily report.\n\nRecommended Actions\n- Monitor hall performance.\n\n"
                "Priority Level\n- Medium."
            ),
            "raw_decision": _raw_decision(reasoning_assessment),
        })
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=ai_json))])


class _CitationAwareFakeOpenAIClient:
    def __init__(self, *, company_id: str, session_id: str, target_file_id: str) -> None:
        from types import SimpleNamespace

        self.chat_completions = _CitationAwareFakeChatCompletions(
            company_id=company_id, session_id=session_id, target_file_id=target_file_id,
        )
        self.chat = SimpleNamespace(completions=self.chat_completions)


def _run_with_fresh_pool(coro_fn):
    """Run one async unit of work against a freshly created, freshly closed
    asyncpg pool. asyncpg pools are bound to the event loop that created
    them, and asyncio.run() creates a brand-new loop on every call - a pool
    cannot be created in one asyncio.run() call and reused in another, so
    each logical database step in this Golden test gets its own short-lived
    pool rather than sharing one across calls."""

    async def runner():
        import asyncpg

        from app.core.config import settings as core_settings

        pool = await asyncpg.create_pool(dsn=core_settings.DATABASE_URL, min_size=1, max_size=5)
        try:
            return await coro_fn(pool)
        finally:
            await pool.close()

    return asyncio.run(runner())


async def _seed_golden_company_department_user(pool) -> tuple[str, str, str]:
    company_row = await pool.fetchrow(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m7-golden-{uuid4().hex[:10]}", "M7 Golden Test Company",
    )
    user_row = await pool.fetchrow(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m7-golden-{uuid4().hex[:10]}@example.com", "M7 Golden Test User",
    )
    department_row = await pool.fetchrow(
        "INSERT INTO departments (company_id, name, slug, department_type) VALUES ($1, $2, $3, $4) RETURNING id",
        company_row["id"], "Dairtna Poultry", DAIRTNA_POULTRY_DEPARTMENT_SLUG, "custom",
    )
    return str(company_row["id"]), str(user_row["id"]), str(department_row["id"])


async def _cleanup_golden(pool, *, company_id: str, user_id: str, file_id: str | None) -> None:
    """Cleans up EVERY row this company's test run could have created -
    not just the one `file_id` param (kept for logging/clarity only) -
    since stress tests (see test_m7_04_stress_golden_upload_survives_many_
    older_real_uploads) seed many files per company, each with its own
    file_chunks/file_chunk_embeddings/operational_event_drafts rows that
    must be deleted before the parent files row can be deleted."""
    _UUID = UUID

    await pool.execute(
        "DELETE FROM file_chunk_embeddings WHERE file_id IN (SELECT id FROM files WHERE company_id = $1)",
        _UUID(company_id),
    )
    await pool.execute(
        "DELETE FROM file_chunks WHERE file_id IN (SELECT id FROM files WHERE company_id = $1)",
        _UUID(company_id),
    )
    await pool.execute(
        "DELETE FROM operational_event_drafts WHERE file_id IN (SELECT id FROM files WHERE company_id = $1)",
        _UUID(company_id),
    )
    await pool.execute("DELETE FROM structured_record_drafts WHERE company_id = $1", _UUID(company_id))
    await pool.execute("DELETE FROM raw_inputs WHERE company_id = $1", _UUID(company_id))
    await pool.execute("DELETE FROM memory_events WHERE company_id = $1", company_id)
    await pool.execute("DELETE FROM memory_facts WHERE company_id = $1", company_id)
    await pool.execute("DELETE FROM files WHERE company_id = $1", _UUID(company_id))
    await pool.execute("DELETE FROM departments WHERE company_id = $1", _UUID(company_id))
    await pool.execute("DELETE FROM companies WHERE id = $1", _UUID(company_id))
    await pool.execute("DELETE FROM users WHERE id = $1", _UUID(user_id))


def test_m7_04_full_golden_journey_through_real_endpoints(tmp_path, monkeypatch) -> None:
    from unittest.mock import AsyncMock, patch

    from fastapi.testclient import TestClient

    from app.core.config import settings as core_settings
    from app.core.security import create_token
    from app.main import app
    from app.services.openai_client import ai_engine

    if not core_settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")

    import app.services.decision_debug as decision_debug_module

    company_id, user_id, department_id = _run_with_fresh_pool(_seed_golden_company_department_user)
    file_id: str | None = None
    original_client = ai_engine.client
    try:
        _configure_jannat_company_id(monkeypatch, UUID(company_id))
        # Enable the existing, pre-built DECISION_CONTEXT_DEBUG snapshot
        # mechanism (app/services/decision_debug.py) for this test only -
        # a read-only, already-shipped test/ops instrumentation hook, not
        # something invented for this test. It captures the real
        # Decision Context AIService.chat() builds each turn into an
        # in-memory deque; it is never part of the public ChatResponse
        # (verified below).
        monkeypatch.setattr(
            decision_debug_module, "settings",
            dataclasses.replace(decision_debug_module.settings, DECISION_CONTEXT_DEBUG=True),
        )

        token = create_token(company_id=company_id, user_id=user_id)
        headers = {"Authorization": f"Bearer {token}"}
        permissions = ["files.upload", "files.read", "agents.custom.use", "ai.chat"]

        xlsx_path = tmp_path / SUPPORTED_FILENAME
        _write_supported_workbook(xlsx_path, hall_number=42, hall_label="Golden Journey Hall")

        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(return_value=_GoldenPermissionAuthService(permissions)),
        ):
            # --- 1: real upload through the real route -----------------
            with open(xlsx_path, "rb") as fh:
                upload_response = client.post(
                    "/files/upload",
                    headers=headers,
                    files={
                        "file": (
                            SUPPORTED_FILENAME, fh,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                    # department_id is an unmarked (non-Form) query param
                    # alongside File(...) in the real route signature - it
                    # must be sent as a query parameter, not multipart form
                    # data, exactly as a real browser upload would.
                    params={"department_id": department_id},
                )
            assert upload_response.status_code == 201, upload_response.text
            uploaded_file = upload_response.json()
            file_id = uploaded_file["id"]
            assert uploaded_file["status"] in {"ready", "processing"}

            # --- 2/3: structural verification directly against the real DB
            async def verify_persistence(pool):
                file_row = await pool.fetchrow("SELECT * FROM files WHERE id = $1", UUID(file_id))
                draft_row = await pool.fetchrow(
                    "SELECT * FROM structured_record_drafts WHERE company_id = $1 "
                    "AND extracted_payload ->> 'file_id' = $2 AND record_type = $3",
                    UUID(company_id), file_id, otc.POULTRY_DAILY_REPORT_RECORD_TYPE,
                )
                return file_row, draft_row

            file_row, draft_row = _run_with_fresh_pool(verify_persistence)
            assert file_row is not None
            assert str(file_row["company_id"]) == company_id
            assert str(file_row["department_id"]) == department_id
            assert draft_row is not None, "the real KAE/persistence path must have produced a poultry draft"
            assert str(draft_row["department_id"]) == department_id

            # --- 4-8: no pre-chat dry run. The citation-aware fake LLM
            # below reads the ACTUAL Decision Context the real /ai/chat
            # call is about to build (via the DECISION_CONTEXT_DEBUG
            # snapshot AIService.chat() itself populates) and constructs
            # its response from that real, just-generated catalog - there
            # is no "assume assemble_truth_context is pure and re-run it
            # separately" step left anywhere in this test.
            fake_client = _CitationAwareFakeOpenAIClient(
                company_id=company_id, session_id="m7-04-golden", target_file_id=file_id,
            )
            ai_engine.client = fake_client
            _reset_stale_db_bindings(app, ai_engine)

            chat_payload = {
                "company_id": company_id,
                "session_id": "m7-04-golden",
                "message": "Give me an update on Golden Journey Hall.",
                "department_id": department_id,
            }
            chat_response = client.post("/ai/chat", headers=headers, json=chat_payload)

        assert chat_response.status_code == 200, chat_response.text
        body = chat_response.json()
        # 14: normally formatted top-level ChatResponse contract.
        assert set(body.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}

        # Exact model-call count: exactly one REASONING call (no repair/
        # regeneration needed since the citation-aware fake always returns
        # an already-valid response under every contract), plus exactly one
        # separate call from the existing, independent fact-extraction
        # subsystem (AIService._extract_and_upsert_facts - a real,
        # legitimately separate external call this real ai_engine
        # singleton already makes after every accepted response when a
        # real memory repo is configured, unrelated to reasoning/citation).
        assert fake_client.chat_completions.reasoning_call_count == 1
        assert fake_client.chat_completions.call_count == 2

        chosen_ref = fake_client.chat_completions.chosen_ref
        assert chosen_ref is not None, "the citation-aware fake must have resolved a real T# during the real chat call"

        # 9/10/11/12: the real M6 validator, the real legacy validator, and
        # the real operational-response check all accepted this response on
        # its own terms.
        assert body["logic_json"]["reasoning_assessment"]["reasoning_state"] == "aligned"
        assert body["logic_json"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] == [chosen_ref]

        # M7-10: independently resolve the returned citation AGAIN against
        # the actual captured chat-generated catalog (not the same lookup
        # reused - a fresh re-derivation from the captured snapshot) and
        # prove it maps to this exact uploaded file's stable id. This is
        # the key proof the correction round requires.
        captured = fake_client.chat_completions.captured_decision_context
        assert captured is not None
        captured_truth_items = captured["operational_truth_context"]
        captured_truth_refs = captured["reasoning_reference_catalog"]["truth"]
        assert chosen_ref in captured_truth_refs
        chosen_index = int(chosen_ref[1:])  # "T7" -> 7, 1-based per _build_reasoning_reference_catalog
        resolved_item = captured_truth_items[chosen_index - 1]
        assert resolved_item.get("source_file_id") == file_id, (
            f"resolved T# {chosen_ref} must map back to the real uploaded file_id {file_id}, "
            f"got source_file_id={resolved_item.get('source_file_id')!r}"
        )
        assert captured_truth_refs[chosen_ref]["is_usable_evidence"] is True
        assert captured_truth_refs[chosen_ref]["epistemic_origin"] in {"observed", "derived"}

        # 15: DECISION_CONTEXT_DEBUG instrumentation must not weaken the
        # normal public response contract - the internal catalog/signals
        # stay excluded from the real ChatResponse even with debug mode on.
        assert "reasoning_reference_catalog" not in body["meta"]["context"]
        assert "reasoning_signals" not in body["meta"]["context"]

        # 13: this is a brand-new, isolated test company with zero seed
        # events - nothing reference_seed-sourced could have reached the
        # prompt at all.
        prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
        assert "reference_seed" not in prompt_text.lower()

        # 15: Caesar/non-Jannat isolation - a different department at the
        # SAME company has zero structured poultry drafts.
        async def verify_isolation(pool):
            other_department_row = await pool.fetchrow(
                "INSERT INTO departments (company_id, name, slug, department_type) "
                "VALUES ($1, $2, $3, $4) RETURNING id",
                UUID(company_id), "Caesar Beverage", "caesar-beverage", "custom",
            )
            other_department_id = other_department_row["id"]
            rows = await pool.fetch(
                "SELECT id FROM structured_record_drafts WHERE company_id = $1 AND department_id = $2",
                UUID(company_id), other_department_id,
            )
            return rows

        isolation_rows = _run_with_fresh_pool(verify_isolation)
        assert isolation_rows == []
    finally:
        ai_engine.client = original_client
        _run_with_fresh_pool(
            lambda pool: _cleanup_golden(pool, company_id=company_id, user_id=user_id, file_id=file_id)
        )
        # See _reset_stale_db_bindings: whatever pool(s) got lazily
        # (re)created for the /ai/chat request are bound to that request's
        # now-closed loop - leaving them cached would break the NEXT test
        # that reuses the same `app`/`ai_engine` singletons on a different
        # loop.
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# M7-04 Correction Round 2, Section 13: the Golden proof must survive the
# same fresh-vs-older-upload precedence issue M7-02/FRESH1-FRESH6 fixed.
# Older uploads are seeded through the lowest honest persistence layer
# (real FileIngestionService + real KAE/persistence gate, against the real
# DB, skipping only the HTTP/TestClient layer for the SEED data - Codex's
# own explicit allowance) - the CURRENT/Golden upload itself always goes
# through the real HTTP endpoint.
# ---------------------------------------------------------------------------


async def _seed_older_upload_via_service(
    pool, *, company_id: str, department_id: str, user_id: str,
    tmp_path: Path, subdir: str, hall_number: int, hall_label: str,
) -> str:
    path = tmp_path / subdir / SUPPORTED_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_supported_workbook(path, hall_number=hall_number, hall_label=hall_label)

    file_service = FileIngestionService(pool)
    auth_context = AuthContext(company_id=company_id, user_id=user_id, permissions=[])
    ingest_result = await file_service.ingest_file(
        company_id=UUID(company_id),
        uploaded_by_user_id=UUID(user_id),
        source_path=path,
        filename=path.name,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        department_id=UUID(department_id),
    )
    file_record = ingest_result["file"]
    summary = await files_api._run_nco_lite_after_upload_if_applicable(
        file_service=file_service,
        auth_context=auth_context,
        department_id=UUID(department_id),
        file_record=file_record,
        source_path=path,
        filename=path.name,
    )
    assert summary is not None and summary["structured_ingestion_status"] == "succeeded"
    return str(file_record["id"])


def test_m7_04_stress_golden_upload_survives_many_older_real_uploads(tmp_path, monkeypatch) -> None:
    """M7-02 + M7-04 composing correctly: stress the bound with real older
    upload-derived evidence BEFORE the Golden upload, then prove the
    Golden upload (through the real endpoint) still produces a real,
    citable, correctly-attributed T# in the ACTUAL chat-generated catalog."""
    from unittest.mock import AsyncMock, patch

    from fastapi.testclient import TestClient

    from app.core.config import settings as core_settings
    from app.core.security import create_token
    from app.main import app
    from app.services.openai_client import ai_engine

    if not core_settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")

    import app.services.decision_debug as decision_debug_module

    company_id, user_id, department_id = _run_with_fresh_pool(_seed_golden_company_department_user)
    file_id: str | None = None
    original_client = ai_engine.client
    try:
        _configure_jannat_company_id(monkeypatch, UUID(company_id))
        monkeypatch.setattr(
            decision_debug_module, "settings",
            dataclasses.replace(decision_debug_module.settings, DECISION_CONTEXT_DEBUG=True),
        )

        # Seed 31 older uploads (distinct halls) through the real service
        # layer against the real DB, one shared pool for the whole batch.
        async def seed_older(pool):
            for index in range(31):
                await _seed_older_upload_via_service(
                    pool, company_id=company_id, department_id=department_id, user_id=user_id,
                    tmp_path=tmp_path, subdir=f"older_{index}",
                    hall_number=200 + index, hall_label=f"Stress Older Hall {index}",
                )

        _run_with_fresh_pool(seed_older)

        token = create_token(company_id=company_id, user_id=user_id)
        headers = {"Authorization": f"Bearer {token}"}
        permissions = ["files.upload", "files.read", "agents.custom.use", "ai.chat"]

        xlsx_path = tmp_path / "golden" / SUPPORTED_FILENAME
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)
        _write_supported_workbook(xlsx_path, hall_number=999, hall_label="Golden Stress Hall")

        client = TestClient(app)
        _reset_stale_db_bindings(app, ai_engine)
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(return_value=_GoldenPermissionAuthService(permissions)),
        ):
            # --- the CURRENT/Golden upload: real HTTP endpoint, always ---
            with open(xlsx_path, "rb") as fh:
                upload_response = client.post(
                    "/files/upload",
                    headers=headers,
                    files={
                        "file": (
                            SUPPORTED_FILENAME, fh,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    },
                    params={"department_id": department_id},
                )
            assert upload_response.status_code == 201, upload_response.text
            file_id = upload_response.json()["id"]

            fake_client = _CitationAwareFakeOpenAIClient(
                company_id=company_id, session_id="m7-04-stress", target_file_id=file_id,
            )
            ai_engine.client = fake_client
            _reset_stale_db_bindings(app, ai_engine)

            chat_payload = {
                "company_id": company_id,
                "session_id": "m7-04-stress",
                "message": "Give me an update on the Golden Stress Hall.",
                "department_id": department_id,
            }
            chat_response = client.post("/ai/chat", headers=headers, json=chat_payload)

        assert chat_response.status_code == 200, chat_response.text
        body = chat_response.json()
        chosen_ref = fake_client.chat_completions.chosen_ref
        assert chosen_ref is not None, (
            "the Golden upload must still receive a usable T# in the actual chat-generated "
            "catalog even with 31 older uploads already present"
        )
        assert body["logic_json"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] == [chosen_ref]

        captured = fake_client.chat_completions.captured_decision_context
        captured_truth_items = captured["operational_truth_context"]
        captured_truth_refs = captured["reasoning_reference_catalog"]["truth"]
        resolved_item = captured_truth_items[int(chosen_ref[1:]) - 1]
        assert resolved_item.get("source_file_id") == file_id
        assert captured_truth_refs[chosen_ref]["is_usable_evidence"] is True
    finally:
        ai_engine.client = original_client
        _run_with_fresh_pool(
            lambda pool: _cleanup_golden(pool, company_id=company_id, user_id=user_id, file_id=file_id)
        )
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# Section 19: reference-seed operational_events cannot contaminate Truth
# ---------------------------------------------------------------------------


def test_seed_operational_events_isolation_truth_assembly_has_no_db_access() -> None:
    """Operational Truth Context assembly is architecturally isolated from
    operational_events (where reference-seed rows live): neither
    assemble_truth_context nor _collect_operational_contexts accepts any
    database handle at all, so it is structurally impossible for a seeded
    operational_events row to be read into a T#."""
    assert "db" not in inspect.signature(otc.assemble_truth_context).parameters
    assert "pool" not in inspect.signature(otc.assemble_truth_context).parameters
    assert "connection" not in inspect.signature(otc.assemble_truth_context).parameters
    assert set(inspect.signature(otc.assemble_truth_context).parameters) == {
        "company", "aimx_department", "uploaded_records",
    }
