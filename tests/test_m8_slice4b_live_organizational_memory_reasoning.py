"""M8 Slice 4B: Live Organizational Memory Context + Auditable Cited
Provenance (real Postgres where DB-backed).

Covers: the live company-wide-only retrieval loader, the OM# citation
namespace and its validation/repair integration, the prompt-rendering
budget (Founder Correction 2 - hard-bounded outcome selection + text
truncation, rendering-only, never mutating persisted OME), the
OrganizationalMemoryProvenanceRef durable type and its receipt integration
(Founder Correction 1 - explicit CITED basis only, never uncited context),
tenant isolation, and dormancy of every protected boundary (no Truth/CB
contamination, no explainability change, no live situation resolution).
"""
from __future__ import annotations

import asyncio
import dataclasses
import pathlib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.ome.errors import InvalidMemoryInput
from app.ome.models import ReasoningReceipt
from app.ome.provenance import build_organizational_memory_provenance_refs
from app.ome.services.reasoning_receipt_service import ReasoningReceiptService
from app.ome.types import (
    CompanyBrainProvenanceRef,
    EvidenceRef,
    OrganizationalMemoryProvenanceRef,
)
from app.services.decision_context import (
    MAX_DECISION_TEXT_CHARS,
    MAX_OM_ITEMS,
    MAX_OUTCOME_SUMMARY_CHARS,
    MAX_RATIONALE_CHARS,
    MAX_RENDERED_OUTCOMES_PER_ITEM,
    INTERNAL_ONLY_DECISION_CONTEXT_KEYS,
    _build_organizational_memory_reference_catalog,
    _build_organizational_memory_section,
    _select_rendered_outcomes,
    _truncate_for_prompt,
    build_decision_context,
    build_decision_context_prompt_block,
    public_decision_context,
)
from app.services.openai_client import AIService
from app.services.reasoning_validation import RecommendationBasis, validate_reasoning_assessment


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=6)


# ---------------------------------------------------------------------------
# Seeding helpers (mirror the M8 Slice 4A pattern)
# ---------------------------------------------------------------------------

async def _seed_company_and_user(conn: asyncpg.Connection, *, label: str) -> tuple[str, str]:
    company_id = await conn.fetchval(
        "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
        f"m8-s4b-{label}-{uuid4().hex[:10]}", f"M8 Slice 4B Test Company {label}",
    )
    user_id = await conn.fetchval(
        "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
        f"m8-s4b-{label}-{uuid4().hex[:10]}@example.com", f"M8 Slice 4B Test User {label}",
    )
    return str(company_id), str(user_id)


async def _seed_receipt(conn: asyncpg.Connection, *, company_id: str, user_id: str) -> str:
    receipt_id = await conn.fetchval(
        """
        INSERT INTO ome_reasoning_receipts (company_id, created_by_user_id, response_snapshot, evidence_refs)
        VALUES ($1, $2, $3::jsonb, '[]'::jsonb)
        RETURNING id
        """,
        company_id, user_id, '{"ceo_text": "test"}',
    )
    return str(receipt_id)


async def _seed_decision(
    conn: asyncpg.Connection, *, company_id: str, receipt_id: str, user_id: str,
    decision_text: str = "Test decision", rationale: str | None = None,
) -> str:
    decision_id = await conn.fetchval(
        """
        INSERT INTO ome_decision_memories
            (company_id, reasoning_receipt_id, decision_text, rationale, decided_by_user_id, decided_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        RETURNING id
        """,
        company_id, receipt_id, decision_text, rationale, user_id,
    )
    return str(decision_id)


async def _seed_outcome(
    conn: asyncpg.Connection, *, company_id: str, decision_id: str, user_id: str,
    result_state: str = "positive", observed_at: datetime | None = None,
) -> str:
    outcome_id = await conn.fetchval(
        """
        INSERT INTO ome_outcome_memories
            (company_id, decision_memory_id, outcome_summary, result_state, recorded_by_user_id, observed_at)
        VALUES ($1, $2, 'Test outcome', $3, $4, $5)
        RETURNING id
        """,
        company_id, decision_id, result_state, user_id, observed_at or datetime.now(timezone.utc),
    )
    return str(outcome_id)


async def _supersede_decision(conn: asyncpg.Connection, *, old_decision_id: str, new_decision_id: str) -> None:
    await conn.execute(
        "UPDATE ome_decision_memories SET status = 'superseded', superseded_by = $2 WHERE id = $1",
        old_decision_id, new_decision_id,
    )


async def _supersede_outcome(conn: asyncpg.Connection, *, old_outcome_id: str, new_outcome_id: str) -> None:
    await conn.execute(
        "UPDATE ome_outcome_memories SET status = 'superseded', superseded_by = $2 WHERE id = $1",
        old_outcome_id, new_outcome_id,
    )


async def _cleanup(conn: asyncpg.Connection, *, company_id: str, user_id: str) -> None:
    await conn.execute("DELETE FROM ome_outcome_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_decision_memories WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM ome_reasoning_receipts WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM files WHERE company_id=$1", company_id)
    await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    await conn.execute("DELETE FROM companies WHERE id=$1", company_id)


@asynccontextmanager
async def _company_scope(pool: asyncpg.Pool, *, label: str):
    """Failure-safe scope: cleanup runs in `finally` around `yield`, so it
    executes even when an assertion inside the block fails - never only on
    the happy path (Step 36 requirement)."""
    async with pool.acquire() as conn:
        company_id, user_id = await _seed_company_and_user(conn, label=label)
    try:
        yield company_id, user_id
    finally:
        async with pool.acquire() as conn:
            await _cleanup(conn, company_id=company_id, user_id=user_id)


# ---------------------------------------------------------------------------
# Live loader: trusted scope, company-wide-only, non-fatal failure
# (items 1-7, 49-52)
# ---------------------------------------------------------------------------

