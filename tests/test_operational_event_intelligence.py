"""M2 -- Operational Events -> Intelligence bridge.

Integration tests against the local dev Postgres instance (DATABASE_URL),
since this surface spans two real repositories (OperationalEventRepository,
MemoryRepository) and a real merge inside AIService.chat() -- a fake pool
cannot exercise the real FK-constrained schema, department scoping, or prove
tenant isolation across two real tables.

Design notes carried through these tests (Codex peer review round 1):

- The bridge is a read-path merge only. operational_events remains the
  single source of truth for timeline events; nothing is written back to
  memory_events.
- Department scoping reuses the same RBAC-verified context["aimx_department"]
  the RAG retrieval path already relies on -- never inferred from text.
- Failure handling distinguishes expected non-availability (no db_pool) from
  unexpected failure (a real pool that still fails), surfaced via
  context["operational_events_bridge"]["status"] so it is testable rather
  than silently degrading.
- Deduplication is deterministic-only (explicit operational_event_id
  linkage). No fuzzy/text-similarity matching is implemented -- see
  _dedupe_linked_operational_events' docstring and the M2 report for why.
"""
import asyncio
from types import SimpleNamespace
from uuid import UUID, uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.repositories.operational_event_repository import (
    OperationalEventRepository,
    to_intelligence_event,
)
from app.services.memory.repository import MemoryRepository
from app.services.openai_client import (
    AIService,
    _dedupe_linked_operational_events,
    _event_recency_key,
    _resolve_scoped_department_id,
)


def _run(coro):
    return asyncio.run(coro)


async def _make_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=5)


async def _seed_company_and_user(pool: asyncpg.Pool) -> tuple[str, str]:
    """Create the minimal real company + user rows operational_events'
    foreign keys require. Returns (company_id, user_id) as strings."""
    async with pool.acquire() as conn:
        company_row = await conn.fetchrow(
            "INSERT INTO companies (slug, name) VALUES ($1, $2) RETURNING id",
            f"test-co-{uuid4().hex[:10]}",
            "Test Company",
        )
        user_row = await conn.fetchrow(
            "INSERT INTO users (email, full_name) VALUES ($1, $2) RETURNING id",
            f"test-{uuid4().hex[:10]}@example.com",
            "Test User",
        )
    return str(company_row["id"]), str(user_row["id"])


async def _seed_department(pool: asyncpg.Pool, company_id: str, name: str) -> str:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO departments (company_id, name, slug) VALUES ($1, $2, $3) RETURNING id",
            UUID(company_id),
            name,
            f"{name.lower()}-{uuid4().hex[:6]}",
        )
    return str(row["id"])


async def _cleanup(pool: asyncpg.Pool, *, company_ids: list[str], user_ids: list[str]) -> None:
    async with pool.acquire() as conn:
        for company_id in company_ids:
            await conn.execute("DELETE FROM operational_events WHERE company_id=$1", company_id)
            await conn.execute("DELETE FROM public.memory_events WHERE company_id=$1", company_id)
            await conn.execute("DELETE FROM departments WHERE company_id=$1", company_id)
            await conn.execute("DELETE FROM companies WHERE id=$1", company_id)
        for user_id in user_ids:
            await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    await pool.close()


async def _create_operational_event(
    pool: asyncpg.Pool,
    *,
    company_id: str,
    user_id: str,
    department_id: str | None = None,
    event_type: str = "operational.production.issue",
    category: str = "issue",
    priority: str = "high",
    title: str = "Feed shortage reported",
    summary: str = "Hall 3 reported feed shortage affecting morning distribution.",
) -> dict:
    repo = OperationalEventRepository(pool)
    return await repo.create_event(
        company_id=UUID(company_id),
        created_by_user_id=UUID(user_id),
        department_id=UUID(department_id) if department_id else None,
        event_type=event_type,
        category=category,
        priority=priority,
        title=title,
        summary=summary,
        source_type="manual",
        payload={"quantity": "3 bags"},
    )


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


