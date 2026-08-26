"""M8 Slice 3A: live reasoning-receipt wiring tests.

Real Postgres throughout. The primary success/repair/failure scenarios go
through the real /ai/chat HTTP route (TestClient(app)) with a real upload
and a real, JWT-authenticated user - reusing the exact
DECISION_CONTEXT_DEBUG citation-aware fake-client pattern already proven by
tests/test_m7_slice1_upload_truth_bridge.py's Golden Journey test. Truth/
Company Brain extraction edge cases (unresolved/missing-source_file_id/
malformed citations) are proven both as pure unit tests of
app/ome/provenance.py's helpers (hand-built catalogs, no DB) and as real
DB-backed tests of AIService._create_live_reasoning_receipt directly
(proving the zero-receipt-on-failure guarantee) - this avoids fighting the
M6 reasoning-assessment validator, which already guarantees every T#/CB# a
real model response can cite resolves in the catalog; the gap cases this
slice's Founder Correction 1 defends against are real DURABILITY gaps
(no source_file_id), not "M6 let an unresolvable ref through".
"""
from __future__ import annotations

import asyncio
import dataclasses
import json
from types import SimpleNamespace
from uuid import UUID, uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_token
from app.main import app
from app.ome.errors import InvalidMemoryInput
from app.ome.provenance import build_truth_evidence_refs
from app.ome.types import EvidenceRef
from app.services.company_brain_context import DAIRTNA_POULTRY_DEPARTMENT_SLUG
from app.services.openai_client import FACT_EXTRACTOR_SYSTEM, AIService, ai_engine
import app.services.decision_debug as decision_debug_module
from app.services.decision_debug import list_decision_debug_snapshots

from tests.test_m7_slice1_upload_truth_bridge import (
    SUPPORTED_FILENAME,
    _GoldenPermissionAuthService,
    _configure_jannat_company_id,
    _reset_stale_db_bindings,
    _write_supported_workbook,
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=5)


async def _seed_company_department_user(pool, *, label: str) -> tuple[str, str, str]:
    company_row = await pool.fetchrow(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m8-s3a-{label}-{uuid4().hex[:8]}", f"M8 Slice 3A Test Company {label}",
    )
    user_row = await pool.fetchrow(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s3a-{label}-{uuid4().hex[:8]}@example.com", f"M8 Slice 3A Test User {label}",
    )
    department_row = await pool.fetchrow(
        "INSERT INTO departments (company_id, name, slug, department_type) VALUES ($1, $2, $3, $4) RETURNING id",
        company_row["id"], "Dairtna Poultry", DAIRTNA_POULTRY_DEPARTMENT_SLUG, "custom",
    )
    return str(company_row["id"]), str(user_row["id"]), str(department_row["id"])


async def _cleanup(pool, *, company_id: str, user_id: str) -> None:
    _uuid = UUID
    await pool.execute("DELETE FROM ome_reasoning_receipts WHERE company_id = $1", _uuid(company_id))
    await pool.execute(
        "DELETE FROM file_chunk_embeddings WHERE file_id IN (SELECT id FROM files WHERE company_id = $1)",
        _uuid(company_id),
    )
    await pool.execute(
        "DELETE FROM file_chunks WHERE file_id IN (SELECT id FROM files WHERE company_id = $1)", _uuid(company_id)
    )
    await pool.execute(
        "DELETE FROM operational_event_drafts WHERE file_id IN (SELECT id FROM files WHERE company_id = $1)",
        _uuid(company_id),
    )
    await pool.execute("DELETE FROM structured_record_drafts WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM raw_inputs WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM memory_events WHERE company_id = $1", company_id)
    await pool.execute("DELETE FROM memory_facts WHERE company_id = $1", company_id)
    await pool.execute("DELETE FROM files WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM departments WHERE company_id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM companies WHERE id = $1", _uuid(company_id))
    await pool.execute("DELETE FROM users WHERE id = $1", _uuid(user_id))


async def _receipt_count(pool, *, company_id: str) -> int:
    return await pool.fetchval(
        "SELECT count(*) FROM ome_reasoning_receipts WHERE company_id = $1", UUID(company_id)
    )


