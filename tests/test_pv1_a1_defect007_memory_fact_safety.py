"""PV1 Slice 3 - Batch A1 - DEFECT-007 memory_facts write/read safety.

Founder rule: CHAT TEXT != AUTHORITATIVE COMPANY TRUTH.

A1 establishes two properties for the live ``/ai/chat`` operational reasoning
path, and nothing else:

* WRITE SAFETY - no live chat turn automatically creates or updates durable
  ``memory_facts`` from user text, AI ``executive_summary``, AI
  ``raw_decision``, or any other generated chat content.
* READ SAFETY - legacy ``memory_facts`` do not materially influence live
  operational reasoning through any of the five verified read paths:
  P1 direct facts block, P2 Company Brain folding / INSTITUTIONAL_MEMORY /
  CB# references, P3 memory-derived COMPANY PROFILE block, P4 Decision
  Context memory trends, P5 Decision Context memory-profile fallback.

These tests deliberately supply contaminated facts that mirror the real rows
recorded in the PV1 Slice 3 pre-correction evidence checkpoint
(``d23c90e0bb6d4cb5fc453c3c998bb103597ca7c5``). The real rows are never
deleted or edited - they remain physically present as negative regression
fixtures; these in-memory mirrors let the same property be asserted without a
live database.

Assertions are provenance-specific: they target values that can only have
arrived through a ``memory_facts`` read path, so unrelated ``memory_events``
prose can never cause a false failure. ``memory_events`` is a different table
and is out of A1 scope.
"""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import app.services.openai_client as openai_client_module
from app.services.openai_client import AIService


VALID_AI_JSON = """
{
  "executive_summary": "Executive Summary\\n- Operational review complete for Production; inventory operational impact assessed as normal.\\n\\nRecommended Actions\\n- Monitor.\\n\\nPriority Level\\n- Medium.",
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
      "recommendation_basis": {"evidence_basis": [], "company_basis": [], "missing_evidence": [], "organizational_memory_basis": []}
    }
  }
}
"""

# A facts-bearing extractor response. Without this the fact extractor would
# return no facts against the fake client and the write test would pass
# vacuously, before any correction - i.e. a false green.
EXTRACTED_FACTS_JSON = """
{"facts":[{"fact_type":"metric","fact_key":"revenue","fact_value":"Extracted from AI prose - must never persist","confidence":80}]}
"""

CONFLICT_PROSE = (
    "Conflicting assertion 'conduct a thorough investigation into flock health' "
    "was received but not adopted on a confidence-threshold basis."
)

# Mirrors the real contaminated rows (session pv1-slice3-s4-halls and earlier
# frontend-ceo-session rows) observed in the Slice 3 evidence checkpoint.
CONTAMINATED_FACTS = [
    {
        "fact_type": "metric",
        "fact_key": "feed_consumption",
        "fact_value": "Hall 2 has specific metrics for feed consumption, while Hall 3 lacks this data.",
        "confidence": 80,
        "updated_at": None,
        "has_conflict": False,
        "residual_uncertainty": None,
    },
    {
        "fact_type": "metric",
        "fact_key": "water_consumption",
        "fact_value": "Hall 2 has specific metrics for water consumption, while Hall 3 lacks this data.",
        "confidence": 80,
        "updated_at": None,
        "has_conflict": False,
        "residual_uncertainty": None,
    },
    {
        "fact_type": "metric",
        "fact_key": "revenue",
        "fact_value": "فقدان الإيرادات بسبب عدم القدرة على تلبية الطلبات",
        "confidence": 15,
        "updated_at": None,
        "has_conflict": False,
        "residual_uncertainty": None,
    },
    {
        "fact_type": "process",
        "fact_key": "goal",
        "fact_value": "تعيين مالك مسؤول لتحديد نقاط الاختناق في الإنتاج خلال 24 ساعة",
        "confidence": 35,
        "updated_at": None,
        "has_conflict": True,
        "residual_uncertainty": CONFLICT_PROSE,
    },
    {
        "fact_type": "metric",
        "fact_key": "product_name",
        "fact_value": "الطيور",
        "confidence": 5,
        "updated_at": None,
        "has_conflict": False,
        "residual_uncertainty": None,
    },
]

# Mirrors MemoryRepository.build_company_profile()'s real return shape,
# including the `conflicts` dict that leaks memory_fact_history prose.
CONTAMINATED_MEMORY_PROFILE = {
    "product_name": "الطيور",
    "product_type": "إنتاج الطيور",
    "target_market": None,
    "primary_market": "قسم المبيعات",
    "expansion_markets": [],
    "stage": None,
    "goal": "تعيين مالك مسؤول لتحديد نقاط الاختناق في الإنتاج خلال 24 ساعة",
    "launch_timeline": "13/05/2026",
    "revenue": "فقدان الإيرادات بسبب عدم القدرة على تلبية الطلبات",
    "team_size": None,
    "conflicts": {"goal": {"residual_uncertainty": CONFLICT_PROSE}},
}