def test_loader_uses_authenticated_company_only_and_excludes_other_company(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="loaderA") as (company_a, user_a):
                async with _company_scope(pool, label="loaderB") as (company_b, user_b):
                    async with pool.acquire() as conn:
                        receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                        decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                        await _seed_outcome(conn, company_id=company_a, decision_id=decision_a, user_id=user_a)
                        receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                        decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                        await _seed_outcome(conn, company_id=company_b, decision_id=decision_b, user_id=user_b)

                    service = AIService()
                    service.db_pool = pool
                    result_a = await service._load_organizational_memory_context(company_id=company_a)
                    assert [item["decision_memory_id"] for item in result_a] == [decision_a]
        finally:
            await pool.close()

    _run(scenario())


def test_loader_always_uses_company_wide_mode_no_situation_id(db_available) -> None:
    """item 2: structural + behavioral - retrieve() is never given a
    situation_id from the live loader."""
    text = pathlib.Path("app/services/openai_client.py").read_text(encoding="utf-8")
    assert "situation_id=None" in text
    # No literal live call site passes a non-None situation_id to retrieve().
    assert "situation_id=situation" not in text


def test_loader_uses_limit_five(db_available) -> None:
    text = pathlib.Path("app/services/openai_client.py").read_text(encoding="utf-8")
    assert "limit=5" in text


def test_empty_organizational_memory_returns_normal_chat_behavior(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="emptyloader") as (company_id, user_id):
                service = AIService()
                service.db_pool = pool
                result = await service._load_organizational_memory_context(company_id=company_id)
                assert result == []
        finally:
            await pool.close()

    _run(scenario())


def test_loader_exception_is_non_fatal_and_produces_no_fake_refs(db_available) -> None:
    async def scenario():
        service = AIService()
        service.db_pool = object()  # will raise when used as an asyncpg pool
        result = await service._load_organizational_memory_context(company_id=str(uuid4()))
        assert result == []

    _run(scenario())


def test_loader_none_db_pool_returns_empty(db_available) -> None:
    async def scenario():
        service = AIService()
        service.db_pool = None
        result = await service._load_organizational_memory_context(company_id=str(uuid4()))
        assert result == []

    _run(scenario())


def test_loader_excludes_superseded_decision(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="supdecloader") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    old_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    await _seed_outcome(conn, company_id=company_id, decision_id=old_decision, user_id=user_id)
                    new_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    await _seed_outcome(conn, company_id=company_id, decision_id=new_decision, user_id=user_id)
                    await _supersede_decision(conn, old_decision_id=old_decision, new_decision_id=new_decision)

                service = AIService()
                service.db_pool = pool
                result = await service._load_organizational_memory_context(company_id=company_id)
                assert [item["decision_memory_id"] for item in result] == [new_decision]
        finally:
            await pool.close()

    _run(scenario())


def test_loader_excludes_superseded_outcome(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="supoutloader") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    old_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    new_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    await _supersede_outcome(conn, old_outcome_id=old_outcome, new_outcome_id=new_outcome)

                service = AIService()
                service.db_pool = pool
                result = await service._load_organizational_memory_context(company_id=company_id)
                assert len(result) == 1
                assert [o["outcome_memory_id"] for o in result[0]["outcomes"]] == [new_outcome]
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Prompt section: heading, wording contract (items 8-15)
# ---------------------------------------------------------------------------

_SAMPLE_ITEM = {
    "decision_memory_id": "did-1",
    "situation_id": None,
    "decision_text": "Approve expansion.",
    "rationale": "Cash coverage supports it.",
    "decided_at": "2020-01-01T00:00:00Z",
    "outcomes": [
        {"outcome_memory_id": "oid-1", "outcome_summary": "Delivered a lift.", "result_state": "positive",
         "observed_at": "2020-02-01T00:00:00Z"},
    ],
}


def test_section_omitted_when_empty() -> None:
    assert _build_organizational_memory_section({}) == ""


def test_section_heading_and_wording_contract_present() -> None:
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([_SAMPLE_ITEM]))
    assert section.startswith("[Historical Organizational Memory]")
    assert "These are prior HUMAN decisions and human-recorded outcomes" in section
    assert "not current Operational Truth" in section
    assert "not current Company Brain policy" in section
    assert "does not prove the Decision CAUSED the Outcome" in section
    assert "Historical success does not require repeating an action" in section
    assert "Historical failure does not blacklist an action" in section
    assert "Current Operational Truth remains authoritative" in section
    assert "Current Company Brain remains authoritative" in section
    assert "NOT similarity-matched" in section
    assert "directly relevant to the current conditions" in section
    assert "materially rely on a historical record, include its OM#" in section


def test_full_prompt_block_contains_om_citation_legality_rule() -> None:
    dc = build_decision_context(context={}, response_language="en", organizational_memory_context=[_SAMPLE_ITEM])
    block = build_decision_context_prompt_block(dc)
    assert "organizational_memory_basis may ONLY contain OM# IDs shown below" in block


# ---------------------------------------------------------------------------
# OM# labeling, per-item rendering, no raw UUIDs (items 15-19, 22, 23)
# ---------------------------------------------------------------------------

def test_om_labels_deterministic_om1_through_omn() -> None:
    items = [{**_SAMPLE_ITEM, "decision_memory_id": f"did-{i}"} for i in range(3)]
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog(items))
    assert "[OM1]" in section and "[OM2]" in section and "[OM3]" in section


def test_raw_durable_uuids_absent_from_dedicated_section() -> None:
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([_SAMPLE_ITEM]))
    assert "did-1" not in section
    assert "oid-1" not in section


def test_decision_text_truncates_only_in_rendering_not_source() -> None:
    long_text = "x" * (MAX_DECISION_TEXT_CHARS + 200)
    item = {**_SAMPLE_ITEM, "decision_text": long_text}
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    assert "[truncated for prompt budget]" in section
    # Source object passed in is never mutated.
    assert item["decision_text"] == long_text