VALID_AI_JSON = """
{
  "executive_summary": "Executive Summary\\n- Feed shortage is creating fulfillment risk.\\n\\nRecommended Actions\\n- Operations: confirm feed resupply within 24 hours.\\n\\nPriority Level\\n- High.",
  "raw_decision": {
    "truth_validation": {
      "contradictions": []
    },
    "reasoning_assessment": {
      "reasoning_state": "insufficient_evidence",
      "operational_assessment": "n/a",
      "company_brain_alignment": "cannot determine",
      "tensions": [],
      "evidence_gaps": [],
      "risk_assessment": "n/a",
      "confidence": 50,
      "recommendation_basis": {"evidence_basis": [], "company_basis": [], "missing_evidence": []}
    }
  }
}
"""


class _FakeChatCompletions:
    def __init__(self):
        self.messages = []

    async def create(self, **kwargs):
        self.messages.append(kwargs["messages"])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=VALID_AI_JSON))]
        )


class _FakeOpenAIClient:
    def __init__(self):
        self.chat_completions = _FakeChatCompletions()
        self.chat = SimpleNamespace(completions=self.chat_completions)


class _MinimalFakeRepo:
    """Satisfies AIService.chat()'s self.repo contract without a real DB --
    used only to prove the "no db_pool" (expected non-availability) path."""

    async def fetch_recent_events(self, **kwargs):
        return []

    async def fetch_facts(self, **kwargs):
        return []

    async def build_company_profile(self, **kwargs):
        return {}


def _service_with_real_db(pool: asyncpg.Pool) -> tuple[AIService, _FakeOpenAIClient]:
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = True
    service.db_pool = pool
    service.repo = MemoryRepository(pool)
    return service, fake_client


# ---------------------------------------------------------------------------
# Provenance completeness (Finding 2)
# ---------------------------------------------------------------------------

def test_to_intelligence_event_preserves_full_provenance_without_fabricating_confidence():
    event_id = uuid4()
    company_id = uuid4()
    department_id = uuid4()
    row = {
        "id": event_id,
        "company_id": company_id,
        "department_id": department_id,
        "event_type": "operational.production.issue",
        "category": "issue",
        "priority": "high",
        "title": "Feed shortage reported",
        "summary": "Hall 3 reported feed shortage affecting morning distribution.",
        "event_timestamp": "2026-06-01T08:00:00+00:00",
        "source_type": "manual",
        "source_ref": "form-123",
        "payload": {"quantity": "3 bags"},
    }

    mapped = to_intelligence_event(row)
    ctx = mapped["context"]

    # Compatibility-shaped top-level fields (unchanged from round 1).
    assert mapped["event_type"] == "operational.production.issue"
    assert mapped["user_message"] == "Feed shortage reported"
    assert mapped["executive_summary"] == "Hall 3 reported feed shortage affecting morning distribution."
    assert mapped["created_at"] == "2026-06-01T08:00:00+00:00"

    # Explicit, unaliased provenance fields (Finding 2).
    assert ctx["operational_event_id"] == str(event_id)
    assert ctx["company_id"] == str(company_id)
    assert ctx["department_id"] == str(department_id)
    assert ctx["event_type"] == "operational.production.issue"
    assert ctx["category"] == "issue"
    assert ctx["priority"] == "high"
    assert ctx["source_type"] == "manual"
    assert ctx["source_ref"] == "form-123"
    assert ctx["event_timestamp"] == "2026-06-01T08:00:00+00:00"
    assert ctx["title"] == "Feed shortage reported"
    assert ctx["summary"] == "Hall 3 reported feed shortage affecting morning distribution."
    assert ctx["payload"] == {"quantity": "3 bags"}
    assert ctx["source"] == "operational_events"

    # Not available on the source row -- must not be invented.
    assert "confidence" not in mapped
    assert "confidence" not in ctx


def test_to_intelligence_event_handles_missing_department_and_ref():
    row = {
        "id": uuid4(),
        "company_id": uuid4(),
        "department_id": None,
        "event_type": "operational.manual",
        "category": "daily_update",
        "priority": "normal",
        "title": "",
        "summary": "General update",
        "event_timestamp": "2026-06-01T08:00:00+00:00",
        "source_type": "manual",
        "source_ref": None,
        "payload": {},
    }

    mapped = to_intelligence_event(row)

    assert mapped["context"]["department_id"] is None
    assert mapped["context"]["source_ref"] is None


