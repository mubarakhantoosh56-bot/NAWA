"""ENG-CONF-001 S4: required tests for conflict/resolution durability.

Integration tests against the local dev Postgres instance (DATABASE_URL),
since MemoryRepository issues real SQL (row locking, jsonb, composite FK)
that a fake pool cannot faithfully exercise. Each test uses a fresh
company_id and cleans up its own rows afterward.

Design note carried through these tests (Codex peer review finding #5):
memory_fact_history records conflict *events* only. Plain inserts and
same-value reinforcements are not conflicts and do not get a history row --
a general history of every update is adjacent finding AF-1 (Founder Decision
R4), which is explicitly excluded from ENG-CONF-001 scope. The prior/rejected
side of a conflict is preserved inside the conflict event's sources_weighed,
captured at the moment the conflict occurs, not via a separately maintained
non-conflict trail.
"""
import asyncio
from uuid import uuid4

import asyncpg
import pytest

from app.core.config import settings
from app.services.memory.repository import MemoryRepository


def _run(coro):
    return asyncio.run(coro)


async def _make_repo() -> tuple[MemoryRepository, asyncpg.Pool]:
    pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=2, max_size=5)
    return MemoryRepository(pool), pool


async def _cleanup(pool: asyncpg.Pool, *company_ids: str) -> None:
    async with pool.acquire() as conn:
        for company_id in company_ids:
            await conn.execute("DELETE FROM public.memory_fact_history WHERE company_id=$1", company_id)
            await conn.execute("DELETE FROM public.memory_facts WHERE company_id=$1", company_id)
    await pool.close()


@pytest.fixture
def db_available() -> bool:
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL not configured")
    return True


# ---------------------------------------------------------------------------
# T-1: detection
# ---------------------------------------------------------------------------

def test_conflict_is_detected_and_logged(db_available, caplog):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            with caplog.at_level("WARNING"):
                await repo.upsert_fact(
                    company_id=company_id, session_id="s2", fact_type="other",
                    fact_key="stage", fact_value="growth", confidence=80,
                )
            return caplog.text
        finally:
            await _cleanup(pool, company_id)

    log_text = _run(scenario())
    assert "Fact conflict detected" in log_text


# ---------------------------------------------------------------------------
# T-2: preservation
# ---------------------------------------------------------------------------

def test_conflicting_assertions_are_preserved_not_overwritten(db_available):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            history = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            return history, current
        finally:
            await _cleanup(pool, company_id)

    history, current = _run(scenario())

    assert len(history) == 1
    conflict_event = history[0]
    assert conflict_event["status"] == "conflict_replaced"
    sources = {s["fact_value"] for s in conflict_event["sources_weighed"]}
    assert sources == {"seed", "growth"}, "both the superseded and winning assertions must survive"
    assert current["fact_value"] == "growth"


def test_rejected_conflicting_assertion_is_preserved_when_existing_wins(db_available):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=90,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="decline", confidence=10,
            )
            history = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            return history, current
        finally:
            await _cleanup(pool, company_id)

    history, current = _run(scenario())

    assert len(history) == 1
    rejected = history[0]
    assert rejected["status"] == "conflict_kept"
    assert rejected["fact_value"] == "decline"
    sources = {s["fact_value"] for s in rejected["sources_weighed"]}
    assert sources == {"growth", "decline"}, "the rejected low-confidence assertion must still be recorded"
    assert current["fact_value"] == "growth", "memory_facts keeps the higher-confidence value"


# ---------------------------------------------------------------------------
# T-3: provenance
# ---------------------------------------------------------------------------

def test_resolution_basis_and_sources_weighed_are_recorded(db_available):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="goal", fact_value="expand regionally", confidence=50,
                source_event_id="evt-1",
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="goal", fact_value="consolidate operations", confidence=70,
                source_event_id="evt-2",
            )
            return await repo.fetch_fact_history(company_id=company_id, fact_key="goal")
        finally:
            await _cleanup(pool, company_id)

    history = _run(scenario())

    replaced = next(row for row in history if row["status"] == "conflict_replaced")
    assert replaced["resolution_basis"] == "new_confidence_gte_existing"
    assert replaced["provenance"]["source_event_id"] == "evt-2"
    sources = replaced["sources_weighed"]
    assert {s["role"] for s in sources} == {"existing", "incoming"}
    existing_source = next(s for s in sources if s["role"] == "existing")
    assert existing_source["fact_value"] == "expand regionally"
    assert existing_source["source_event_id"] == "evt-1"