# P5 is currently inert only because build_company_profile()'s key namespace
# and _compact_company_profile()'s field list are disjoint. This fixture adds
# a deliberately OVERLAPPING key so the test proves the fallback is actually
# gated rather than merely coincidentally empty.
OVERLAPPING_MEMORY_PROFILE = dict(CONTAMINATED_MEMORY_PROFILE)
OVERLAPPING_MEMORY_PROFILE["current_operational_challenges"] = (
    "MEMORY-PROFILE-FALLBACK-MUST-NOT-REACH-DECISION-CONTEXT"
)
OVERLAPPING_MEMORY_PROFILE["growth_priorities"] = (
    "MEMORY-PROFILE-GROWTH-MUST-NOT-REACH-DECISION-CONTEXT"
)


class _RecordingRepo:
    """Records every memory access the live chat path performs."""

    def __init__(self, facts=None, profile=None):
        self._facts = facts if facts is not None else list(CONTAMINATED_FACTS)
        self._profile = profile if profile is not None else dict(CONTAMINATED_MEMORY_PROFILE)
        self.calls: list[str] = []
        self.upserted: list[dict] = []

    async def fetch_recent_events(self, **kwargs):
        self.calls.append("fetch_recent_events")
        return []

    async def fetch_facts(self, **kwargs):
        self.calls.append("fetch_facts")
        return [dict(fact) for fact in self._facts]

    async def build_company_profile(self, **kwargs):
        self.calls.append("build_company_profile")
        return dict(self._profile)

    async def insert_event(self, event=None, **kwargs):
        self.calls.append("insert_event")
        return {}

    async def upsert_fact(self, **kwargs):
        self.calls.append("upsert_fact")
        self.upserted.append(dict(kwargs))
        return {}


class _FakeChatCompletions:
    def __init__(self):
        self.messages: list[list[dict]] = []
        self.extractor_calls = 0

    async def create(self, **kwargs):
        messages = kwargs["messages"]
        joined = "\n".join(str(m.get("content") or "") for m in messages)
        if "institutional memory extraction engine" in joined:
            self.extractor_calls += 1
            content = EXTRACTED_FACTS_JSON
        else:
            self.messages.append(messages)
            content = VALID_AI_JSON
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class _FakeOpenAIClient:
    def __init__(self):
        self.chat_completions = _FakeChatCompletions()
        self.chat = SimpleNamespace(completions=self.chat_completions)


def _run_chat(monkeypatch, repo, message="Compare Hall 2 and Hall 3 on feed consumption."):
    """Drive one live AIService.chat turn and return (prompt_text, decision_context, repo, fake_client)."""
    service = AIService()
    fake_client = _FakeOpenAIClient()
    service.client = fake_client
    service.max_history = 1
    service.db_enabled = True
    service.db_pool = object()
    service.repo = repo

    captured: dict = {}
    real_build = openai_client_module.build_decision_context

    def capturing_build(**kwargs):
        decision_context = real_build(**kwargs)
        captured["decision_context"] = decision_context
        return decision_context

    async def fake_get_by_id(self, company_id):
        return {"id": str(company_id), "name": "Test Co", "slug": "test-co"}

    monkeypatch.setattr(
        "app.services.openai_client._validate_execution_structure", lambda parsed: True
    )
    monkeypatch.setattr(
        "app.services.openai_client.build_decision_context", capturing_build
    )
    monkeypatch.setattr(
        "app.repositories.company_repository.CompanyRepository.get_by_id", fake_get_by_id
    )

    asyncio.run(
        service.chat(
            session_id="pv1-a1-defect007",
            message=message,
            context={"response_language": "en"},
            company_id=str(uuid4()),
        )
    )

    prompt_text = "\n".join(
        str(m.get("content") or "") for m in fake_client.chat_completions.messages[0]
    )
    return prompt_text, captured.get("decision_context", {}), repo, fake_client


# ---------------------------------------------------------------- A. WRITE


def test_a1_live_chat_never_writes_memory_facts(monkeypatch):
    """A. WRITE SAFETY - no automatic durable memory_facts mutation."""
    repo = _RecordingRepo()
    _prompt, _dc, repo, fake_client = _run_chat(monkeypatch, repo)

    # The repository write path is never reached.
    assert "upsert_fact" not in repo.calls
    assert repo.upserted == []
    # The extractor itself is never invoked from the live chat path, so no
    # second model call is spent on it either.
    assert fake_client.chat_completions.extractor_calls == 0