# ---------------------------------------------------------------------------
# Department scoping (Finding 1)
# ---------------------------------------------------------------------------

def test_resolve_scoped_department_id_reads_only_the_rbac_verified_context_field():
    dept_id = uuid4()
    assert _resolve_scoped_department_id({"aimx_department": {"id": str(dept_id)}}) == dept_id
    assert _resolve_scoped_department_id({}) is None
    assert _resolve_scoped_department_id({"aimx_department": "not-a-dict"}) is None
    assert _resolve_scoped_department_id({"aimx_department": {"id": "not-a-uuid"}}) is None


def test_ceo_context_sees_company_wide_operational_events(db_available, monkeypatch):
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        dept_a = await _seed_department(pool, company_id, "Production")
        dept_b = await _seed_department(pool, company_id, "Sales")
        try:
            await _create_operational_event(
                pool, company_id=company_id, user_id=user_id, department_id=dept_a,
                summary="Production hall reported a feed shortage.",
            )
            await _create_operational_event(
                pool, company_id=company_id, user_id=user_id, department_id=dept_b,
                summary="Sales team reported a delivery delay.",
            )

            service, _fake_client = _service_with_real_db(pool)
            result = await service.chat(
                session_id="m2-ceo-session",
                message="What happened today?",
                context={"response_language": "en"},  # no aimx_department -> CEO/company-wide
                company_id=company_id,
            )
            return result
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    result = _run(scenario())

    bridge = result["meta"]["context"]["operational_events_bridge"]
    assert bridge["status"] == "ok"
    assert bridge["fetched"] == 2
    summaries = [item["summary"] for item in result["meta"]["context"]["decision_context"]["operational_events"]]
    assert any("feed shortage" in s.lower() for s in summaries)
    assert any("delivery delay" in s.lower() for s in summaries)


def test_department_scoped_context_excludes_other_departments_events(db_available, monkeypatch):
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        dept_a = await _seed_department(pool, company_id, "Production")
        dept_b = await _seed_department(pool, company_id, "Sales")
        try:
            await _create_operational_event(
                pool, company_id=company_id, user_id=user_id, department_id=dept_a,
                summary="Production hall reported a feed shortage.",
            )
            await _create_operational_event(
                pool, company_id=company_id, user_id=user_id, department_id=dept_b,
                summary="Sales team reported a delivery delay.",
            )

            service, _fake_client = _service_with_real_db(pool)
            result = await service.chat(
                session_id="m2-dept-session",
                message="What happened today?",
                context={"response_language": "en", "aimx_department": {"id": dept_a}},
                company_id=company_id,
            )
            return result
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    result = _run(scenario())

    bridge = result["meta"]["context"]["operational_events_bridge"]
    assert bridge["status"] == "ok"
    assert bridge["fetched"] == 1
    summaries = [item["summary"] for item in result["meta"]["context"]["decision_context"]["operational_events"]]
    assert any("feed shortage" in s.lower() for s in summaries)
    assert not any("delivery delay" in s.lower() for s in summaries)


def test_operational_events_do_not_cross_company_boundary(db_available):
    async def scenario():
        pool = await _make_pool()
        company_a, user_a = await _seed_company_and_user(pool)
        company_b, user_b = await _seed_company_and_user(pool)
        try:
            await _create_operational_event(pool, company_id=company_a, user_id=user_a)

            event_repo = OperationalEventRepository(pool)
            company_b_rows = await event_repo.list_events(company_id=UUID(company_b), limit=10)
            company_a_rows = await event_repo.list_events(company_id=UUID(company_a), limit=10)

            return company_a_rows, company_b_rows
        finally:
            await _cleanup(pool, company_ids=[company_a, company_b], user_ids=[user_a, user_b])

    company_a_rows, company_b_rows = _run(scenario())

    assert len(company_a_rows) == 1
    assert company_b_rows == []