# ---------------------------------------------------------------------------
# T-4: residual uncertainty
# ---------------------------------------------------------------------------

def test_residual_uncertainty_recorded_for_both_conflict_outcomes(db_available):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s3", fact_type="other",
                fact_key="stage", fact_value="decline", confidence=20,
            )
            return await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
        finally:
            await _cleanup(pool, company_id)

    history = _run(scenario())

    # Only the two conflict events are recorded -- the plain "seed" insert
    # is not a conflict and leaves no history row (AF-1 stays out of scope).
    assert len(history) == 2
    replaced = next(row for row in history if row["status"] == "conflict_replaced")
    kept = next(row for row in history if row["status"] == "conflict_kept")
    assert replaced["residual_uncertainty"] and "superseded" in replaced["residual_uncertainty"]
    assert kept["residual_uncertainty"] and "not adopted" in kept["residual_uncertainty"]


# ---------------------------------------------------------------------------
# T-5: retrievability
# ---------------------------------------------------------------------------

def test_conflicts_and_resolutions_are_retrievable_after_the_fact(db_available):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            # Retrieval happens in a call unrelated to the writes above --
            # simulating "after the fact" inspection.
            full_ledger = await repo.fetch_fact_history(company_id=company_id)
            scoped_ledger = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            facts = await repo.fetch_facts(company_id=company_id)
            return full_ledger, scoped_ledger, facts
        finally:
            await _cleanup(pool, company_id)

    full_ledger, scoped_ledger, facts = _run(scenario())

    assert len(full_ledger) == 1
    assert len(scoped_ledger) == 1
    assert full_ledger[0]["status"] == "conflict_replaced"
    stage_fact = next(f for f in facts if f["fact_key"] == "stage")
    assert stage_fact["has_conflict"] is True
    assert stage_fact["residual_uncertainty"]


def test_build_company_profile_surfaces_conflicts(db_available):
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s3", fact_type="other",
                fact_key="goal", fact_value="expand regionally", confidence=50,
            )
            return await repo.build_company_profile(company_id=company_id)
        finally:
            await _cleanup(pool, company_id)

    profile = _run(scenario())

    assert profile["stage"] == "growth"
    assert "stage" in profile["conflicts"]
    assert "goal" not in profile["conflicts"]


# ---------------------------------------------------------------------------
# T-6: D1 behaviour -- resolution is confidence-driven, not chronological
# ---------------------------------------------------------------------------

def test_later_lower_confidence_input_does_not_override_earlier_higher_confidence(db_available):
    """D1 (automatic chronological deference vs. investigation) regression.

    ENG-CONF-001 does not resolve D1 to Satisfied -- that requires the
    prompt-layer / investigation-mechanism work deferred at R6, which is out
    of this task's scope. This test only guards against regressing to naive
    "last write wins" behaviour: a later assertion with lower confidence must
    not silently replace an earlier, higher-confidence one.
    """
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=90,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="decline", confidence=5,
            )
            return await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
        finally:
            await _cleanup(pool, company_id)

    current = _run(scenario())
    assert current["fact_value"] == "growth", "later-but-weaker input must not override on recency alone"


def test_equal_confidence_conflict_replaces(db_available):
    """Documents the tie-breaking rule (conf >= existing_conf replaces) as an
    explicit, tested behaviour rather than an incidental >= in the code."""
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=50,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=50,
            )
            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            history = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            return current, history
        finally:
            await _cleanup(pool, company_id)

    current, history = _run(scenario())
    assert current["fact_value"] == "growth"
    assert history[0]["status"] == "conflict_replaced"
    assert history[0]["resolution_basis"] == "new_confidence_gte_existing"


# ---------------------------------------------------------------------------
# T-7: D2 behaviour -- detection + preservation + retrievability together
# ---------------------------------------------------------------------------