def _raw_decision(reasoning_assessment: dict) -> dict:
    """Same structurally-required shape test_m7_slice1_upload_truth_bridge.py
    uses - duplicated deliberately, not imported, matching that file's own
    stated convention for fixture helpers."""
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


def _valid_ai_response(reasoning_assessment: dict) -> SimpleNamespace:
    ai_json = json.dumps({
        "executive_summary": (
            "Executive Summary\n- Slice 3A live receipt wiring test.\n\n"
            "Recommended Actions\n- Monitor hall performance.\n\nPriority Level\n- Medium."
        ),
        "raw_decision": _raw_decision(reasoning_assessment),
    })
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=ai_json))])


def _invalid_ai_response() -> SimpleNamespace:
    """Structurally invalid raw_decision.reasoning_assessment (missing the
    required recommendation_basis field) - fails M6 Pydantic validation
    while still satisfying legacy/operational structure, so it exercises
    exactly the M6 repair/failure path without accidentally triggering
    operational regeneration too."""
    reasoning_assessment = {
        "reasoning_state": "aligned",
        "operational_assessment": "x",
        "company_brain_alignment": "cannot determine",
        "tensions": [],
        "evidence_gaps": [],
        "risk_assessment": "x",
        "confidence": 50,
    }
    return _valid_ai_response(reasoning_assessment)


class _ConfigurableFakeChatCompletions:
    """Reads the REAL Decision Context the actual chat() call just built
    (DECISION_CONTEXT_DEBUG snapshot mechanism - identical technique to
    test_m7_slice1_upload_truth_bridge.py's _CitationAwareFakeChatCompletions)
    and constructs its response dynamically from that real, just-generated
    catalog - never a pre-chat dry run, never client-controlled provenance.
    """

    def __init__(self, *, company_id: str, session_id: str, target_file_id: str, mode: str) -> None:
        self.messages: list = []
        self.company_id = company_id
        self.session_id = session_id
        self.target_file_id = target_file_id
        self.mode = mode
        self.call_count = 0
        self.reasoning_call_count = 0
        self.chosen_truth_ref: str | None = None
        self.chosen_cb_ref: str | None = None

    async def create(self, **kwargs):
        self.call_count += 1
        self.messages.append(kwargs["messages"])

        is_fact_extraction_call = any(
            message.get("role") == "system" and message.get("content") == FACT_EXTRACTOR_SYSTEM
            for message in kwargs["messages"]
        )
        if is_fact_extraction_call:
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"facts": []})))]
            )

        self.reasoning_call_count += 1

        if self.mode == "always_invalid":
            return _invalid_ai_response()
        if self.mode == "invalid_then_valid" and self.reasoning_call_count == 1:
            return _invalid_ai_response()

        snapshots = list_decision_debug_snapshots(company_id=self.company_id, session_id=self.session_id)
        assert snapshots, "DECISION_CONTEXT_DEBUG must be enabled for this test"
        decision_context = snapshots[0]["decision_context"]
        truth_items = decision_context.get("operational_truth_context") or []
        truth_refs = decision_context["reasoning_reference_catalog"]["truth"]
        usable_refs = [
            ref for index, ref in enumerate(truth_refs, start=1)
            if truth_items[index - 1].get("source_file_id") == self.target_file_id
            and truth_refs[ref]["is_usable_evidence"]
        ]
        assert usable_refs, "must contain a usable T# mapped to target_file_id"
        self.chosen_truth_ref = usable_refs[0]

        company_brain_refs = decision_context["reasoning_reference_catalog"]["company_brain"]
        settled_cb_refs = [ref for ref, meta in company_brain_refs.items() if meta["is_settled"]]
        company_basis: list[str] = []
        if settled_cb_refs:
            self.chosen_cb_ref = settled_cb_refs[0]
            company_basis = [self.chosen_cb_ref]

        reasoning_assessment = {
            "reasoning_state": "aligned",
            "operational_assessment": "Slice 3A live receipt test observation.",
            "company_brain_alignment": "supported by current evidence" if company_basis else "cannot determine",
            "tensions": [],
            "evidence_gaps": [],
            "risk_assessment": "n/a",
            "confidence": 65,
            "recommendation_basis": {
                "evidence_basis": [self.chosen_truth_ref],
                "company_basis": company_basis,
                "missing_evidence": [],
                # M8 Slice 4B: organizational_memory_basis is now a
                # required RecommendationBasis field - no Slice 4B
                # scenario is under test in this Slice 3A-focused file.
                "organizational_memory_basis": [],
            },
        }
        return _valid_ai_response(reasoning_assessment)