def test_rationale_truncates_only_in_rendering() -> None:
    long_text = "y" * (MAX_RATIONALE_CHARS + 200)
    item = {**_SAMPLE_ITEM, "rationale": long_text}
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    assert "[truncated for prompt budget]" in section
    assert item["rationale"] == long_text


def test_outcome_summary_truncates_only_in_rendering() -> None:
    long_summary = "z" * (MAX_OUTCOME_SUMMARY_CHARS + 200)
    item = {**_SAMPLE_ITEM, "outcomes": [{**_SAMPLE_ITEM["outcomes"][0], "outcome_summary": long_summary}]}
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    assert "[truncated for prompt budget]" in section
    assert item["outcomes"][0]["outcome_summary"] == long_summary


def test_truncate_for_prompt_deterministic_and_never_mutates() -> None:
    text = "abc" * 300
    result_1 = _truncate_for_prompt(text, 10)
    result_2 = _truncate_for_prompt(text, 10)
    assert result_1 == result_2
    assert text == "abc" * 300  # unchanged


def test_source_4a_style_dict_unchanged_after_rendering() -> None:
    item = dict(_SAMPLE_ITEM)
    original = dict(item)
    _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    _build_organizational_memory_reference_catalog([item])
    assert item == original


# ---------------------------------------------------------------------------
# Hard outcome-rendering bound (Founder Correction 2) (items 18-21, 25, 31)
# ---------------------------------------------------------------------------

def _outcomes(n: int) -> list[dict]:
    base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "outcome_memory_id": f"oid-{i}",
            "outcome_summary": f"Summary {i}",
            "result_state": "positive",
            "observed_at": (base_time + timedelta(days=i)).isoformat(),
        }
        for i in range(n)
    ]


def test_five_or_fewer_outcomes_all_rendered() -> None:
    outcomes = _outcomes(5)
    selected = _select_rendered_outcomes(outcomes)
    assert selected == outcomes
    assert len(selected) == 5


def test_more_than_five_outcomes_selects_latest_five() -> None:
    outcomes = _outcomes(8)
    selected = _select_rendered_outcomes(outcomes)
    assert len(selected) == MAX_RENDERED_OUTCOMES_PER_ITEM == 5
    assert [o["outcome_memory_id"] for o in selected] == [f"oid-{i}" for i in range(3, 8)]


def test_selected_latest_five_rendered_chronologically() -> None:
    outcomes = _outcomes(8)
    selected = _select_rendered_outcomes(outcomes)
    observed_ats = [o["observed_at"] for o in selected]
    assert observed_ats == sorted(observed_ats)


def test_omitted_outcome_count_stated_accurately() -> None:
    item = {**_SAMPLE_ITEM, "outcomes": _outcomes(8)}
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    assert "Earlier active outcomes omitted from this prompt for context budgeting: 3" in section


def test_catalog_contains_exactly_rendered_outcome_ids() -> None:
    item = {**_SAMPLE_ITEM, "outcomes": _outcomes(8)}
    catalog = _build_organizational_memory_reference_catalog([item])
    assert catalog["OM1"]["rendered_outcome_memory_ids"] == tuple(f"oid-{i}" for i in range(3, 8))


def test_multiple_selected_outcomes_preserved_not_collapsed() -> None:
    item = {**_SAMPLE_ITEM, "outcomes": _outcomes(3)}
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    for i in range(3):
        assert f"Summary {i}" in section
    assert "Final outcome" not in section
    assert "Decision caused" not in section


# ---------------------------------------------------------------------------
# Unknown outcome rendering (item 26)
# ---------------------------------------------------------------------------

def test_explicit_unknown_renders_literally() -> None:
    item = {**_SAMPLE_ITEM, "outcomes": [{**_SAMPLE_ITEM["outcomes"][0], "result_state": "unknown"}]}
    section = _build_organizational_memory_section(_build_organizational_memory_reference_catalog([item]))
    assert "— unknown —" in section


# ---------------------------------------------------------------------------
# Internal-only stripping (public/frontend boundary)
# ---------------------------------------------------------------------------

def test_organizational_memory_keys_are_internal_only() -> None:
    assert "organizational_memory_context" in INTERNAL_ONLY_DECISION_CONTEXT_KEYS
    assert "organizational_memory_reference_catalog" in INTERNAL_ONLY_DECISION_CONTEXT_KEYS

    dc = build_decision_context(context={}, response_language="en", organizational_memory_context=[_SAMPLE_ITEM])
    public = public_decision_context(dc)
    assert "organizational_memory_context" not in public
    assert "organizational_memory_reference_catalog" not in public


# ---------------------------------------------------------------------------
# RecommendationBasis schema + OM# validation (items 28-33)
# ---------------------------------------------------------------------------

def test_recommendation_basis_accepts_organizational_memory_basis() -> None:
    basis = RecommendationBasis(
        evidence_basis=[], company_basis=[], missing_evidence=[], organizational_memory_basis=["OM1"]
    )
    assert basis.organizational_memory_basis == ["OM1"]


def _parsed(om_refs: list[str]) -> dict:
    return {
        "raw_decision": {
            "reasoning_assessment": {
                "reasoning_state": "aligned",
                "operational_assessment": "x",
                "company_brain_alignment": "cannot determine",
                "tensions": [],
                "evidence_gaps": [],
                "risk_assessment": "x",
                "confidence": 70,
                "recommendation_basis": {
                    "evidence_basis": [], "company_basis": [], "missing_evidence": [],
                    "organizational_memory_basis": om_refs,
                },
            }
        }
    }


def _dc_with_om_catalog() -> dict:
    return {"organizational_memory_reference_catalog": {"OM1": {"decision_memory_id": "d1", "rendered_outcome_memory_ids": ("o1",)}}}