def test_conflict_detection_preservation_and_retrievability_together(db_available):
    """D2 (silent resolution vs. detection and preservation) was Partially
    Satisfied: detection existed but preservation/provenance did not. This
    test exercises all three together against the same conflict, closing
    exactly that gap for the memory_facts write path.
    """
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            history = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            return history, current
        finally:
            await _cleanup(pool, company_id)

    history, current = _run(scenario())

    # Detected (not silent):
    assert any(row["status"] == "conflict_replaced" for row in history)
    # Preserved (both sides retrievable, not just the winner):
    sources = {s["fact_value"] for s in history[0]["sources_weighed"]}
    assert sources == {"seed", "growth"}
    # Surfaced on the read path, not hidden behind the winning value alone:
    assert current["has_conflict"] is True


def test_has_conflict_survives_reinforcement_after_conflict(db_available):
    """Codex finding #4: has_conflict must not become False merely because a
    later same-value reinforcement occurs. Reinforcement never writes to
    memory_fact_history (it is not a conflict), so it cannot mask the earlier
    real conflict recorded there -- this test proves that end to end via the
    coordinated read path (get_fact_by_key and fetch_facts both)."""
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s3", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=82,
            )
            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            facts = await repo.fetch_facts(company_id=company_id)
            return current, facts
        finally:
            await _cleanup(pool, company_id)

    current, facts = _run(scenario())

    assert current["confidence"] > 80, "reinforcement must still raise confidence"
    assert current["has_conflict"] is True, "a later uncontested reinforcement must not hide the earlier real conflict"
    stage_fact = next(f for f in facts if f["fact_key"] == "stage")
    assert stage_fact["has_conflict"] is True


# ---------------------------------------------------------------------------
# T-8: D3 behaviour -- append-with-provenance, prior records preserved
# ---------------------------------------------------------------------------

def test_append_with_provenance_preserves_prior_record(db_available):
    """D3 (substitution/overwrite vs. append-with-provenance) was Not
    Satisfied: 'the prior fact_value is not written anywhere else first -- it
    is gone.' This test proves the prior value is no longer gone: at the
    moment a conflict occurs, it is captured -- with its own provenance --
    inside the conflict event's sources_weighed, even though memory_facts
    still overwrites its own current-value pointer for fast lookups.

    (Revised from the original version of this test, which asserted a
    separate top-level 'initial' history row for the prior value. Codex
    finding #5: writing a history row for every non-conflicting update is
    adjacent finding AF-1 -- Founder Decision R4 -- which stays out of
    ENG-CONF-001 scope. The prior assertion is preserved at conflict time
    instead, which still satisfies D3 without a general history ledger.)
    """
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
                source_event_id="evt-seed",
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
                source_event_id="evt-growth",
            )
            return await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
        finally:
            await _cleanup(pool, company_id)

    history = _run(scenario())

    assert len(history) == 1
    winner = history[0]
    assert winner["status"] == "conflict_replaced"
    assert winner["fact_value"] == "growth"
    assert winner["resolution_basis"]
    assert winner["provenance"]["source_event_id"] == "evt-growth"

    prior_source = next(s for s in winner["sources_weighed"] if s["role"] == "existing")
    assert prior_source["fact_value"] == "seed"
    assert prior_source["source_event_id"] == "evt-seed"


# ---------------------------------------------------------------------------
# Codex peer review corrections -- additional required coverage
# ---------------------------------------------------------------------------

def test_history_write_failure_rolls_back_the_memory_facts_update(db_available):
    """Codex finding #1 (BLOCKER): atomicity. If the memory_fact_history
    insert fails, the memory_facts mutation it was supposed to accompany
    must not persist -- the two writes happen on one connection inside one
    transaction. Simulated by making the history INSERT raise after the
    memory_facts UPDATE has been issued on the same (uncommitted)
    transaction."""
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        original_execute = asyncpg.Connection.execute
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )

            async def failing_execute(self, query, *args, **kwargs):
                if "INSERT INTO public.memory_fact_history" in query:
                    raise RuntimeError("simulated history insert failure")
                return await original_execute(self, query, *args, **kwargs)

            asyncpg.Connection.execute = failing_execute
            raised = False
            try:
                await repo.upsert_fact(
                    company_id=company_id, session_id="s2", fact_type="other",
                    fact_key="stage", fact_value="growth", confidence=80,
                )
            except RuntimeError:
                raised = True
            finally:
                asyncpg.Connection.execute = original_execute

            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            history = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            return raised, current, history
        finally:
            asyncpg.Connection.execute = original_execute
            await _cleanup(pool, company_id)

    raised, current, history = _run(scenario())

    assert raised is True
    assert current["fact_value"] == "seed", "the memory_facts UPDATE must have rolled back with the failed history insert"
    assert history == [], "no partial/orphaned history row may survive a rolled-back transaction"


