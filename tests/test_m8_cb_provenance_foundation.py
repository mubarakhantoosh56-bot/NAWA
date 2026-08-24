"""Pre-Slice-3 Company Brain provenance foundation tests (real Postgres for
receipt-persistence tests; pure unit tests for the type/builder).

Proves: CompanyBrainProvenanceRef is a durable, self-contained snapshot
computed ONLY from a trusted internal_source_item's exact statement text
(never rereading a knowledge file); build_company_brain_provenance_refs
resolves ONLY already-cited CB# labels against a trusted
reasoning_reference_catalog, failing closed on anything unresolved;
ReasoningReceiptService.create_receipt persists Truth and Company Brain
provenance distinctly in the same evidence_refs JSONB array, enforcing
tenant safety and CB-citation completeness; and (no migration 015) this
foundation layer itself needs no schema change. Historical note: this
suite originally also proved the whole foundation was dormant (no
app/services/openai_client.py wiring at all) - M8 Slice 3A is the
Founder-authorized round that wires the live call inside
AIService.chat(); see test_api_route_never_directly_references_ome_
provenance_internals below for the narrower, still-true invariant that
replaced the old blanket dormancy assertion, and
tests/test_m8_slice3a_live_reasoning_receipts.py for the live-wiring
tests themselves.
"""
from __future__ import annotations

import asyncio
import hashlib
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.ome.errors import InvalidMemoryInput
from app.ome.models import ReasoningReceipt
from app.ome.provenance import build_company_brain_provenance_refs
from app.ome.repositories.reasoning_receipt_repository import ReasoningReceiptRepository
from app.ome.services.reasoning_receipt_service import ReasoningReceiptService
from app.ome.types import CompanyBrainProvenanceRef, EvidenceRef


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=6)


async def _seed_company_and_user(conn: asyncpg.Connection, *, label: str) -> tuple[str, str]:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m8-cbp-{label}-{uuid4().hex[:10]}", f"M8 CB Provenance Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-cbp-{label}-{uuid4().hex[:10]}@example.com", f"M8 CB Provenance Test User {label}",
    )
    return str(company_id), str(user_id)


async def _wipe_company(conn: asyncpg.Connection, company_id: str) -> None:
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE company_id=$1", company_id)


def _document_item(*, source: str = "DAIRTNA_DECISION_RULES", key: str = "قاعدة تجريبية", statement: str = "بعض النص التجريبي.") -> dict[str, Any]:
    return {
        "type": "DECISION_RULE",
        "key": key,
        "statement": statement,
        "scope": "company",
        "authority": "authoritative",
        "source": source,
        "source_type": "company_knowledge_document",
        "status": "available",
        "conflict_state": None,
        "provenance_note": None,
    }


def _memory_fact_item(*, key: str = "expansion_market", statement: str = "Cairo is the priority expansion market.") -> dict[str, Any]:
    return {
        "type": "INSTITUTIONAL_MEMORY",
        "key": key,
        "statement": statement,
        "scope": "company",
        "authority": "institutional",
        "source": "memory_facts",
        "source_type": "memory_fact",
        "status": "available",
        "conflict_state": None,
        "provenance_note": None,
    }


def _catalog(cb_items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "truth": {},
        "company_brain": {
            label: {"internal_source_item": item} for label, item in cb_items.items()
        },
    }


def _reasoning_assessment(*, company_basis: list[str] | None = None) -> dict[str, Any]:
    return {
        "reasoning_state": "aligned",
        "operational_assessment": "n/a",
        "company_brain_alignment": "supported by current evidence",
        "tensions": [],
        "evidence_gaps": [],
        "risk_assessment": "n/a",
        "confidence": 80,
        "recommendation_basis": {
            "evidence_basis": [],
            "company_basis": company_basis or [],
            "missing_evidence": [],
        },
    }


# ---------------------------------------------------------------------------
# DISCRIMINATED PROVENANCE ROUND-TRIP (Codex fix round)
# ---------------------------------------------------------------------------

def test_evidence_ref_to_dict_returns_exact_truth_shape() -> None:
    file_id = uuid4()
    ref = EvidenceRef(type="file", id=file_id)
    assert ref.to_dict() == {"category": "truth", "type": "file", "id": str(file_id)}


def test_evidence_ref_from_dict_round_trips_category_type_id() -> None:
    original = {"category": "truth", "type": "file", "id": str(uuid4())}
    assert EvidenceRef.from_dict(original).to_dict() == original