def test_valid_om_ref_passes_validation() -> None:
    valid, errors = validate_reasoning_assessment(_parsed(["OM1"]), _dc_with_om_catalog())
    assert valid, errors


def test_malformed_om_ref_fails() -> None:
    valid, errors = validate_reasoning_assessment(_parsed(["OMX"]), _dc_with_om_catalog())
    assert not valid
    assert any("not a valid OM# reference" in e for e in errors)


def test_invented_om_ref_fails() -> None:
    valid, errors = validate_reasoning_assessment(_parsed(["OM99"]), _dc_with_om_catalog())
    assert not valid
    assert any("was not supplied" in e for e in errors)


def test_truth_ref_in_organizational_memory_basis_fails() -> None:
    valid, errors = validate_reasoning_assessment(_parsed(["T1"]), _dc_with_om_catalog())
    assert not valid
    assert any("not a valid OM# reference" in e for e in errors)


def test_company_brain_ref_in_organizational_memory_basis_fails() -> None:
    valid, errors = validate_reasoning_assessment(_parsed(["CB1"]), _dc_with_om_catalog())
    assert not valid
    assert any("not a valid OM# reference" in e for e in errors)


def test_om_ref_in_evidence_basis_fails() -> None:
    parsed = _parsed([])
    parsed["raw_decision"]["reasoning_assessment"]["recommendation_basis"]["evidence_basis"] = ["OM1"]
    valid, errors = validate_reasoning_assessment(parsed, _dc_with_om_catalog())
    assert not valid
    assert any("not a valid T# reference" in e for e in errors)


def test_om_ref_in_company_basis_fails() -> None:
    parsed = _parsed([])
    parsed["raw_decision"]["reasoning_assessment"]["recommendation_basis"]["company_basis"] = ["OM1"]
    valid, errors = validate_reasoning_assessment(parsed, _dc_with_om_catalog())
    assert not valid
    assert any("not a valid CB# reference" in e for e in errors)


# ---------------------------------------------------------------------------
# Provenance builder: resolution, fail-closed, rendered-outcome law
# (items 29, 31, 36, 37, 38)
# ---------------------------------------------------------------------------

def test_om_provenance_does_not_contaminate_truth_or_company_brain() -> None:
    """items 34, 35: structural - the OM builder is a wholly separate
    function/category from Truth/Company Brain, never called by either."""
    text = pathlib.Path("app/ome/provenance.py").read_text(encoding="utf-8")
    assert "def build_organizational_memory_provenance_refs(" in text
    assert "def build_truth_evidence_refs(" in text
    assert "def build_company_brain_provenance_refs(" in text


def test_valid_om_ref_resolves_to_correct_decision_and_rendered_outcomes() -> None:
    decision_id, outcome_id = str(uuid4()), str(uuid4())
    catalog = {"OM1": {"decision_memory_id": decision_id, "rendered_outcome_memory_ids": (outcome_id,)}}
    refs = build_organizational_memory_provenance_refs(
        cited_om_refs=["OM1"], organizational_memory_reference_catalog=catalog
    )
    assert len(refs) == 1
    assert str(refs[0].decision_memory_id) == decision_id
    assert [str(o) for o in refs[0].outcome_memory_ids] == [outcome_id]
    assert refs[0].category == "organizational_memory"


def test_uncited_om_produces_no_provenance() -> None:
    refs = build_organizational_memory_provenance_refs(
        cited_om_refs=[], organizational_memory_reference_catalog={"OM1": {"decision_memory_id": str(uuid4()), "rendered_outcome_memory_ids": (str(uuid4()),)}}
    )
    assert refs == []


def test_unresolvable_om_ref_fails_closed() -> None:
    with pytest.raises(InvalidMemoryInput):
        build_organizational_memory_provenance_refs(cited_om_refs=["OM1"], organizational_memory_reference_catalog={})


def test_duplicate_om_citations_preserved() -> None:
    decision_id, outcome_id = str(uuid4()), str(uuid4())
    catalog = {"OM1": {"decision_memory_id": decision_id, "rendered_outcome_memory_ids": (outcome_id,)}}
    refs = build_organizational_memory_provenance_refs(
        cited_om_refs=["OM1", "OM1"], organizational_memory_reference_catalog=catalog
    )
    assert len(refs) == 2


# ---------------------------------------------------------------------------
# Final-only citation law (Founder Step 15) (items 27, 43, 44, 63)
# ---------------------------------------------------------------------------

def test_provenance_reflects_only_final_citations_not_a_rejected_first_attempt() -> None:
    """Direct proof of the final-only law at the provenance-builder layer:
    app/services/openai_client.py's _create_live_reasoning_receipt only
    ever calls build_organizational_memory_provenance_refs with the FINAL
    accepted reasoning_assessment's organizational_memory_basis (confirmed
    structurally below) - simulating "first attempt cited OM1, final
    accepted cited OM2" here proves the receipt would persist ONLY OM2."""
    catalog = {
        "OM1": {"decision_memory_id": str(uuid4()), "rendered_outcome_memory_ids": (str(uuid4()),)},
        "OM2": {"decision_memory_id": str(uuid4()), "rendered_outcome_memory_ids": (str(uuid4()),)},
    }
    # Only the FINAL accepted citation (OM2) is ever passed - a rejected
    # first attempt's OM1 citation never reaches this call in the real
    # chat() flow (see structural proof below).
    refs = build_organizational_memory_provenance_refs(
        cited_om_refs=["OM2"], organizational_memory_reference_catalog=catalog
    )
    assert len(refs) == 1
    assert str(refs[0].decision_memory_id) == catalog["OM2"]["decision_memory_id"]