class _ConfigurableFakeOpenAIClient:
    def __init__(self, *, company_id: str, session_id: str, target_file_id: str, mode: str = "cite_truth_and_cb") -> None:
        self.chat_completions = _ConfigurableFakeChatCompletions(
            company_id=company_id, session_id=session_id, target_file_id=target_file_id, mode=mode,
        )
        self.chat = SimpleNamespace(completions=self.chat_completions)


def _upload_and_chat(*, tmp_path, monkeypatch, mode: str, session_id: str):
    """Shared harness: seed a Jannat/Dairtna company+department+user, upload
    one real file through the real route, then POST /ai/chat with a
    _ConfigurableFakeOpenAIClient in the given mode. Returns
    (company_id, user_id, file_id, chat_response, fake_client)."""
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")

    async def seed(pool):
        return await _seed_company_department_user(pool, label="live")

    async def seed_runner():
        pool = await _make_pool()
        try:
            return await seed(pool)
        finally:
            await pool.close()

    company_id, user_id, department_id = asyncio.run(seed_runner())

    _configure_jannat_company_id(monkeypatch, UUID(company_id))
    monkeypatch.setattr(
        decision_debug_module, "settings",
        dataclasses.replace(decision_debug_module.settings, DECISION_CONTEXT_DEBUG=True),
    )

    token = create_token(company_id=company_id, user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}
    permissions = ["files.upload", "files.read", "agents.custom.use", "ai.chat"]

    xlsx_path = tmp_path / SUPPORTED_FILENAME
    _write_supported_workbook(xlsx_path, hall_number=7, hall_label="Slice 3A Hall")

    original_client = ai_engine.client
    client = TestClient(app)
    _reset_stale_db_bindings(app, ai_engine)
    from unittest.mock import AsyncMock, patch

    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_GoldenPermissionAuthService(permissions)),
    ):
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

        fake_client = _ConfigurableFakeOpenAIClient(
            company_id=company_id, session_id=session_id, target_file_id=file_id, mode=mode,
        )
        ai_engine.client = fake_client
        _reset_stale_db_bindings(app, ai_engine)

        chat_response = client.post(
            "/ai/chat",
            headers=headers,
            json={
                "company_id": company_id,
                "session_id": session_id,
                "message": "Give me an update on Slice 3A Hall.",
                "department_id": department_id,
            },
        )

    ai_engine.client = original_client
    _reset_stale_db_bindings(app, ai_engine)
    return company_id, user_id, file_id, chat_response, fake_client


# ---------------------------------------------------------------------------
# LIVE SUCCESS (items 1-8) + TRUTH/CB live persistence (9-10, 17-18) +
# PUBLIC BOUNDARY (28-31) + TENANT (34)
# ---------------------------------------------------------------------------