def test_evidence_ref_from_dict_rejects_missing_category() -> None:
    with pytest.raises(InvalidMemoryInput):
        EvidenceRef.from_dict({"type": "file", "id": str(uuid4())})


def test_evidence_ref_from_dict_rejects_company_brain_category() -> None:
    with pytest.raises(InvalidMemoryInput):
        EvidenceRef.from_dict({"category": "company_brain", "type": "file", "id": str(uuid4())})


def test_evidence_ref_from_dict_still_rejects_unsupported_type() -> None:
    with pytest.raises(InvalidMemoryInput):
        EvidenceRef.from_dict({"category": "truth", "type": "operational_event", "id": str(uuid4())})


def test_service_truth_persistence_still_stores_category_truth(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="dc1")
                file_id = await conn.fetchval(
                    """
                    INSERT INTO files (company_id, uploaded_by_user_id, filename, content_type, file_size_bytes, storage_path)
                    VALUES ($1, $2, $3, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 100, '/tmp/test.xlsx')
                    RETURNING id
                    """,
                    company_id, user_id, f"m8-cbp-test-{uuid4().hex[:10]}.xlsx",
                )
            service = ReasoningReceiptService(pool)
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={"ceo_text": "x", "reasoning_assessment": _reasoning_assessment()},
                evidence_refs=[EvidenceRef(type="file", id=UUID(str(file_id)))],
            )
            assert receipt.evidence_refs == [{"category": "truth", "type": "file", "id": str(file_id)}]
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM files WHERE company_id=$1", company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_service_no_longer_injects_truth_category_manually() -> None:
    """Structural proof (Codex Fix 1D): the service must rely on
    EvidenceRef.to_dict() as the sole serializer for truth refs - it must
    never itself construct a category="truth" dict literal around it."""
    import inspect

    from app.ome.services import reasoning_receipt_service as service_module

    source = inspect.getsource(service_module)
    assert '"category": "truth"' not in source
    assert "'category': 'truth'" not in source
    assert "persisted_refs.append(ref.to_dict())" in source


def test_company_brain_provenance_ref_to_dict_emits_category() -> None:
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=_document_item(), display_label="CB1",
    )
    assert ref.to_dict()["category"] == "company_brain"


def test_company_brain_provenance_ref_from_dict_round_trips_exactly() -> None:
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=_document_item(), display_label="CB1",
    )
    original = ref.to_dict()
    assert CompanyBrainProvenanceRef.from_dict(original).to_dict() == original


def test_company_brain_provenance_ref_from_dict_rejects_missing_category() -> None:
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=_document_item(),
    )
    payload = ref.to_dict()
    del payload["category"]
    with pytest.raises(InvalidMemoryInput):
        CompanyBrainProvenanceRef.from_dict(payload)


def test_company_brain_provenance_ref_from_dict_rejects_truth_category() -> None:
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=_document_item(),
    )
    payload = ref.to_dict()
    payload["category"] = "truth"
    with pytest.raises(InvalidMemoryInput):
        CompanyBrainProvenanceRef.from_dict(payload)


# ---------------------------------------------------------------------------
# TYPE / BUILDER
# ---------------------------------------------------------------------------

def test_company_brain_provenance_ref_is_frozen() -> None:
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=_document_item(), display_label="CB1",
    )
    with pytest.raises(Exception):
        ref.text_snapshot = "mutated"  # type: ignore[misc]


def test_document_backed_cb_item_builds_correctly() -> None:
    item = _document_item(source="DAIRTNA_DECISION_RULES", key="فلسفة المخاطرة", statement="خذ قرارات محسوبة المخاطر.")
    company_id = uuid4()
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=company_id, internal_source_item=item, display_label="CB1",
    )
    assert ref.company_id == company_id
    assert ref.source_key == "DAIRTNA_DECISION_RULES"
    assert ref.item_key == "فلسفة المخاطرة"
    assert ref.text_snapshot == "خذ قرارات محسوبة المخاطر."
    assert ref.display_label == "CB1"


def test_memory_facts_cb_item_builds_correctly() -> None:
    item = _memory_fact_item(key="expansion_market", statement="Cairo is the priority expansion market.")
    company_id = uuid4()
    ref = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=company_id, internal_source_item=item, display_label="CB2",
    )
    assert ref.source_key == "memory_facts"
    assert ref.item_key == "expansion_market"
    assert ref.text_snapshot == "Cairo is the priority expansion market."