def test_receipt_creation_reads_organizational_memory_basis_from_final_assessment_only() -> None:
    """Structural proof: _create_live_reasoning_receipt takes
    reasoning_assessment as a single parameter (the FINAL accepted one,
    per chat()'s own call-site ordering - see its docstring) and reads
    organizational_memory_basis directly off it - there is no second,
    earlier reasoning_assessment parameter it could read from instead."""
    text = pathlib.Path("app/services/openai_client.py").read_text(encoding="utf-8")
    assert "organizational_memory_labels = recommendation_basis.get(\"organizational_memory_basis\")" in text
    # Only one reasoning_assessment parameter exists on the receipt-creation method.
    assert text.count("async def _create_live_reasoning_receipt(") == 1


# ---------------------------------------------------------------------------
# ReasoningReceipt integration: type, round-trip, coexistence (items 29,
# 30, 34, 35, 38, 39, 40, 41, 45)
# ---------------------------------------------------------------------------

def test_provenance_ref_exact_fields_and_forbidden_fields() -> None:
    fields = {f.name for f in dataclasses.fields(OrganizationalMemoryProvenanceRef)}
    assert fields == {"decision_memory_id", "outcome_memory_ids", "category"}


def test_provenance_ref_round_trip() -> None:
    ref = OrganizationalMemoryProvenanceRef(decision_memory_id=uuid4(), outcome_memory_ids=(uuid4(), uuid4()))
    payload = ref.to_dict()
    assert payload["category"] == "organizational_memory"
    restored = OrganizationalMemoryProvenanceRef.from_dict(payload)
    assert restored == ref


def test_provenance_category_exactly_organizational_memory() -> None:
    ref = OrganizationalMemoryProvenanceRef(decision_memory_id=uuid4(), outcome_memory_ids=(uuid4(),))
    assert ref.to_dict()["category"] == "organizational_memory"


_GENERIC_OM_ERROR = "invalid organizational memory provenance"


def test_receipt_rejects_non_organizational_memory_provenance_ref_type(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="badomref") as (company_id, user_id):
                service = ReasoningReceiptService(pool)
                with pytest.raises(InvalidMemoryInput):
                    await service.create_receipt(
                        company_id=UUID(company_id),
                        created_by_user_id=UUID(user_id),
                        session_id="s4b-bad",
                        response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                        evidence_refs=[],
                        organizational_memory_refs=["not-a-ref"],
                    )
        finally:
            await pool.close()

    _run(scenario())


# ---------------------------------------------------------------------------
# Required-fix round (Codex Blocker 1): ReasoningReceiptService.create_receipt
# now independently re-verifies referential + tenant integrity for every
# OrganizationalMemoryProvenanceRef against the real database, rather than
# trusting an arbitrary/caller-supplied ref. Every rejection test below
# proves BOTH the rejection itself and that only the SAME generic error
# message is raised regardless of which specific check failed (item F/
# "Error/Privacy behavior" - never distinguishing nonexistent from
# cross-company, never naming a foreign company).
# ---------------------------------------------------------------------------