def test_live_success_creates_exactly_one_receipt_with_full_provenance(tmp_path, monkeypatch) -> None:
    company_id, user_id, file_id, chat_response, fake_client = _upload_and_chat(
        tmp_path=tmp_path, monkeypatch=monkeypatch, mode="cite_truth_and_cb", session_id="m8-s3a-live-1",
    )
    try:
        assert chat_response.status_code == 200, chat_response.text
        body = chat_response.json()

        # 1/28: public response shape unchanged; receipt id present only
        # inside meta (never a new top-level field).
        assert set(body.keys()) == {"ceo_text", "logic_json", "followup_question", "meta"}
        receipt_id = body["meta"]["reasoning_receipt_id"]
        assert receipt_id, "reasoning_receipt_id must be non-null for a successful live response (item 2)"

        async def verify(pool):
            row = await pool.fetchrow(
                "SELECT * FROM ome_reasoning_receipts WHERE company_id = $1", UUID(company_id)
            )
            count = await _receipt_count(pool, company_id=company_id)
            return row, count

        async def runner():
            pool = await _make_pool()
            try:
                return await verify(pool)
            finally:
                await pool.close()

        row, count = asyncio.run(runner())
        assert count == 1, "exactly one receipt per successful request (item 15/1)"
        assert str(row["id"]) == receipt_id, "returned id equals persisted receipt.id (item 3)"
        assert str(row["company_id"]) == company_id, "receipt.company_id equals JWT/auth company (item 4/34)"
        assert str(row["created_by_user_id"]) == user_id, "receipt.created_by_user_id equals authenticated user (item 5)"
        assert row["session_id"] == "m8-s3a-live-1", "receipt.session_id equals request session_id (item 6)"

        import json as _json
        snapshot = _json.loads(row["response_snapshot"]) if isinstance(row["response_snapshot"], str) else row["response_snapshot"]
        assert snapshot["ceo_text"] == body["ceo_text"], "response_snapshot.ceo_text equals exact returned ceo_text (item 7)"
        assert snapshot["reasoning_assessment"] == body["logic_json"]["reasoning_assessment"], (
            "response_snapshot.reasoning_assessment equals exact final returned reasoning_assessment (item 8)"
        )

        evidence_refs = _json.loads(row["evidence_refs"]) if isinstance(row["evidence_refs"], str) else row["evidence_refs"]
        truth_entries = [e for e in evidence_refs if e["category"] == "truth"]
        cb_entries = [e for e in evidence_refs if e["category"] == "company_brain"]
        assert truth_entries, "cited T# resolves to a persisted truth EvidenceRef (item 9)"
        assert truth_entries[0]["type"] == "file"
        assert truth_entries[0]["id"] == file_id, "truth ref resolves to exact uploaded file UUID (item 9/10)"
        if fake_client.chat_completions.chosen_cb_ref is not None:
            assert cb_entries, "cited CB# persists exact Company Brain provenance (item 17)"
            assert cb_entries[0]["display_label"] == fake_client.chat_completions.chosen_cb_ref
            import hashlib
            assert cb_entries[0]["content_sha256"] == hashlib.sha256(
                cb_entries[0]["text_snapshot"].encode("utf-8")
            ).hexdigest(), "checksum matches exact cited statement (item 18)"

        # 29/30/31: no internal provenance leak in the public response.
        assert "reasoning_reference_catalog" not in body["meta"]["context"]
        assert "internal_source_item" not in json.dumps(body)
        assert "text_snapshot" not in json.dumps(body["meta"].get("context", {}))
    finally:

        async def cleanup_runner():
            pool = await _make_pool()
            try:
                await _cleanup(pool, company_id=company_id, user_id=user_id)
            finally:
                await pool.close()

        asyncio.run(cleanup_runner())
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# FINAL/REPAIR (items 21-23)
# ---------------------------------------------------------------------------

def test_repair_path_creates_exactly_one_receipt_for_final_repaired_result(tmp_path, monkeypatch) -> None:
    company_id, user_id, file_id, chat_response, fake_client = _upload_and_chat(
        tmp_path=tmp_path, monkeypatch=monkeypatch, mode="invalid_then_valid", session_id="m8-s3a-repair-1",
    )
    try:
        assert chat_response.status_code == 200, chat_response.text
        assert fake_client.chat_completions.reasoning_call_count == 2, (
            "one invalid candidate + one repair call (item 21)"
        )
        body = chat_response.json()
        assert body["meta"]["reasoning_receipt_id"]

        async def runner():
            pool = await _make_pool()
            try:
                count = await _receipt_count(pool, company_id=company_id)
                row = await pool.fetchrow(
                    "SELECT response_snapshot FROM ome_reasoning_receipts WHERE company_id = $1", UUID(company_id)
                )
                return count, row
            finally:
                await pool.close()

        count, row = asyncio.run(runner())
        assert count == 1, "receipt created only once, for the FINAL repaired result (item 21)"
        import json as _json
        snapshot = _json.loads(row["response_snapshot"]) if isinstance(row["response_snapshot"], str) else row["response_snapshot"]
        assert "recommendation_basis" in snapshot["reasoning_assessment"], (
            "persisted snapshot is the repaired (valid), not the pre-repair invalid, candidate"
        )
    finally:

        async def cleanup_runner():
            pool = await _make_pool()
            try:
                await _cleanup(pool, company_id=company_id, user_id=user_id)
            finally:
                await pool.close()

        asyncio.run(cleanup_runner())
        _reset_stale_db_bindings(app, ai_engine)