# -------------------------------------------------------- B. DIRECT PROMPT


def test_a1_contaminated_facts_absent_from_operational_prompt(monkeypatch):
    """B. P1 - the direct INSTITUTIONAL FACTS block carries nothing."""
    repo = _RecordingRepo()
    prompt, _dc, _repo, _client = _run_chat(monkeypatch, repo)

    for fact in CONTAMINATED_FACTS:
        assert fact["fact_value"] not in prompt, f"leaked fact_value: {fact['fact_key']}"
    assert "INSTITUTIONAL FACTS (COMPANY TRUTHS):" not in prompt


# --------------------------------------------------------- C. COMPANY BRAIN


def test_a1_no_company_brain_item_or_cb_ref_from_memory_facts(monkeypatch):
    """C. P2 - no INSTITUTIONAL_MEMORY items, no memory-sourced CB# refs."""
    repo = _RecordingRepo()
    _prompt, decision_context, _repo, _client = _run_chat(monkeypatch, repo)

    brain_items = decision_context.get("company_brain_context") or []
    assert [i for i in brain_items if i.get("source") == "memory_facts"] == []
    assert [i for i in brain_items if i.get("type") == "INSTITUTIONAL_MEMORY"] == []

    catalog = (decision_context.get("reasoning_reference_catalog") or {}).get(
        "company_brain"
    ) or {}
    memory_refs = [
        ref
        for ref in catalog.values()
        if isinstance(ref, dict)
        and (
            ref.get("type") == "INSTITUTIONAL_MEMORY"
            or (ref.get("internal_source_item") or {}).get("source") == "memory_facts"
        )
    ]
    assert memory_refs == []


# -------------------------------------------------------- D. COMPANY PROFILE


def test_a1_no_memory_derived_company_profile_in_prompt(monkeypatch):
    """D. P3 - no memory-derived profile fields and no conflict-ledger prose."""
    repo = _RecordingRepo()
    prompt, _dc, _repo, _client = _run_chat(monkeypatch, repo)

    for key, value in CONTAMINATED_MEMORY_PROFILE.items():
        if isinstance(value, str) and value:
            assert value not in prompt, f"leaked memory profile field: {key}"
    # memory_fact_history residual-uncertainty prose must not reach the model.
    assert CONFLICT_PROSE not in prompt
    assert "residual_uncertainty" not in prompt


# ------------------------------------------------------- E. DECISION CONTEXT


def test_a1_no_memory_signal_trends_in_decision_context(monkeypatch):
    """E1. P4 - no 'Memory signal: ...' trend hints."""
    repo = _RecordingRepo()
    _prompt, decision_context, _repo, _client = _run_chat(monkeypatch, repo)

    trends = decision_context.get("trends") or []
    assert [t for t in trends if str(t).startswith("Memory signal:")] == []


def test_a1_memory_profile_fallback_is_gated_not_merely_inert(monkeypatch):
    """E2. P5 - proven gated using a deliberately overlapping-key profile."""
    repo = _RecordingRepo(profile=dict(OVERLAPPING_MEMORY_PROFILE))
    prompt, decision_context, _repo, _client = _run_chat(monkeypatch, repo)

    sentinels = (
        "MEMORY-PROFILE-FALLBACK-MUST-NOT-REACH-DECISION-CONTEXT",
        "MEMORY-PROFILE-GROWTH-MUST-NOT-REACH-DECISION-CONTEXT",
    )
    serialized = repr(decision_context)
    for sentinel in sentinels:
        assert sentinel not in serialized, "memory_profile fallback reached decision context"
        assert sentinel not in prompt, "memory_profile fallback reached the prompt"


# ------------------------------------------------- provenance discrimination


def test_a1_assertions_do_not_confuse_memory_events_with_memory_facts(monkeypatch):
    """memory_events is a different table and stays in scope for reasoning.

    Guards against a false-positive reading of the tests above: A1 must not
    be credited with removing prose that never came from memory_facts.
    """

    class _EventsRepo(_RecordingRepo):
        async def fetch_recent_events(self, **kwargs):
            self.calls.append("fetch_recent_events")
            return [
                {
                    "event_type": "operational.production.daily_update",
                    "user_message": "Chat operational input captured",
                    "executive_summary": "MEMORY-EVENT-PROSE-STAYS",
                    "created_at": None,
                }
            ]

    repo = _EventsRepo()
    prompt, _dc, _repo, _client = _run_chat(monkeypatch, repo)

    assert "MEMORY-EVENT-PROSE-STAYS" in prompt