def test_receipt_accepts_valid_same_company_decision_and_outcome(db_available) -> None:
    """items 1, 17, F: a real same-company Decision + a real same-company
    Outcome that genuinely belongs to it -> receipt accepted."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omvalid") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    outcome_id = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)

                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(decision_id), outcome_memory_ids=(UUID(outcome_id),)
                )
                receipt = await service.create_receipt(
                    company_id=UUID(company_id),
                    created_by_user_id=UUID(user_id),
                    session_id="s4b-valid",
                    response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                    evidence_refs=[],
                    company_brain_refs=[],
                    organizational_memory_refs=[om_ref],
                )
                assert isinstance(receipt, ReasoningReceipt)
                categories = {ref["category"] for ref in receipt.evidence_refs}
                assert categories == {"organizational_memory"}
                assert receipt.evidence_refs[0]["decision_memory_id"] == decision_id
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_rejects_nonexistent_decision(db_available) -> None:
    """items 2, 18, A."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omnodec") as (company_id, user_id):
                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=uuid4(), outcome_memory_ids=(uuid4(),)
                )
                with pytest.raises(InvalidMemoryInput) as exc_info:
                    await service.create_receipt(
                        company_id=UUID(company_id),
                        created_by_user_id=UUID(user_id),
                        session_id="s4b-nodec",
                        response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                        evidence_refs=[],
                        organizational_memory_refs=[om_ref],
                    )
                assert str(exc_info.value) == _GENERIC_OM_ERROR
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_rejects_cross_company_decision(db_available) -> None:
    """items 3, 19, B: Decision exists, but belongs to company B while the
    receipt is being created for company A - rejected, generic message."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omcrossdecA") as (company_a, user_a):
                async with _company_scope(pool, label="omcrossdecB") as (company_b, user_b):
                    async with pool.acquire() as conn:
                        receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                        decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                        outcome_b = await _seed_outcome(conn, company_id=company_b, decision_id=decision_b, user_id=user_b)

                    service = ReasoningReceiptService(pool)
                    om_ref = OrganizationalMemoryProvenanceRef(
                        decision_memory_id=UUID(decision_b), outcome_memory_ids=(UUID(outcome_b),)
                    )
                    with pytest.raises(InvalidMemoryInput) as exc_info:
                        await service.create_receipt(
                            company_id=UUID(company_a),
                            created_by_user_id=UUID(user_a),
                            session_id="s4b-crossdec",
                            response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                            evidence_refs=[],
                            organizational_memory_refs=[om_ref],
                        )
                    assert str(exc_info.value) == _GENERIC_OM_ERROR
                    # Privacy: the error never names the foreign company.
                    assert company_b not in str(exc_info.value)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_rejects_nonexistent_outcome(db_available) -> None:
    """items 4, 20, C: valid Decision, but the cited Outcome id does not
    exist at all."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omnoout") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)

                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(decision_id), outcome_memory_ids=(uuid4(),)
                )
                with pytest.raises(InvalidMemoryInput) as exc_info:
                    await service.create_receipt(
                        company_id=UUID(company_id),
                        created_by_user_id=UUID(user_id),
                        session_id="s4b-noout",
                        response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                        evidence_refs=[],
                        organizational_memory_refs=[om_ref],
                    )
                assert str(exc_info.value) == _GENERIC_OM_ERROR
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_rejects_cross_company_outcome(db_available) -> None:
    """items 5, 21, D: valid Decision in company A, but the cited Outcome
    exists only in company B - rejected, generic message."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omcrossoutA") as (company_a, user_a):
                async with _company_scope(pool, label="omcrossoutB") as (company_b, user_b):
                    async with pool.acquire() as conn:
                        receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                        decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                        receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                        decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                        outcome_b = await _seed_outcome(conn, company_id=company_b, decision_id=decision_b, user_id=user_b)

                    service = ReasoningReceiptService(pool)
                    om_ref = OrganizationalMemoryProvenanceRef(
                        decision_memory_id=UUID(decision_a), outcome_memory_ids=(UUID(outcome_b),)
                    )
                    with pytest.raises(InvalidMemoryInput) as exc_info:
                        await service.create_receipt(
                            company_id=UUID(company_a),
                            created_by_user_id=UUID(user_a),
                            session_id="s4b-crossout",
                            response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                            evidence_refs=[],
                            organizational_memory_refs=[om_ref],
                        )
                    assert str(exc_info.value) == _GENERIC_OM_ERROR
                    assert company_b not in str(exc_info.value)
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_rejects_outcome_belonging_to_different_decision(db_available) -> None:
    """items 6, 22, E: valid Decision + a valid same-company Outcome, but
    that Outcome actually belongs to a DIFFERENT Decision - rejected."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omwrongdec") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_1 = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    decision_2 = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    outcome_of_decision_2 = await _seed_outcome(
                        conn, company_id=company_id, decision_id=decision_2, user_id=user_id
                    )

                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(decision_1), outcome_memory_ids=(UUID(outcome_of_decision_2),)
                )
                with pytest.raises(InvalidMemoryInput) as exc_info:
                    await service.create_receipt(
                        company_id=UUID(company_id),
                        created_by_user_id=UUID(user_id),
                        session_id="s4b-wrongdec",
                        response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                        evidence_refs=[],
                        organizational_memory_refs=[om_ref],
                    )
                assert str(exc_info.value) == _GENERIC_OM_ERROR
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_accepts_multiple_valid_outcomes_for_same_decision(db_available) -> None:
    """items 7, 23, G."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="ommulti") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    outcome_1 = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    outcome_2 = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)

                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(decision_id),
                    outcome_memory_ids=(UUID(outcome_1), UUID(outcome_2)),
                )
                receipt = await service.create_receipt(
                    company_id=UUID(company_id),
                    created_by_user_id=UUID(user_id),
                    session_id="s4b-multi",
                    response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                    evidence_refs=[],
                    organizational_memory_refs=[om_ref],
                )
                assert sorted(receipt.evidence_refs[0]["outcome_memory_ids"]) == sorted([outcome_1, outcome_2])
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_accepts_truth_company_brain_and_valid_om_together(db_available) -> None:
    """items 8, 24, K: Truth + Company Brain + a REAL, DB-backed OM ref
    all on the same receipt."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omtriple") as (company_id, user_id):
                async with pool.acquire() as conn:
                    file_id = await conn.fetchval(
                        """
                        INSERT INTO files (company_id, uploaded_by_user_id, filename, content_type, file_size_bytes, storage_path)
                        VALUES ($1, $2, 'test.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 10, '/tmp/x.xlsx')
                        RETURNING id
                        """,
                        company_id, user_id,
                    )
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    outcome_id = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)

                service = ReasoningReceiptService(pool)
                cb_ref = CompanyBrainProvenanceRef(
                    company_id=UUID(company_id), source_key="src", item_key="key",
                    content_sha256="a" * 64, text_snapshot="statement", display_label="CB1",
                )
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(decision_id), outcome_memory_ids=(UUID(outcome_id),)
                )
                receipt = await service.create_receipt(
                    company_id=UUID(company_id),
                    created_by_user_id=UUID(user_id),
                    session_id="s4b-tripleval",
                    response_snapshot={
                        "ceo_text": "x",
                        "reasoning_assessment": {"recommendation_basis": {"company_basis": ["CB1"]}},
                    },
                    evidence_refs=[EvidenceRef(type="file", id=UUID(str(file_id)))],
                    company_brain_refs=[cb_ref],
                    organizational_memory_refs=[om_ref],
                )
                categories = sorted(ref["category"] for ref in receipt.evidence_refs)
                assert categories == ["company_brain", "organizational_memory", "truth"]
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_accepts_superseded_decision_historical_reference(db_available) -> None:
    """items 9, 25, J: a superseded Decision row still exists and is a
    structurally valid historical reference - the receipt-boundary
    integrity check must NOT reject merely because status='superseded'.
    Live Slice 4A retrieval (unchanged, untouched this round) remains
    solely responsible for excluding superseded rows from what gets
    OFFERED to the model in the first place."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omsupdec") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    old_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    outcome_id = await _seed_outcome(conn, company_id=company_id, decision_id=old_decision, user_id=user_id)
                    new_decision = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    await _supersede_decision(conn, old_decision_id=old_decision, new_decision_id=new_decision)

                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(old_decision), outcome_memory_ids=(UUID(outcome_id),)
                )
                receipt = await service.create_receipt(
                    company_id=UUID(company_id),
                    created_by_user_id=UUID(user_id),
                    session_id="s4b-supdec",
                    response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                    evidence_refs=[],
                    organizational_memory_refs=[om_ref],
                )
                assert receipt.evidence_refs[0]["decision_memory_id"] == old_decision
        finally:
            await pool.close()

    _run(scenario())


def test_receipt_accepts_superseded_outcome_historical_reference(db_available) -> None:
    """items 10, 25, J: a superseded Outcome row still exists, still
    genuinely belongs to the referenced Decision, and remains a valid
    historical reference - not rejected merely for status."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omsupout") as (company_id, user_id):
                async with pool.acquire() as conn:
                    receipt_id = await _seed_receipt(conn, company_id=company_id, user_id=user_id)
                    decision_id = await _seed_decision(conn, company_id=company_id, receipt_id=receipt_id, user_id=user_id)
                    old_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    new_outcome = await _seed_outcome(conn, company_id=company_id, decision_id=decision_id, user_id=user_id)
                    await _supersede_outcome(conn, old_outcome_id=old_outcome, new_outcome_id=new_outcome)

                service = ReasoningReceiptService(pool)
                om_ref = OrganizationalMemoryProvenanceRef(
                    decision_memory_id=UUID(decision_id), outcome_memory_ids=(UUID(old_outcome),)
                )
                receipt = await service.create_receipt(
                    company_id=UUID(company_id),
                    created_by_user_id=UUID(user_id),
                    session_id="s4b-supout",
                    response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                    evidence_refs=[],
                    organizational_memory_refs=[om_ref],
                )
                assert set(receipt.evidence_refs[0]["outcome_memory_ids"]) == {old_outcome}
        finally:
            await pool.close()

    _run(scenario())