def test_failed_reasoning_and_repair_creates_zero_receipts(tmp_path, monkeypatch) -> None:
    company_id, user_id, file_id, chat_response, fake_client = _upload_and_chat(
        tmp_path=tmp_path, monkeypatch=monkeypatch, mode="always_invalid", session_id="m8-s3a-fail-1",
    )
    try:
        assert chat_response.status_code == 500, chat_response.text

        async def runner():
            pool = await _make_pool()
            try:
                return await _receipt_count(pool, company_id=company_id)
            finally:
                await pool.close()

        count = asyncio.run(runner())
        assert count == 0, "failed reasoning/failed repair creates zero receipts (item 22/23)"
    finally:

        async def cleanup_runner():
            pool = await _make_pool()
            try:
                await _cleanup(pool, company_id=company_id, user_id=user_id)
            finally:
                await pool.close()

        asyncio.run(cleanup_runner())
        _reset_stale_db_bindings(app, ai_engine)


# ---------------------------------------------------------------------------
# TRUTH provenance helper - pure unit tests (items 11-16)
# ---------------------------------------------------------------------------

def _truth_catalog(entries: dict[str, dict]) -> dict:
    return {"truth": entries, "company_brain": {}}


def _usable_truth_entry(*, source_file_id: str | None) -> dict:
    return {
        "is_usable_evidence": True,
        "internal_source_item": {
            "canonical_field": "hall_temperature", "source_file_id": source_file_id,
        },
    }


def test_truth_helper_resolves_cited_t_ref_to_exact_file_uuid() -> None:
    file_id = str(uuid4())
    catalog = _truth_catalog({"T1": _usable_truth_entry(source_file_id=file_id)})
    refs = build_truth_evidence_refs(cited_evidence_basis_refs=["T1"], reasoning_reference_catalog=catalog)
    assert refs == [EvidenceRef(type="file", id=UUID(file_id))]


def test_truth_helper_uncited_entries_not_persisted() -> None:
    file_id = str(uuid4())
    catalog = _truth_catalog({
        "T1": _usable_truth_entry(source_file_id=file_id),
        "T2": _usable_truth_entry(source_file_id=str(uuid4())),
    })
    refs = build_truth_evidence_refs(cited_evidence_basis_refs=["T1"], reasoning_reference_catalog=catalog)
    assert len(refs) == 1
    assert refs[0].id == UUID(file_id)


def test_truth_helper_preserves_citation_order() -> None:
    file_a, file_b = str(uuid4()), str(uuid4())
    catalog = _truth_catalog({
        "T1": _usable_truth_entry(source_file_id=file_a),
        "T2": _usable_truth_entry(source_file_id=file_b),
    })
    refs = build_truth_evidence_refs(cited_evidence_basis_refs=["T2", "T1"], reasoning_reference_catalog=catalog)
    assert [str(r.id) for r in refs] == [file_b, file_a]


def test_truth_helper_preserves_duplicate_citations() -> None:
    file_id = str(uuid4())
    catalog = _truth_catalog({"T1": _usable_truth_entry(source_file_id=file_id)})
    refs = build_truth_evidence_refs(cited_evidence_basis_refs=["T1", "T1"], reasoning_reference_catalog=catalog)
    assert len(refs) == 2
    assert refs[0] == refs[1] == EvidenceRef(type="file", id=UUID(file_id))


def test_truth_helper_unresolved_cited_ref_fails_closed() -> None:
    catalog = _truth_catalog({})
    with pytest.raises(InvalidMemoryInput):
        build_truth_evidence_refs(cited_evidence_basis_refs=["T1"], reasoning_reference_catalog=catalog)


def test_truth_helper_missing_source_file_id_fails_closed() -> None:
    """Founder Correction 1: a cited T# that is real/usable but not
    file-backed must NEVER be silently skipped - it fails the whole
    receipt."""
    catalog = _truth_catalog({"T1": _usable_truth_entry(source_file_id=None)})
    with pytest.raises(InvalidMemoryInput):
        build_truth_evidence_refs(cited_evidence_basis_refs=["T1"], reasoning_reference_catalog=catalog)