def test_concurrent_conflicting_upserts_serialize_correctly(db_available):
    """Codex finding #2 (BLOCKER): concurrency. Two concurrent upserts for
    the same fact_key must not both be classified as initial, must not
    silently overwrite each other, must not pair one fact_value with
    another's confidence, and must not lose conflict preservation."""
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await asyncio.gather(
                repo.upsert_fact(
                    company_id=company_id, session_id="sA", fact_type="other",
                    fact_key="stage", fact_value="alpha", confidence=70,
                ),
                repo.upsert_fact(
                    company_id=company_id, session_id="sB", fact_type="other",
                    fact_key="stage", fact_value="beta", confidence=90,
                ),
            )
            current = await repo.get_fact_by_key(company_id=company_id, fact_key="stage")
            history = await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
            return current, history
        finally:
            await _cleanup(pool, company_id)

    current, history = _run(scenario())

    # Higher confidence must win regardless of which coroutine's INSERT won
    # the race to create the row first.
    assert current["fact_value"] == "beta"
    assert current["confidence"] == 90
    # Exactly one conflict event -- not two "initial" rows, not a lost update.
    assert len(history) == 1
    assert history[0]["status"] in ("conflict_replaced", "conflict_kept")
    assert {s["fact_value"] for s in history[0]["sources_weighed"]} == {"alpha", "beta"}


def test_conflict_with_links_to_true_current_assertion_not_rejected_one(db_available):
    """Codex finding #3 (BLOCKER): conflict linkage. A prior rejected
    (conflict_kept) event must never become the conflict_with reference for
    a later conflict against the still-current assertion; only a prior
    conflict_replaced event -- one that actually became current -- may be
    referenced."""
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_id, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=90,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="decline", confidence=10,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s3", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=95,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s4", fact_type="other",
                fact_key="stage", fact_value="collapse", confidence=5,
            )
            return await repo.fetch_fact_history(company_id=company_id, fact_key="stage")
        finally:
            await _cleanup(pool, company_id)

    history = _run(scenario())
    by_value = {row["fact_value"]: row for row in history}

    decline_row = by_value["decline"]
    growth_row = by_value["growth"]
    collapse_row = by_value["collapse"]

    assert decline_row["status"] == "conflict_kept"
    assert decline_row["conflict_with"] is None, "no prior conflict_replaced event exists yet"

    assert growth_row["status"] == "conflict_replaced"
    assert growth_row["conflict_with"] is None, (
        "seed was never itself a conflict_replaced event; the rejected 'decline' "
        "row must NOT become the reference"
    )
    assert growth_row["conflict_with"] != decline_row["id"]

    assert collapse_row["status"] == "conflict_kept"
    assert collapse_row["conflict_with"] == growth_row["id"], (
        "must link to the event that actually made 'growth' the current assertion"
    )