# ---------------------------------------------------------------------------
# Failure behavior (Finding 3)
# ---------------------------------------------------------------------------

def test_operational_events_bridge_reports_not_configured_when_db_pool_missing():
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.db_enabled = True
    service.db_pool = None
    service.repo = _MinimalFakeRepo()

    result = _run(
        service.chat(
            session_id="m2-no-pool-session",
            message="Anything to report?",
            context={"response_language": "en"},
            company_id=str(uuid4()),
        )
    )

    assert result["meta"]["context"]["operational_events_bridge"] == {"status": "not_configured"}


def test_operational_events_bridge_reports_error_status_on_unexpected_failure(db_available, caplog):
    async def scenario():
        pool = await _make_pool()
        try:
            service, _fake_client = _service_with_real_db(pool)
            with caplog.at_level("ERROR"):
                result = await service.chat(
                    session_id="m2-error-session",
                    message="Anything to report?",
                    context={"response_language": "en"},
                    company_id="not-a-valid-uuid",
                )
            return result, caplog.text
        finally:
            await pool.close()

    result, log_text = _run(scenario())

    assert result["meta"]["context"]["operational_events_bridge"]["status"] == "error"
    assert "Operational event bridge failed unexpectedly" in log_text
    # The rest of the chat flow must not be dragged down with it.
    assert result["ceo_text"]


# ---------------------------------------------------------------------------
# Deduplication (Finding 4)
# ---------------------------------------------------------------------------

def test_dedupe_collapses_only_an_explicit_id_linked_duplicate():
    existing = [{"context": {"operational_event_id": "abc-123"}}]
    incoming = [
        {"context": {"operational_event_id": "abc-123"}, "executive_summary": "duplicate"},
        {"context": {"operational_event_id": "xyz-999"}, "executive_summary": "genuinely new"},
    ]

    kept, skipped = _dedupe_linked_operational_events(existing, incoming)

    assert skipped == 1
    assert len(kept) == 1
    assert kept[0]["context"]["operational_event_id"] == "xyz-999"


def test_dedupe_never_collapses_on_text_similarity_alone():
    """Two genuinely separate incidents with identical text must both survive
    -- there is no deterministic identity linking them, so the safe default
    is to keep both (prefer false negatives over unsafe false positives)."""
    existing = [{"context": {}, "executive_summary": "Feed shortage reported in hall 3"}]
    incoming = [
        {"context": {"operational_event_id": "different-id"}, "executive_summary": "Feed shortage reported in hall 3"},
    ]

    kept, skipped = _dedupe_linked_operational_events(existing, incoming)

    assert skipped == 0
    assert len(kept) == 1


def test_dedupe_with_no_linkage_anywhere_keeps_everything():
    existing = [{"context": {}, "executive_summary": "unrelated"}]
    incoming = [{"context": {"operational_event_id": "abc"}, "executive_summary": "new"}]

    kept, skipped = _dedupe_linked_operational_events(existing, incoming)

    assert skipped == 0
    assert kept == incoming


# ---------------------------------------------------------------------------
# Timestamp robustness (Finding 5)
# ---------------------------------------------------------------------------

def test_event_recency_key_handles_aware_naive_iso_and_invalid_values():
    from datetime import datetime, timezone

    aware = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)
    naive = datetime(2026, 6, 1, 8, 0)
    iso_string = "2026-06-01T08:00:00+00:00"

    assert _event_recency_key({"created_at": aware}) == aware
    assert _event_recency_key({"created_at": naive}) == naive.replace(tzinfo=timezone.utc)
    assert _event_recency_key({"created_at": iso_string}) == datetime.fromisoformat(iso_string)
    assert _event_recency_key({}) == datetime.min.replace(tzinfo=timezone.utc)
    assert _event_recency_key({"created_at": "not-a-timestamp"}) == datetime.min.replace(tzinfo=timezone.utc)
    assert _event_recency_key({"created_at": None}) == datetime.min.replace(tzinfo=timezone.utc)