def test_checksum_equals_sha256_of_exact_statement() -> None:
    statement = "This exact string is what the model saw this turn."
    item = _document_item(statement=statement)
    ref = CompanyBrainProvenanceRef.from_internal_source_item(company_id=uuid4(), internal_source_item=item)
    assert ref.content_sha256 == hashlib.sha256(statement.encode("utf-8")).hexdigest()


def test_statement_not_reread_or_recomputed_from_source() -> None:
    """Mutating the source dict AFTER construction must never retroactively
    change the ref - the ref captured a snapshot at construction time, not
    a live reference, and nothing here ever performs file I/O."""
    item = _document_item(statement="original statement text")
    ref = CompanyBrainProvenanceRef.from_internal_source_item(company_id=uuid4(), internal_source_item=item)
    original_checksum = ref.content_sha256

    item["statement"] = "a completely different statement, as if the source file changed later"

    assert ref.text_snapshot == "original statement text"
    assert ref.content_sha256 == original_checksum


def test_display_label_is_optional_debug_only() -> None:
    item = _document_item()
    ref_without_label = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=item,
    )
    assert ref_without_label.display_label is None

    ref_with_label = CompanyBrainProvenanceRef.from_internal_source_item(
        company_id=uuid4(), internal_source_item=item, display_label="CB7",
    )
    assert ref_with_label.display_label == "CB7"


def test_malformed_source_rejected() -> None:
    item = _document_item()
    del item["source"]
    with pytest.raises(InvalidMemoryInput):
        CompanyBrainProvenanceRef.from_internal_source_item(company_id=uuid4(), internal_source_item=item)


def test_malformed_key_rejected() -> None:
    item = _document_item()
    item["key"] = "   "
    with pytest.raises(InvalidMemoryInput):
        CompanyBrainProvenanceRef.from_internal_source_item(company_id=uuid4(), internal_source_item=item)


def test_malformed_statement_rejected() -> None:
    item = _document_item()
    item["statement"] = 12345
    with pytest.raises(InvalidMemoryInput):
        CompanyBrainProvenanceRef.from_internal_source_item(company_id=uuid4(), internal_source_item=item)


def test_unresolved_cited_cb_label_rejected() -> None:
    catalog = _catalog({"CB1": _document_item()})
    with pytest.raises(InvalidMemoryInput):
        build_company_brain_provenance_refs(
            company_id=uuid4(), cited_company_basis_refs=["CB5"], reasoning_reference_catalog=catalog,
        )


def test_citation_order_preserved() -> None:
    catalog = _catalog({
        "CB1": _document_item(key="rule one", statement="statement one"),
        "CB2": _document_item(key="rule two", statement="statement two"),
    })
    refs = build_company_brain_provenance_refs(
        company_id=uuid4(), cited_company_basis_refs=["CB2", "CB1"], reasoning_reference_catalog=catalog,
    )
    assert [ref.display_label for ref in refs] == ["CB2", "CB1"]
    assert [ref.item_key for ref in refs] == ["rule two", "rule one"]


def test_duplicate_cited_labels_preserved() -> None:
    catalog = _catalog({"CB1": _document_item()})
    refs = build_company_brain_provenance_refs(
        company_id=uuid4(), cited_company_basis_refs=["CB1", "CB1"], reasoning_reference_catalog=catalog,
    )
    assert len(refs) == 2
    assert refs[0].display_label == refs[1].display_label == "CB1"


# ---------------------------------------------------------------------------
# TENANT
# ---------------------------------------------------------------------------

def test_ref_uses_trusted_supplied_company_id() -> None:
    company_id = uuid4()
    catalog = _catalog({"CB1": _document_item()})
    refs = build_company_brain_provenance_refs(
        company_id=company_id, cited_company_basis_refs=["CB1"], reasoning_reference_catalog=catalog,
    )
    assert refs[0].company_id == company_id


