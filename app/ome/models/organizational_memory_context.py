"""Internal retrieval-context shapes for M8 Slice 4A (Organizational Memory
Retrieval Foundation).

These are NOT persistence models - nothing here maps to a database table or
is ever written to the database. They are the bounded, safe aggregate shape
OrganizationalMemoryRetrievalService returns: one eligible DecisionMemory
paired with its active OutcomeMemory sequence.

Recursive-memory guard (Founder Correction 3, M8 Slice 4A): every field
here is either a durable internal provenance pointer (an id) or verbatim
HUMAN-authored OME text (decision_text/rationale/outcome_summary). Nothing
here is ever read from ReasoningReceipt.response_snapshot,
ReasoningReceipt.evidence_refs, or any other AI-generated text - an Outcome
was recorded after a decision, never claimed to have been caused by it, and
retrieval must never let AI-generated text re-enter itself as "memory" a
future turn could cite. reasoning_receipt_id is carried through as an
opaque pointer only, taken directly from DecisionMemory - this module never
imports or calls ReasoningReceiptRepository/ReasoningReceiptService.

No company_id, no user ids, no scoring, no similarity, no confidence, no
causal language, no policy label, and no text truncation (Founder
Correction 4: item-count bounding only, in the retrieval service - text
truncation/token budgeting is explicitly deferred to a later slice that
actually renders this into a prompt).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class OrganizationalMemoryOutcomeContext:
    """One HUMAN-recorded outcome, verbatim, inside a retrieved Decision
    aggregate. result_state is the exact backend enum value
    ("positive"/"negative"/"mixed"/"unknown") - never re-labeled here."""

    outcome_memory_id: UUID
    outcome_summary: str
    result_state: str
    observed_at: datetime


@dataclass(frozen=True)
class OrganizationalMemoryContextItem:
    """One eligible DecisionMemory paired with its active Outcome sequence,
    oldest observed_at first. Eligibility (>=1 active Outcome; see the
    retrieval service) is enforced by the service that constructs this
    object, not by this dataclass itself - `outcomes` is therefore always
    non-empty for any instance the service actually returns, but that
    invariant is not re-validated here."""

    decision_memory_id: UUID
    reasoning_receipt_id: UUID
    situation_id: UUID | None
    decision_text: str
    rationale: str | None
    decided_at: datetime
    outcomes: tuple[OrganizationalMemoryOutcomeContext, ...]