def test_expansion_market_reads_are_excluded_from_conflict_join(db_available):
    """Codex finding #6: the fact_key-based join must not let expansion_market
    inherit conflict state that was never actually about it.

    Write-path correction (discovered while building this test): the
    documented "expansion_market allows multiple rows" business rule is
    already unreachable today -- memory_facts' UNIQUE (company_id, fact_key)
    constraint rejects a second row for fact_key='expansion_market'
    regardless of how it is inserted (verified: even a raw multi-row SQL
    INSERT for two different expansion_market values raises
    UniqueViolationError). That is a pre-existing schema-level defect, not
    named in any S1-S4 surface or Codex finding, and is not fixed here.

    So this test proves the join guard (`fact_key <> 'expansion_market'`)
    directly and adversarially: it seeds a *synthetic*
    memory_fact_history row for fact_key='expansion_market' with a conflict
    status -- something the application itself can never produce, since
    expansion_market never conflicts -- and asserts fetch_facts still does
    not attach it to the real expansion_market fact. This is a stronger
    check than relying on the application simply never generating such a
    row; it proves the guard holds even if that invariant were ever broken.
    """
    company_id = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO public.memory_facts
                    (company_id, session_id, fact_type, fact_key, fact_value, confidence)
                    VALUES ($1,'s1','other','expansion_market','Egypt',80)
                    """,
                    company_id,
                )
                # Adversarial: a history row that should be structurally
                # impossible in practice, but if it ever existed, must still
                # not be joined onto the real expansion_market fact.
                await conn.execute(
                    """
                    INSERT INTO public.memory_fact_history
                    (company_id, fact_type, fact_key, fact_value, confidence, status,
                     resolution_basis, sources_weighed, residual_uncertainty, provenance)
                    VALUES
                    ($1,'other','expansion_market','rogue-conflict-value',10,'conflict_kept',
                     'existing_confidence_gt_new','[]'::jsonb,'synthetic test row','{}'::jsonb)
                    """,
                    company_id,
                )
            # A real, unrelated conflict on a different key must not bleed
            # into expansion_market's row via the fact_key-based join either.
            await repo.upsert_fact(
                company_id=company_id, session_id="s3", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_id, session_id="s4", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            return await repo.fetch_facts(company_id=company_id)
        finally:
            await _cleanup(pool, company_id)

    facts = _run(scenario())

    expansion_fact = next(f for f in facts if f["fact_key"] == "expansion_market")
    assert expansion_fact["fact_value"] == "Egypt"
    assert expansion_fact["has_conflict"] is False, "the synthetic conflict row must not be joined onto expansion_market"
    assert expansion_fact["residual_uncertainty"] is None

    stage_fact = next(f for f in facts if f["fact_key"] == "stage")
    assert stage_fact["has_conflict"] is True


def test_conflict_state_does_not_cross_company_boundary(db_available):
    """Codex finding #7: tenant-safe linkage, application-level check. A
    second company that has never touched a fact_key must see no trace of
    another company's conflict on that same key."""
    company_a = str(uuid4())
    company_b = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_a, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_a, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            b_fact = await repo.get_fact_by_key(company_id=company_b, fact_key="stage")
            b_history = await repo.fetch_fact_history(company_id=company_b, fact_key="stage")
            return b_fact, b_history
        finally:
            await _cleanup(pool, company_a, company_b)

    b_fact, b_history = _run(scenario())
    assert b_fact is None
    assert b_history == []


def test_conflict_with_cannot_reference_another_companys_history_row(db_available):
    """Codex finding #7: tenant-safe linkage, database-level enforcement.
    The composite FK on (conflict_with, company_id) -> (id, company_id) must
    reject a cross-tenant reference outright, not merely rely on application
    code never constructing one."""
    company_a = str(uuid4())
    company_b = str(uuid4())

    async def scenario():
        repo, pool = await _make_repo()
        try:
            await repo.upsert_fact(
                company_id=company_a, session_id="s1", fact_type="other",
                fact_key="stage", fact_value="seed", confidence=60,
            )
            await repo.upsert_fact(
                company_id=company_a, session_id="s2", fact_type="other",
                fact_key="stage", fact_value="growth", confidence=80,
            )
            a_history = await repo.fetch_fact_history(company_id=company_a, fact_key="stage")
            a_row_id = a_history[0]["id"]

            with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO public.memory_fact_history
                        (company_id, fact_type, fact_key, fact_value, confidence, status,
                         conflict_with, resolution_basis, sources_weighed, provenance)
                        VALUES
                        ($1,'other','stage','rogue',50,'conflict_kept',
                         $2,'existing_confidence_gt_new','[]'::jsonb,'{}'::jsonb)
                        """,
                        company_b, a_row_id,
                    )
        finally:
            await _cleanup(pool, company_a)

    _run(scenario())
