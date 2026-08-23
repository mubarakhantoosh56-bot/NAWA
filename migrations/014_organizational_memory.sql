-- M8 Slice 1: Organizational Memory Engine (OME) MVP persistence foundation.
--
-- Exactly three new tables, per the Founder-approved Option B3 architecture
-- (M8 OME -- Provenance Integrity Decision):
--
--   ome_reasoning_receipts  -- immutable, server-created proof of what
--                              evidence one specific NAWA response used
--   ome_decision_memories   -- one explicit HUMAN decision, bound to the
--                              reasoning receipt it was made in response to
--   ome_outcome_memories    -- one HUMAN-recorded historical outcome of
--                              one decision
--
-- This migration is additive only: no existing table is renamed, no column
-- is dropped, no row is rewritten or backfilled. The one exception is a
-- single new UNIQUE constraint added to the existing operational_situations
-- table (Codex-required fix, see below) -- adding a constraint to an
-- existing table is additive (it can only make previously-valid data
-- invalid if a duplicate (id, company_id) pair already existed, which is
-- structurally impossible since id is already that table's primary key).
--
-- No API, service, retrieval, or live-reasoning wiring is introduced here --
-- persistence only (Slice 1 scope).
--
-- Tenant safety: every OME-to-OME reference (receipt<-decision,
-- decision<-outcome, each table's own supersession self-reference, AND
-- decision<-situation) uses the composite (id, company_id) FK pattern
-- already proven in migrations/013_memory_fact_history.sql's conflict_with
-- FK, so a cross-company link is rejected at the database level, not
-- merely by application-layer convention. This closes the Codex-flagged
-- gap in the first version of this migration, where situation_id was a
-- plain (non-composite) FK.

-- Codex-required fix: operational_situations needs a UNIQUE(id, company_id)
-- constraint so ome_decision_memories can FK against it tenant-safely.
-- operational_situations.id is already the table's PRIMARY KEY (globally
-- unique on its own), so this constraint can never reject any existing
-- row -- it only adds the composite uniqueness FKs require. No column is
-- added, no row is touched, no M7 runtime behavior changes.
ALTER TABLE operational_situations
    ADD CONSTRAINT uq_operational_situations_id_company UNIQUE (id, company_id);