def test_event_recency_key_sorts_mixed_datetime_and_string_sources_correctly():
    from datetime import datetime, timezone

    events = [
        {"created_at": "2026-06-01T08:00:00+00:00", "label": "older_string"},
        {"created_at": datetime(2026, 6, 2, 8, 0, tzinfo=timezone.utc), "label": "newer_datetime"},
    ]
    events.sort(key=_event_recency_key, reverse=True)

    assert [e["label"] for e in events] == ["newer_datetime", "older_string"]


# ---------------------------------------------------------------------------
# T1 / T4: real operational event becomes evidence; no events -> no fabrication
# ---------------------------------------------------------------------------

def test_real_operational_event_is_merged_with_memory_events(db_available):
    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            await _create_operational_event(pool, company_id=company_id, user_id=user_id)

            memory_repo = MemoryRepository(pool)
            event_repo = OperationalEventRepository(pool)

            memory_events = await memory_repo.fetch_recent_events(company_id=company_id, limit=10)
            operational_rows = await event_repo.list_events(company_id=UUID(company_id), limit=10)
            merged = memory_events + [to_intelligence_event(r) for r in operational_rows]

            return merged
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    merged = _run(scenario())

    assert len(merged) == 1
    assert merged[0]["context"]["source"] == "operational_events"
    assert merged[0]["executive_summary"] == "Hall 3 reported feed shortage affecting morning distribution."


def test_no_operational_events_leaves_memory_events_list_unchanged(db_available):
    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            memory_repo = MemoryRepository(pool)
            event_repo = OperationalEventRepository(pool)

            memory_events = await memory_repo.fetch_recent_events(company_id=company_id, limit=10)
            operational_rows = await event_repo.list_events(company_id=UUID(company_id), limit=10)

            assert operational_rows == []
            assert memory_events == []
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    _run(scenario())


# ---------------------------------------------------------------------------
# M7 Slice 1 Correction Round 1 (M7-03): reference/test seed operational
# events (scripts/seed_jannat_operational_events.py writes
# source_type="reference_seed") must never influence a live Golden
# reasoning response as if they were verified operational events. Filtered
# in AIService.chat() right after fetch (see REFERENCE_SEED_EVENT_SOURCE_TYPE
# in app/services/openai_client.py) - list_events() itself is untouched, so
# other callers (e.g. an admin auditing the raw operational-events list)
# still see seed rows unfiltered.
# ---------------------------------------------------------------------------


async def _create_reference_seed_event(
    pool: asyncpg.Pool,
    *,
    company_id: str,
    user_id: str,
    department_id: str | None = None,
    title: str = "Synthetic Reference Seed Event",
    summary: str = "Synthetic reference-seed placeholder event, never a real operational report.",
) -> dict:
    repo = OperationalEventRepository(pool)
    return await repo.create_event(
        company_id=UUID(company_id),
        created_by_user_id=UUID(user_id),
        department_id=UUID(department_id) if department_id else None,
        event_type="operational.reference_seed",
        category="issue",
        priority="normal",
        title=title,
        summary=summary,
        source_type="reference_seed",
        payload={},
    )


def test_s1_real_operational_event_remains_in_live_context(db_available, monkeypatch):
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            await _create_operational_event(
                pool, company_id=company_id, user_id=user_id,
                summary="Production hall reported a feed shortage.",
            )
            service, fake_client = _service_with_real_db(pool)
            result = await service.chat(
                session_id="m7-03-s1",
                message="What happened today?",
                context={"response_language": "en"},
                company_id=company_id,
            )
            return result, fake_client
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    result, fake_client = _run(scenario())

    bridge = result["meta"]["context"]["operational_events_bridge"]
    assert bridge["status"] == "ok"
    assert bridge["fetched"] == 1
    summaries = [item["summary"] for item in result["meta"]["context"]["decision_context"]["operational_events"]]
    assert any("feed shortage" in s.lower() for s in summaries)
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "feed shortage" in prompt_text.lower()


