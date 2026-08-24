"""Service for retrieving outcome-backed Organizational Memory (M8 Slice 4A:
Organizational Memory Retrieval Foundation).

BACKEND-ONLY, DORMANT, READ-ONLY. Nothing in app/api/chat.py,
app/services/openai_client.py, or app/services/decision_context.py calls
this service, and this service calls nothing in those files either - live
/ai/chat wiring, prompt-block construction, and any ReasoningReceipt
provenance extension are explicitly separate, later, independently-
authorized slices (M8 Slice 4B+). This module performs no writes and no
mutation: it composes only the existing, unmodified
DecisionMemoryRepository/OutcomeMemoryRepository read methods.

Core law (Founder Correction 1, M8 Slice 4A): a DecisionMemory is eligible
for retrieval ONLY if it has at least one ACTIVE OutcomeMemory - a decision
with zero recorded outcomes is historical decision history, not yet
outcome-informed organizational experience. An explicit active
OutcomeMemory(result_state="unknown") IS a real recorded outcome and
therefore IS eligible; it is not the same as having no outcome at all.

Core law (Founder Correction 2, M8 Slice 4A): this is a BOUNDED HISTORICAL
CANDIDATE RETRIEVAL FOUNDATION, not a similarity/relevance engine.
situation_id equality means the exact same situation, never "similar."
When situation_id is supplied, retrieval is exact-situation-only and never
backfilled with unrelated company-wide recent history in the same call
(that would make the result look more semantically coherent than it is).
When situation_id is omitted, retrieval returns bounded recent
company-wide outcome-backed candidates - never labeled "similar."

Core law (Founder Correction 3, M8 Slice 4A): the returned aggregate
carries reasoning_receipt_id as an opaque durable pointer, copied directly
off DecisionMemory - this module never imports or calls
ReasoningReceiptRepository/ReasoningReceiptService and never reads
response_snapshot/evidence_refs/ceo_text/reasoning_assessment. Retrieved
content is anchored strictly to HUMAN-authored OME text
(decision_text/rationale/outcome_summary) - a deliberate recursive-memory
guard: an Outcome is recorded AFTER a decision, never claimed to have been
CAUSED by it, and AI-generated text must never be able to re-enter itself
as "memory" a later turn could cite.

Core law (Founder Correction 4, M8 Slice 4A): no text truncation happens
here. This is a domain retrieval/aggregation foundation, not a
prompt-rendering layer - token budgeting belongs to whichever later slice
actually transforms this into a prompt block. Retrieval is bounded by ITEM
COUNT only (`limit`).

Required-fix round (Codex pre-commit finding 1): exact-situation mode pages
through DecisionMemoryRepository.list_by_situation's new `offset` parameter
until either `limit` eligible items are collected or that exact situation's
decision history is exhausted - a single MAX_LIST_LIMIT-sized page is no
longer a completeness ceiling for this mode. Company-wide mode is
DELIBERATELY left unpaged: it fetches one bounded recent candidate pool and
accepts underfill, exactly as before (Founder Correction, Step 12/1D) -
paging must never be applied there, since "bounded recent" is the whole
point of that mode.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.ome.errors import InvalidMemoryInput
from app.ome.models.organizational_memory_context import (
    OrganizationalMemoryContextItem,
    OrganizationalMemoryOutcomeContext,
)
from app.ome.repositories.decision_memory_repository import (
    MAX_LIST_LIMIT as _DECISION_REPO_MAX_LIST_LIMIT,
)
from app.ome.repositories.decision_memory_repository import DecisionMemoryRepository
from app.ome.repositories.outcome_memory_repository import OutcomeMemoryRepository

DEFAULT_LIMIT = 5
MAX_LIMIT = 5
MIN_LIMIT = 1

# Size of the raw candidate pool fetched from DecisionMemoryRepository
# before outcome-eligibility filtering (Founder Correction 1) narrows it
# down to at most `limit` items. Matches the repository's own existing
# MAX_LIST_LIMIT exactly - no new SQL, no speculative overfetch beyond what
# the existing repository already supports. Per Step 12: if filtering
# no-outcome decisions out of this pool yields fewer than `limit` eligible
# items, returning fewer is correct behavior, never padded with a second
# query.
_CANDIDATE_POOL_SIZE = _DECISION_REPO_MAX_LIST_LIMIT


class OrganizationalMemoryRetrievalService:
    """Read-only composition of the existing DecisionMemoryRepository and
    OutcomeMemoryRepository - no new repository method, no receipt
    repository, no writes."""

    def __init__(self, db: Any) -> None:
        """Initialize the service with its repositories."""
        self.decision_repo = DecisionMemoryRepository(db)
        self.outcome_repo = OutcomeMemoryRepository(db)

    async def retrieve(
        self,
        *,
        company_id: UUID,
        situation_id: UUID | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[OrganizationalMemoryContextItem]:
        """Return up to `limit` outcome-backed Decision+Outcome aggregates
        for one company, newest decision first.

        company_id is mandatory and always trusted caller context (intended
        to come from AuthContext at a future API boundary, exactly like
        every other OME service) - every repository call below is scoped by
        it, and no client-provided company scope exists because this slice
        exposes no API at all.

        situation_id=None means company-wide recent mode (Founder
        Correction 2, Step 12): one bounded recent candidate pool, filtered
        to outcome-backed ones, underfill accepted, never paged further -
        never labeled "similar." situation_id set means exact-situation
        mode (Step 11): only decisions bound to that exact situation_id are
        considered, paged through in full (see _retrieve_exact_situation)
        so a qualifying decision outside the first page is never missed -
        never backfilled with unrelated company-wide history in the same
        call, and [] is a valid, correct result only when no qualifying
        decision exists anywhere in that exact situation's history.
        """
        _require_valid_limit(limit)

        if situation_id is not None:
            return await self._retrieve_exact_situation(
                company_id=company_id, situation_id=situation_id, limit=limit
            )
        return await self._retrieve_company_wide(company_id=company_id, limit=limit)

    async def _retrieve_company_wide(
        self, *, company_id: UUID, limit: int
    ) -> list[OrganizationalMemoryContextItem]:
        """Company-wide recent mode: ONE bounded candidate pool, never
        paged further. Underfill (fewer than `limit` results after
        outcome-eligibility filtering) is correct, accepted behavior, not a
        bug - "bounded recent" is the entire point of this mode (Founder
        Correction, Step 12/1D)."""
        candidate_decisions = await self.decision_repo.list_recent(
            company_id=company_id,
            include_superseded=False,
            limit=_CANDIDATE_POOL_SIZE,
        )
        # list_recent has no id tie-break in its own ORDER BY, so the
        # deterministic ordering (Step 10) is applied here in Python.
        ordered_candidates = sorted(
            candidate_decisions,
            key=lambda decision: (-decision.decided_at.timestamp(), str(decision.id)),
        )

        items: list[OrganizationalMemoryContextItem] = []
        for decision in ordered_candidates:
            if len(items) >= limit:
                break
            item = await self._build_item_if_eligible(company_id=company_id, decision=decision)
            if item is not None:
                items.append(item)
        return items

    async def _retrieve_exact_situation(
        self, *, company_id: UUID, situation_id: UUID, limit: int
    ) -> list[OrganizationalMemoryContextItem]:
        """Exact-situation mode: page through list_by_situation's full,
        deterministically-ordered (decided_at DESC, id ASC) history via its
        `offset` parameter until either `limit` eligible outcome-backed
        items are collected, or a page comes back shorter than requested
        (meaning that exact situation's decision history is exhausted).
        Never calls list_recent - never backfills with unrelated
        company-wide history in the same call (Founder Correction 2)."""
        items: list[OrganizationalMemoryContextItem] = []
        offset = 0
        while len(items) < limit:
            page = await self.decision_repo.list_by_situation(
                company_id=company_id,
                situation_id=situation_id,
                include_superseded=False,
                limit=_CANDIDATE_POOL_SIZE,
                offset=offset,
            )
            if not page:
                break

            # The repository's own ORDER BY (decided_at DESC, id ASC) is
            # already fully deterministic - each page is processed in that
            # exact order, never re-sorted or re-merged across pages.
            for decision in page:
                if len(items) >= limit:
                    break
                item = await self._build_item_if_eligible(company_id=company_id, decision=decision)
                if item is not None:
                    items.append(item)

            offset += len(page)
            if len(page) < _CANDIDATE_POOL_SIZE:
                # Short page: this exact situation's decision history is
                # exhausted - stop, do not request another page.
                break

        return items

    async def _build_item_if_eligible(
        self, *, company_id: UUID, decision: Any
    ) -> OrganizationalMemoryContextItem | None:
        """Return the full aggregate for one decision if it has >=1 active
        outcome (Founder Correction 1), else None. Shared by both retrieval
        modes so eligibility/ordering logic exists in exactly one place."""
        active_outcomes = await self.outcome_repo.list_by_decision(
            company_id=company_id,
            decision_memory_id=decision.id,
            include_superseded=False,
        )
        if not active_outcomes:
            return None

        # Deterministic, chronological outcome ordering (Step 9):
        # observed_at ASC with an explicit outcome id ASC tie-break - never
        # latest-only, never collapsed/summarized. The repository itself
        # returns newest-first; this re-sorts, it never trusts incidental
        # repository ordering for either axis.
        ordered_outcomes = sorted(
            active_outcomes,
            key=lambda outcome: (outcome.observed_at, str(outcome.id)),
        )

        return OrganizationalMemoryContextItem(
            decision_memory_id=decision.id,
            reasoning_receipt_id=decision.reasoning_receipt_id,
            situation_id=decision.situation_id,
            decision_text=decision.decision_text,
            rationale=decision.rationale,
            decided_at=decision.decided_at,
            outcomes=tuple(
                OrganizationalMemoryOutcomeContext(
                    outcome_memory_id=outcome.id,
                    outcome_summary=outcome.outcome_summary,
                    result_state=outcome.result_state,
                    observed_at=outcome.observed_at,
                )
                for outcome in ordered_outcomes
            ),
        )


def _require_valid_limit(limit: int) -> None:
    if not isinstance(limit, int) or isinstance(limit, bool) or not (MIN_LIMIT <= limit <= MAX_LIMIT):
        raise InvalidMemoryInput(f"limit must be an integer between {MIN_LIMIT} and {MAX_LIMIT}, got {limit!r}")