CREATE TABLE IF NOT EXISTS ome_reasoning_receipts (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id           UUID NOT NULL,
    created_by_user_id   UUID NOT NULL,
    session_id           TEXT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Immutable audit snapshot of the finalized NAWA response necessary to
    -- identify what response the human later acted on (CEO-visible text,
    -- accepted reasoning assessment / recommendation basis) -- not a second
    -- conversational memory system and not raw request internals.
    response_snapshot    JSONB NOT NULL,

    -- Server-resolved evidence identity for this response (source_file_id /
    -- operational_event_id / etc.), populated by the future chat-response
    -- write path from the request-scoped reasoning_reference_catalog.
    -- Never a client declaration.
    evidence_refs        JSONB NOT NULL DEFAULT '[]'::jsonb,

    CONSTRAINT fk_ome_reasoning_receipts_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),

    CONSTRAINT fk_ome_reasoning_receipts_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),

    CONSTRAINT chk_ome_reasoning_receipts_response_snapshot_object
        CHECK (jsonb_typeof(response_snapshot) = 'object'),

    CONSTRAINT chk_ome_reasoning_receipts_evidence_refs_array
        CHECK (jsonb_typeof(evidence_refs) = 'array'),

    -- Enables tenant-safe composite FKs from ome_decision_memories.
    CONSTRAINT uq_ome_reasoning_receipts_id_company
        UNIQUE (id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_ome_reasoning_receipts_company_created_at
    ON ome_reasoning_receipts (company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ome_reasoning_receipts_company_session
    ON ome_reasoning_receipts (company_id, session_id);


CREATE TABLE IF NOT EXISTS ome_decision_memories (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id             UUID NOT NULL,
    reasoning_receipt_id   UUID NOT NULL,
    situation_id           UUID NULL,

    decision_text          TEXT NOT NULL,
    rationale               TEXT NULL,
    decided_by_user_id     UUID NOT NULL,
    decided_at              TIMESTAMPTZ NOT NULL,

    status                  TEXT NOT NULL DEFAULT 'active',
    superseded_by           UUID NULL,

    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ome_decision_memories_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),

    CONSTRAINT fk_ome_decision_memories_decided_by_user
        FOREIGN KEY (decided_by_user_id)
        REFERENCES users(id),

    -- Tenant-safe (Codex-required fix): a decision can only reference an
    -- operational_situation belonging to the same company.
    CONSTRAINT fk_ome_decision_memories_situation_same_company
        FOREIGN KEY (situation_id, company_id)
        REFERENCES operational_situations (id, company_id),

    -- Tenant-safe: a decision can only reference a reasoning receipt that
    -- belongs to the same company.
    CONSTRAINT fk_ome_decision_memories_receipt_same_company
        FOREIGN KEY (reasoning_receipt_id, company_id)
        REFERENCES ome_reasoning_receipts (id, company_id),

    -- Tenant-safe self-reference for supersession. No ON DELETE clause
    -- (Codex-required fix): OME hard deletion is not supported in MVP, so
    -- a decision that is still referenced as another decision's
    -- superseded_by must not be deletable at all -- default NO ACTION,
    -- not SET NULL (which is unsafe on a composite FK whose second column,
    -- company_id, is NOT NULL and must never be nulled).
    CONSTRAINT fk_ome_decision_memories_superseded_by_same_company
        FOREIGN KEY (superseded_by, company_id)
        REFERENCES ome_decision_memories (id, company_id),

    CONSTRAINT chk_ome_decision_memories_status
        CHECK (status IN ('active', 'superseded')),

    CONSTRAINT chk_ome_decision_memories_no_self_supersede
        CHECK (superseded_by IS NULL OR superseded_by <> id),

    -- Codex-required fix: status and superseded_by must never disagree --
    -- 'active' rows never carry a superseded_by, 'superseded' rows always do.
    CONSTRAINT chk_ome_decision_memories_status_supersession_consistent
        CHECK (
            (status = 'active' AND superseded_by IS NULL)
            OR
            (status = 'superseded' AND superseded_by IS NOT NULL)
        ),

    -- Enables tenant-safe composite FKs from ome_outcome_memories and from
    -- this table's own supersession self-reference.
    CONSTRAINT uq_ome_decision_memories_id_company
        UNIQUE (id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_ome_decision_memories_company_decided_at
    ON ome_decision_memories (company_id, decided_at DESC);

CREATE INDEX IF NOT EXISTS idx_ome_decision_memories_company_situation
    ON ome_decision_memories (company_id, situation_id);

CREATE INDEX IF NOT EXISTS idx_ome_decision_memories_company_status
    ON ome_decision_memories (company_id, status);

CREATE INDEX IF NOT EXISTS idx_ome_decision_memories_company_receipt
    ON ome_decision_memories (company_id, reasoning_receipt_id);


CREATE TABLE IF NOT EXISTS ome_outcome_memories (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id            UUID NOT NULL,
    decision_memory_id    UUID NOT NULL,

    outcome_summary       TEXT NOT NULL,
    result_state          TEXT NOT NULL,
    recorded_by_user_id   UUID NOT NULL,
    observed_at            TIMESTAMPTZ NOT NULL,

    status                 TEXT NOT NULL DEFAULT 'active',
    superseded_by          UUID NULL,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ome_outcome_memories_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),

    CONSTRAINT fk_ome_outcome_memories_recorded_by_user
        FOREIGN KEY (recorded_by_user_id)
        REFERENCES users(id),

    -- Tenant-safe: an outcome can only reference a decision that belongs
    -- to the same company.
    CONSTRAINT fk_ome_outcome_memories_decision_same_company
        FOREIGN KEY (decision_memory_id, company_id)
        REFERENCES ome_decision_memories (id, company_id),

    -- Tenant-safe self-reference for supersession. No ON DELETE clause
    -- (same Codex-required fix as ome_decision_memories, above).
    CONSTRAINT fk_ome_outcome_memories_superseded_by_same_company
        FOREIGN KEY (superseded_by, company_id)
        REFERENCES ome_outcome_memories (id, company_id),

    CONSTRAINT chk_ome_outcome_memories_result_state
        CHECK (result_state IN ('positive', 'negative', 'mixed', 'unknown')),

    CONSTRAINT chk_ome_outcome_memories_status
        CHECK (status IN ('active', 'superseded')),

    CONSTRAINT chk_ome_outcome_memories_no_self_supersede
        CHECK (superseded_by IS NULL OR superseded_by <> id),

    -- Codex-required fix: same status/superseded_by consistency invariant
    -- as ome_decision_memories.
    CONSTRAINT chk_ome_outcome_memories_status_supersession_consistent
        CHECK (
            (status = 'active' AND superseded_by IS NULL)
            OR
            (status = 'superseded' AND superseded_by IS NOT NULL)
        ),

    CONSTRAINT uq_ome_outcome_memories_id_company
        UNIQUE (id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_ome_outcome_memories_company_decision
    ON ome_outcome_memories (company_id, decision_memory_id);

CREATE INDEX IF NOT EXISTS idx_ome_outcome_memories_company_observed_at
    ON ome_outcome_memories (company_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_ome_outcome_memories_company_status
    ON ome_outcome_memories (company_id, status);