def test_truth_helper_malformed_source_file_id_fails_closed() -> None:
    catalog = _truth_catalog({"T1": _usable_truth_entry(source_file_id="not-a-uuid")})
    with pytest.raises(InvalidMemoryInput):
        build_truth_evidence_refs(cited_evidence_basis_refs=["T1"], reasoning_reference_catalog=catalog)


def test_truth_helper_no_citations_is_valid() -> None:
    assert build_truth_evidence_refs(cited_evidence_basis_refs=[], reasoning_reference_catalog=_truth_catalog({})) == []


# ---------------------------------------------------------------------------
# _create_live_reasoning_receipt - real DB, direct call (items 14-16, 20,
# 32-33 structural)
# ---------------------------------------------------------------------------

def test_live_receipt_helper_truth_gap_fails_and_persists_nothing(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id, _department_id = await _seed_company_department_user(pool, label="gap")
            service = AIService()
            service.db_pool = pool
            decision_context = {
                "reasoning_reference_catalog": {
                    "truth": {"T1": _usable_truth_entry(source_file_id=None)},
                    "company_brain": {},
                }
            }
            reasoning_assessment = {
                "recommendation_basis": {"evidence_basis": ["T1"], "company_basis": [], "missing_evidence": []},
            }
            with pytest.raises(InvalidMemoryInput):
                await service._create_live_reasoning_receipt(
                    company_id=company_id, created_by_user_id=user_id, session_id="m8-s3a-gap",
                    ceo_text="x", reasoning_assessment=reasoning_assessment, decision_context=decision_context,
                )
            count = await _receipt_count(pool, company_id=company_id)
            assert count == 0, "no receipt persisted when Truth provenance cannot be represented (item 14/15/16)"
            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            await pool.close()

    _run(scenario())


def test_live_receipt_helper_cb_gap_fails_and_persists_nothing(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id, _department_id = await _seed_company_department_user(pool, label="cbgap")
            service = AIService()
            service.db_pool = pool
            decision_context = {
                "reasoning_reference_catalog": {
                    "truth": {},
                    "company_brain": {},  # CB1 cited but not present at all
                }
            }
            reasoning_assessment = {
                "recommendation_basis": {"evidence_basis": [], "company_basis": ["CB1"], "missing_evidence": []},
            }
            with pytest.raises(InvalidMemoryInput):
                await service._create_live_reasoning_receipt(
                    company_id=company_id, created_by_user_id=user_id, session_id="m8-s3a-cbgap",
                    ceo_text="x", reasoning_assessment=reasoning_assessment, decision_context=decision_context,
                )
            count = await _receipt_count(pool, company_id=company_id)
            assert count == 0, "no receipt persisted for an unresolved cited CB# (item 20)"
            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# PERSISTENCE FAILURE (items 24-27)
# ---------------------------------------------------------------------------

def test_persistence_failure_aborts_request_and_skips_all_side_effects(db_available, monkeypatch) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            company_id, user_id, _department_id = await _seed_company_department_user(pool, label="persistfail")

            service = AIService()
            service.client = SimpleNamespace(
                chat=SimpleNamespace(
                    completions=SimpleNamespace(
                        create=_always_valid_no_citation_completion,
                    )
                )
            )

            async def _boom(*args, **kwargs):
                raise RuntimeError("simulated receipt persistence failure")

            # Instance-attribute monkeypatch: chat() calls
            # self._create_live_reasoning_receipt(...) with only keyword
            # args, so a plain function assigned here (no manual `self`
            # binding needed) intercepts that exact call.
            monkeypatch.setattr(service, "_create_live_reasoning_receipt", _boom)

            key = service._memory_key(company_id, "m8-s3a-persistfail")
            with pytest.raises(Exception):
                await service.chat(
                    session_id="m8-s3a-persistfail",
                    message="hello",
                    context={},
                    company_id=company_id,
                    created_by_user_id=user_id,
                )

            # item 25: no assistant/user session-history append after failure
            # (self.sessions[key] is pre-initialized to [] early in chat(),
            # before the receipt-creation block - it must still be empty).
            assert key not in service.sessions or service.sessions[key] == []

            # items 26/27: the receipt raise happens BEFORE
            # log_decision_event_db/_extract_and_upsert_facts in the new
            # ordering (Founder Correction 2) - neither must have run for
            # this unseen response, regardless of whether service's own
            # lazily-created DB pool would otherwise have let them succeed.
            events = await pool.fetch("SELECT id FROM memory_events WHERE company_id = $1", company_id)
            facts = await pool.fetch("SELECT id FROM memory_facts WHERE company_id = $1", company_id)
            assert events == [], "no legacy DB memory event for the unseen response (item 26)"
            assert facts == [], "no memory-fact extraction/upsert from the unseen response (item 27)"

            count = await _receipt_count(pool, company_id=company_id)
            assert count == 0

            await _cleanup(pool, company_id=company_id, user_id=user_id)
        finally:
            if service.db_pool is not None:
                await service.db_pool.close()
            await pool.close()

    _run(scenario())


async def _always_valid_no_citation_completion(**kwargs):
    reasoning_assessment = {
        "reasoning_state": "insufficient_evidence",
        "operational_assessment": "x",
        "company_brain_alignment": "cannot determine",
        "tensions": [],
        "evidence_gaps": [],
        "risk_assessment": "x",
        "confidence": 40,
        "recommendation_basis": {
            "evidence_basis": [],
            "company_basis": [],
            "missing_evidence": [],
            "organizational_memory_basis": [],
        },
    }
    return _valid_ai_response(reasoning_assessment)


# ---------------------------------------------------------------------------
# DORMANCY / NON-GOALS (items 36-38) + structural client-injection immunity
# (items 32-33)
# ---------------------------------------------------------------------------

def test_no_outcome_supersession_api_added() -> None:
    """Historical note: before M8 Slice 3B-1, this test also asserted no
    app/api/*.py file referenced record_decision - proving the whole human
    decision-recording surface was dormant; that assertion became obsolete
    when Slice 3B-1 added app/api/decisions.py. Before M8 Slice 3C-1, this
    test ALSO asserted no app/api/*.py file referenced record_outcome/
    OutcomeMemoryService at all - proving outcome recording itself was
    still fully dormant. M8 Slice 3C-1 is the Founder-authorized round
    that adds exactly that API (app/api/outcomes.py, CREATE-only), so that
    assertion is now obsolete by design too, not a regression. What
    remains genuinely true and load-bearing is narrower: outcome
    SUPERSESSION specifically stays unexposed - no app/api/*.py file may
    CALL supersede_outcome. (The substring "supersede_outcome" legitimately
    appears in app/api/outcomes.py's own explanatory docstring, describing
    what stays deliberately unexposed - so this checks actual call-site
    usage, not prose.)"""
    import pathlib

    for path in pathlib.Path("app/api").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert ".supersede_outcome(" not in text


def test_no_migration_015() -> None:
    import pathlib

    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert not any(name.startswith("015") for name in migration_files)


def test_chat_request_model_has_no_provenance_fields() -> None:
    from app.models.request import ChatRequest

    assert "evidence_refs" not in ChatRequest.model_fields
    assert "company_brain_refs" not in ChatRequest.model_fields


def test_chat_route_never_reads_provenance_from_request() -> None:
    import pathlib

    text = pathlib.Path("app/api/chat.py").read_text(encoding="utf-8")
    assert "evidence_refs" not in text
    assert "company_brain_refs" not in text


# ---------------------------------------------------------------------------
# Final zero-leftover verification for this module
# ---------------------------------------------------------------------------

def test_zero_slice3a_leftovers_marker(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            companies = await pool.fetchval("SELECT count(*) FROM companies WHERE slug LIKE 'm8-s3a-%'")
            users = await pool.fetchval("SELECT count(*) FROM users WHERE email LIKE 'm8-s3a-%'")
            receipts = await pool.fetchval(
                "SELECT count(*) FROM ome_reasoning_receipts r JOIN companies c ON c.id = r.company_id "
                "WHERE c.slug LIKE 'm8-s3a-%'"
            )
            return companies, users, receipts
        finally:
            await pool.close()

    companies, users, receipts = _run(scenario())
    assert companies == 0
    assert users == 0
    assert receipts == 0