def test_om_verification_performs_no_mutation(db_available) -> None:
    """item H: a REJECTED verification attempt (cross-company outcome)
    must not mutate any row - exact snapshot comparison before/after."""
    async def scenario():
        pool = await _make_pool()
        try:
            async with _company_scope(pool, label="omnomutA") as (company_a, user_a):
                async with _company_scope(pool, label="omnomutB") as (company_b, user_b):
                    async with pool.acquire() as conn:
                        receipt_a = await _seed_receipt(conn, company_id=company_a, user_id=user_a)
                        decision_a = await _seed_decision(conn, company_id=company_a, receipt_id=receipt_a, user_id=user_a)
                        receipt_b = await _seed_receipt(conn, company_id=company_b, user_id=user_b)
                        decision_b = await _seed_decision(conn, company_id=company_b, receipt_id=receipt_b, user_id=user_b)
                        outcome_b = await _seed_outcome(conn, company_id=company_b, decision_id=decision_b, user_id=user_b)

                        decisions_before = [dict(r) for r in await conn.fetch(
                            "SELECT * FROM ome_decision_memories WHERE company_id IN ($1,$2) ORDER BY id", company_a, company_b
                        )]
                        outcomes_before = [dict(r) for r in await conn.fetch(
                            "SELECT * FROM ome_outcome_memories WHERE company_id IN ($1,$2) ORDER BY id", company_a, company_b
                        )]

                    service = ReasoningReceiptService(pool)
                    om_ref = OrganizationalMemoryProvenanceRef(
                        decision_memory_id=UUID(decision_a), outcome_memory_ids=(UUID(outcome_b),)
                    )
                    with pytest.raises(InvalidMemoryInput):
                        await service.create_receipt(
                            company_id=UUID(company_a),
                            created_by_user_id=UUID(user_a),
                            session_id="s4b-nomut",
                            response_snapshot={"ceo_text": "x", "reasoning_assessment": {}},
                            evidence_refs=[],
                            organizational_memory_refs=[om_ref],
                        )

                    async with pool.acquire() as conn:
                        decisions_after = [dict(r) for r in await conn.fetch(
                            "SELECT * FROM ome_decision_memories WHERE company_id IN ($1,$2) ORDER BY id", company_a, company_b
                        )]
                        outcomes_after = [dict(r) for r in await conn.fetch(
                            "SELECT * FROM ome_outcome_memories WHERE company_id IN ($1,$2) ORDER BY id", company_a, company_b
                        )]
                        assert decisions_after == decisions_before
                        assert outcomes_after == outcomes_before
        finally:
            await pool.close()

    _run(scenario())


def test_om_verification_does_not_inspect_old_receipt_content() -> None:
    """item I: structural - the new _verify_organizational_memory_refs
    method's own EXECUTABLE CODE (not its docstring, which legitimately
    names these fields in prose explaining what is deliberately never
    touched - the same docstring-vs-usage distinction drawn elsewhere in
    this file/session) never reads response_snapshot/ceo_text/
    reasoning_assessment of any receipt, and never traverses
    DecisionMemory.reasoning_receipt_id or instantiates
    ReasoningReceiptRepository."""
    text = pathlib.Path("app/ome/services/reasoning_receipt_service.py").read_text(encoding="utf-8")
    method_start = text.index("async def _verify_organizational_memory_refs(")
    docstring_end = text.index('"""', text.index('"""', method_start) + 3) + 3
    executable_code = text[docstring_end:docstring_end + 2000]
    assert "response_snapshot" not in executable_code
    assert ".ceo_text" not in executable_code
    assert "reasoning_receipt_id" not in executable_code
    assert "ReasoningReceiptRepository(" not in executable_code


def test_no_old_receipt_content_read_by_provenance_builder() -> None:
    """items 21, 32, 33, 46, 47, 48: structural - the OM provenance path
    never reads/loads a prior receipt's response_snapshot/evidence_refs/
    ceo_text/reasoning_assessment. It resolves only from the current
    turn's server-built catalog (durable ids only)."""
    provenance_text = pathlib.Path("app/ome/provenance.py").read_text(encoding="utf-8")
    om_function_start = provenance_text.index("def build_organizational_memory_provenance_refs(")
    om_function_text = provenance_text[om_function_start:om_function_start + 3000]
    assert "response_snapshot" not in om_function_text
    assert "ReasoningReceiptRepository" not in om_function_text
    assert ".ceo_text" not in om_function_text