def test_s2_reference_seed_event_excluded_from_live_reasoning_context(db_available, monkeypatch):
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            await _create_reference_seed_event(
                pool, company_id=company_id, user_id=user_id,
                title="Reference Seed Only Event",
                summary="This reference-seed event must never reach live reasoning.",
            )
            service, fake_client = _service_with_real_db(pool)
            result = await service.chat(
                session_id="m7-03-s2",
                message="What happened today?",
                context={"response_language": "en"},
                company_id=company_id,
            )
            return result, fake_client
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    result, fake_client = _run(scenario())

    bridge = result["meta"]["context"]["operational_events_bridge"]
    assert bridge["status"] == "ok"
    assert bridge["fetched"] == 0
    assert result["meta"]["context"]["decision_context"]["operational_events"] == []
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "reference-seed event must never reach live reasoning" not in prompt_text.lower()


def test_s3_mixture_of_real_and_seed_events_only_real_reaches_live_context(db_available, monkeypatch):
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            await _create_operational_event(
                pool, company_id=company_id, user_id=user_id,
                summary="Production hall reported a feed shortage.",
            )
            await _create_reference_seed_event(
                pool, company_id=company_id, user_id=user_id,
                title="Reference Seed Only Event",
                summary="Synthetic seed summary that must not appear live.",
            )
            service, fake_client = _service_with_real_db(pool)
            result = await service.chat(
                session_id="m7-03-s3",
                message="What happened today?",
                context={"response_language": "en"},
                company_id=company_id,
            )
            return result, fake_client
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    result, fake_client = _run(scenario())

    bridge = result["meta"]["context"]["operational_events_bridge"]
    assert bridge["status"] == "ok"
    assert bridge["fetched"] == 1
    summaries = [item["summary"] for item in result["meta"]["context"]["decision_context"]["operational_events"]]
    assert any("feed shortage" in s.lower() for s in summaries)
    assert not any("synthetic seed summary" in s.lower() for s in summaries)
    prompt_text = "\n".join(m["content"] for m in fake_client.chat_completions.messages[0])
    assert "feed shortage" in prompt_text.lower()
    assert "synthetic seed summary" not in prompt_text.lower()


def test_s4_reference_seed_event_never_produces_a_truth_reference(db_available, monkeypatch):
    """Operational Truth Context (M4 T#) has zero code path reading
    operational_events at all (assemble_truth_context takes no DB handle -
    see test_seed_operational_events_isolation_truth_assembly_has_no_db_access
    in test_m7_slice1_upload_truth_bridge.py for the structural proof); this
    is the live-chat-level confirmation that a reference-seed event produces
    no reasoning_reference_catalog entry of any kind."""
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            await _create_reference_seed_event(pool, company_id=company_id, user_id=user_id)
            service, _fake_client = _service_with_real_db(pool)
            result = await service.chat(
                session_id="m7-03-s4",
                message="What happened today?",
                context={"response_language": "en"},
                company_id=company_id,
            )
            return result
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    result = _run(scenario())
    assert result["meta"]["context"]["decision_context"]["operational_events"] == []
    assert "reasoning_reference_catalog" not in result["meta"]["context"]["decision_context"]


def test_s5_reference_seed_event_absent_from_verified_event_prompt_text(db_available, monkeypatch):
    monkeypatch.setattr("app.services.openai_client._validate_execution_structure", lambda parsed: True)

    async def scenario():
        pool = await _make_pool()
        company_id, user_id = await _seed_company_and_user(pool)
        try:
            await _create_reference_seed_event(
                pool, company_id=company_id, user_id=user_id,
                title="Unmistakable Seed Marker Title",
                summary="Unmistakable seed marker summary text.",
            )
            service, fake_client = _service_with_real_db(pool)
            await service.chat(
                session_id="m7-03-s5",
                message="What happened today?",
                context={"response_language": "en"},
                company_id=company_id,
            )
            return fake_client
        finally:
            await _cleanup(pool, company_ids=[company_id], user_ids=[user_id])

    fake_client = _run(scenario())
    full_prompt_text = "\n".join(
        m["content"] for call_messages in [fake_client.chat_completions.messages[0]] for m in call_messages
    )
    assert "unmistakable seed marker" not in full_prompt_text.lower()