def test_receipt_rejects_cb_ref_company_id_mismatch(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="t1")
            service = ReasoningReceiptService(pool)

            wrong_company_ref = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=uuid4(), internal_source_item=_document_item(), display_label="CB1",
            )
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                    response_snapshot={
                        "ceo_text": "x",
                        "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                    },
                    evidence_refs=[],
                    company_brain_refs=[wrong_company_ref],
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# RECEIPT
# ---------------------------------------------------------------------------

def test_canonical_response_snapshot_unchanged_with_cb_refs(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r1")
            service = ReasoningReceiptService(pool)
            cb_ref = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(), display_label="CB1",
            )
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={
                    "ceo_text": "x",
                    "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                    "prompt": "must be dropped",
                },
                evidence_refs=[],
                company_brain_refs=[cb_ref],
            )
            assert set(receipt.response_snapshot.keys()) == {"ceo_text", "reasoning_assessment"}
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_truth_and_company_brain_provenance_persist_distinctly(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r2")
                file_id = await conn.fetchval(
                    """
                    INSERT INTO files (company_id, uploaded_by_user_id, filename, content_type, file_size_bytes, storage_path)
                    VALUES ($1, $2, $3, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 100, '/tmp/test.xlsx')
                    RETURNING id
                    """,
                    company_id, user_id, f"m8-cbp-test-{uuid4().hex[:10]}.xlsx",
                )
            service = ReasoningReceiptService(pool)
            cb_ref = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(), display_label="CB1",
            )
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={
                    "ceo_text": "x",
                    "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                },
                evidence_refs=[EvidenceRef(type="file", id=UUID(str(file_id)))],
                company_brain_refs=[cb_ref],
            )
            categories = sorted(entry["category"] for entry in receipt.evidence_refs)
            assert categories == ["company_brain", "truth"]
            truth_entry = next(e for e in receipt.evidence_refs if e["category"] == "truth")
            cb_entry = next(e for e in receipt.evidence_refs if e["category"] == "company_brain")
            assert truth_entry["type"] == "file"
            assert truth_entry["id"] == str(file_id)
            assert cb_entry["source_key"] == "DAIRTNA_DECISION_RULES"
            assert cb_entry["display_label"] == "CB1"
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM files WHERE company_id=$1", company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_no_company_basis_cited_means_empty_cb_refs_valid(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r3")
            service = ReasoningReceiptService(pool)
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={"ceo_text": "x", "reasoning_assessment": _reasoning_assessment()},
                evidence_refs=[],
                company_brain_refs=[],
            )
            assert receipt.evidence_refs == []
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_cited_cb1_missing_provenance_fails_closed(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r4")
            service = ReasoningReceiptService(pool)
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                    response_snapshot={
                        "ceo_text": "x",
                        "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                    },
                    evidence_refs=[],
                    company_brain_refs=[],
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_cited_cb1_cb2_both_must_be_represented(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r5")
            service = ReasoningReceiptService(pool)
            ref1 = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(key="rule one"), display_label="CB1",
            )
            ref2 = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(key="rule two"), display_label="CB2",
            )
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={
                    "ceo_text": "x",
                    "reasoning_assessment": _reasoning_assessment(company_basis=["CB1", "CB2"]),
                },
                evidence_refs=[],
                company_brain_refs=[ref1, ref2],
            )
            labels = [entry["display_label"] for entry in receipt.evidence_refs]
            assert labels == ["CB1", "CB2"]
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_extra_uncited_cb_provenance_rejected(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r6")
            service = ReasoningReceiptService(pool)
            ref1 = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(key="rule one"), display_label="CB1",
            )
            ref2 = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(key="rule two"), display_label="CB2",
            )
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                    response_snapshot={
                        "ceo_text": "x",
                        "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                    },
                    evidence_refs=[],
                    company_brain_refs=[ref1, ref2],
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_persisted_text_snapshot_survives_exact(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r7")
            service = ReasoningReceiptService(pool)
            repo = ReasoningReceiptRepository(pool)
            exact_statement = "هذا هو النص الدقيق الذي رآه النموذج في هذا الطلب."
            cb_ref = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id),
                internal_source_item=_document_item(statement=exact_statement),
                display_label="CB1",
            )
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={
                    "ceo_text": "x",
                    "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                },
                evidence_refs=[],
                company_brain_refs=[cb_ref],
            )
            fetched = await repo.get_by_id(company_id=UUID(company_id), receipt_id=receipt.id)
            assert fetched is not None
            cb_entry = fetched.evidence_refs[0]
            assert cb_entry["text_snapshot"] == exact_statement
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_persisted_checksum_matches_persisted_snapshot(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r8")
            service = ReasoningReceiptService(pool)
            repo = ReasoningReceiptRepository(pool)
            cb_ref = CompanyBrainProvenanceRef.from_internal_source_item(
                company_id=UUID(company_id), internal_source_item=_document_item(), display_label="CB1",
            )
            receipt = await service.create_receipt(
                company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                response_snapshot={
                    "ceo_text": "x",
                    "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                },
                evidence_refs=[],
                company_brain_refs=[cb_ref],
            )
            fetched = await repo.get_by_id(company_id=UUID(company_id), receipt_id=receipt.id)
            assert fetched is not None
            cb_entry = fetched.evidence_refs[0]
            expected = hashlib.sha256(cb_entry["text_snapshot"].encode("utf-8")).hexdigest()
            assert cb_entry["content_sha256"] == expected
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


def test_company_brain_refs_rejects_client_shaped_raw_dict(db_available) -> None:
    """Structural dormancy proof: create_receipt only ever accepts real
    CompanyBrainProvenanceRef instances - a raw dict shaped like one (as a
    client-facing/API path might naively pass through) is rejected, never
    silently trusted."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                company_id, user_id = await _seed_company_and_user(conn, label="r9")
            service = ReasoningReceiptService(pool)
            client_shaped_dict = {
                "company_id": company_id,
                "source_key": "DAIRTNA_DECISION_RULES",
                "item_key": "فلسفة المخاطرة",
                "content_sha256": "0" * 64,
                "text_snapshot": "attacker-supplied text",
                "display_label": "CB1",
            }
            with pytest.raises(InvalidMemoryInput):
                await service.create_receipt(
                    company_id=UUID(company_id), created_by_user_id=UUID(user_id), session_id=None,
                    response_snapshot={
                        "ceo_text": "x",
                        "reasoning_assessment": _reasoning_assessment(company_basis=["CB1"]),
                    },
                    evidence_refs=[],
                    company_brain_refs=[client_shaped_dict],  # type: ignore[list-item]
                )
            async with pool.acquire() as conn:
                await _wipe_company(conn, company_id)
                await conn.execute("DELETE FROM users WHERE id=$1", user_id)
                await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# DORMANCY
# ---------------------------------------------------------------------------

def test_no_api_module_imports_provenance_helper() -> None:
    import pathlib

    api_dir = pathlib.Path("app/api")
    for path in api_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "app.ome.provenance" not in text
        assert "build_company_brain_provenance_refs" not in text


def test_api_route_never_directly_references_ome_provenance_internals() -> None:
    """Historical note: before M8 Slice 3A, this test asserted
    app/services/openai_client.py never referenced create_receipt/
    CompanyBrainProvenanceRef/build_company_brain_provenance_refs at all -
    proving the whole foundation was dormant. M8 Slice 3A is exactly the
    Founder-authorized round that wires that live call inside
    AIService.chat() (see that module's _create_live_reasoning_receipt),
    so that specific assertion is now obsolete by design, not a
    regression - the real, still-load-bearing invariant this test
    protects is narrower and remains true: the API ROUTE layer
    (app/api/chat.py) itself never references these OME internals
    directly - it only ever calls ai_engine.chat(...), keeping all
    provenance extraction/receipt-creation logic encapsulated in the
    service layer, never spread into the route/API surface."""
    import pathlib

    text = pathlib.Path("app/api/chat.py").read_text(encoding="utf-8")
    assert "build_company_brain_provenance_refs" not in text
    assert "CompanyBrainProvenanceRef" not in text
    assert "create_receipt" not in text
    assert "ReasoningReceiptService" not in text


def test_no_migration_015() -> None:
    import pathlib

    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert not any(name.startswith("015") for name in migration_files)
    assert "014_organizational_memory.sql" in migration_files


# ---------------------------------------------------------------------------
# Final zero-leftover verification for this module
# ---------------------------------------------------------------------------

def test_zero_cb_provenance_leftovers_marker(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                companies = await conn.fetchval("SELECT count(*) FROM companies WHERE slug LIKE 'm8-cbp-%'")
                users = await conn.fetchval("SELECT count(*) FROM users WHERE email LIKE 'm8-cbp-%'")
                files = await conn.fetchval("SELECT count(*) FROM files WHERE filename LIKE 'm8-cbp-%'")
                return companies, users, files
        finally:
            await pool.close()

    companies, users, files = _run(scenario())
    assert companies == 0
    assert users == 0
    assert files == 0