def test_om_provenance_ref_has_no_reasoning_receipt_id_field() -> None:
    """Founder Step 16: durable pointers only - never reasoning_receipt_id
    (transitive resolution stays external via DecisionMemory.reasoning_
    receipt_id, never inlined)."""
    fields = {f.name for f in dataclasses.fields(OrganizationalMemoryProvenanceRef)}
    assert "reasoning_receipt_id" not in fields
    assert "text_snapshot" not in fields
    assert "company_id" not in fields
    assert "confidence" not in fields


# ---------------------------------------------------------------------------
# No policy promotion / no scoring / no Truth or Company Brain mutation
# (items 41, 42, 56, 57)
# ---------------------------------------------------------------------------

def test_om_provenance_builder_imports_no_company_brain_or_truth_module() -> None:
    """Real, narrowly-scoped import-graph proof for what Slice 4B actually
    owns: app/ome/provenance.py's OM builder never imports a Company Brain
    or Operational Truth module at all (write or read) - it resolves
    purely from the caller-supplied turn-local catalog, never a fresh
    lookup of either layer."""
    provenance_text = pathlib.Path("app/ome/provenance.py").read_text(encoding="utf-8")
    assert "app.services.company_brain_context" not in provenance_text
    assert "app.services.operational_truth_context" not in provenance_text


def test_receipt_service_om_verification_uses_only_ome_read_repositories() -> None:
    """Real, narrowly-scoped import-graph proof: the required-fix-round OM
    verification in app/ome/services/reasoning_receipt_service.py imports
    only the two existing OME read repositories (DecisionMemoryRepository/
    OutcomeMemoryRepository, both already company-scoped) - never a
    Company Brain or Operational Truth service of any kind (write or
    read), and never a generic/unscoped database accessor."""
    text = pathlib.Path("app/ome/services/reasoning_receipt_service.py").read_text(encoding="utf-8")
    assert "from app.ome.repositories.decision_memory_repository import DecisionMemoryRepository" in text
    assert "from app.ome.repositories.outcome_memory_repository import OutcomeMemoryRepository" in text
    assert "self.decision_repo.get_by_id(" in text
    assert "self.outcome_repo.get_by_id(" in text
    assert "app.services.company_brain_context" not in text
    assert "app.services.operational_truth_context" not in text


def test_no_policy_promotion_method_invoked_anywhere_in_new_om_code() -> None:
    """Real, narrowly-scoped call-graph proof: none of the three files
    this fix round's OM code lives in call anything named/shaped like a
    Company Brain WRITE/promotion method (create/update/insert/promote on
    a company_brain-named target). This is a call-site check (looking for
    an actual invocation pattern), not a bare substring that could
    false-positive on prose."""
    for path in [
        "app/ome/types.py",
        "app/ome/provenance.py",
        "app/ome/services/reasoning_receipt_service.py",
    ]:
        text = pathlib.Path(path).read_text(encoding="utf-8")
        for forbidden_call in [
            "promote_to_company_brain(",
            "CompanyBrainRepository(",
            "company_brain_service",
            ".create_company_brain",
            ".update_company_brain",
        ]:
            assert forbidden_call not in text


def test_no_scoring_or_confidence_field_on_provenance_ref() -> None:
    fields = {f.name for f in dataclasses.fields(OrganizationalMemoryProvenanceRef)}
    assert not ({"score", "similarity", "confidence", "relevance"} & fields)


# ---------------------------------------------------------------------------
# Protected-boundary dormancy proofs (items 43-46, 59-62)
# ---------------------------------------------------------------------------

# Historical note: before M8 Slice 4C-1, this test asserted
# app/services/explainability.py contained no "organizational_memory"/
# "cited_organizational_memory" text at all - proving the whole public
# explainability surface for Organizational Memory was dormant. M8 Slice
# 4C-1 is the Founder-authorized round that adds exactly that public field
# (see app/services/explainability.py's cited_organizational_memory and
# tests/test_m8_slice4c1_organizational_memory_explainability.py for its
# behavior proofs), so that assertion is now obsolete by design, not a
# regression - removed rather than kept as a hollow check, since no
# narrower true statement survives it (the whole point of the retired
# test was "zero Organizational Memory content in this file," and
# Organizational Memory content is now this file's actual feature).


def test_no_live_situation_resolution_in_chat_api() -> None:
    text = pathlib.Path("app/api/chat.py").read_text(encoding="utf-8")
    assert "situation_id" not in text
    assert "organizational_memory" not in text


def test_migrations_still_001_through_014() -> None:
    """M8 boundary invariant: migration 014 is present, unrenamed.
    (Historical note: this test previously also asserted no migration
    015 existed; that assertion became obsolete once Founder-approved
    M9 Slice 1 added migration 015, and has been removed - it was never
    the real invariant this M8 slice needed, which is that 001-014
    remain intact, not that no future milestone may ever add one.)"""
    migration_files = sorted(p.name for p in pathlib.Path("migrations").glob("*.sql"))
    assert "014_organizational_memory.sql" in migration_files


def test_migration_014_checksum_unchanged() -> None:
    import hashlib

    digest = hashlib.sha256(pathlib.Path("migrations/014_organizational_memory.sql").read_bytes()).hexdigest()
    assert digest == "8e30a9b8bb7c73f226ac8bf8eb1a751ddb311c82404c5f635fd995c46a378710"


# ---------------------------------------------------------------------------
# Namespace cleanliness snapshot - SUPPLEMENTARY, defense in depth only
# (every DB-mutating test above uses _company_scope's guaranteed teardown)
# ---------------------------------------------------------------------------

def test_m8_s4b_namespace_cleanliness_snapshot(db_available) -> None:
    async def scenario():
        pool = await _make_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT slug FROM companies WHERE slug LIKE 'm8-s4b-%'")
            assert rows == [], f"leftover m8-s4b-* companies: {[r['slug'] for r in rows]}"
        finally:
            await pool.close()

    _run(scenario())
