-- M9 Slice 1: Decision Execution Foundation -- Action persistence.
--
-- Exactly two new tables, per the Founder-accepted M9 Architecture
-- Contract v1.3 (Option M9-2 -- Decision-linked Action + immutable
-- append-only change ledger):
--
--   ome_actions               -- CURRENT execution state of one
--                                human-authorized unit of work against
--                                exactly one DecisionMemory
--   ome_action_change_events  -- immutable append-only ledger covering
--                                exactly two change types: status
--                                transitions and assignment changes
--
-- This migration is additive only: no existing table is renamed, no
-- column is dropped, no row is rewritten or backfilled, and (unlike
-- migrations/014_organizational_memory.sql) no existing table needs a
-- new constraint -- ome_decision_memories already carries
-- uq_ome_decision_memories_id_company from migration 014, so this
-- migration can compose against it tenant-safely with zero alteration
-- to any existing table.
--
-- No API, service, retrieval, or live-reasoning wiring is introduced
-- here -- persistence only (Slice 1 scope, mirroring M8 Slice 1
-- exactly, per the Architecture Contract's own Slice 1 exit condition).
--
-- Tenant safety: Action -> DecisionMemory and ActionChangeEvent ->
-- Action both use the composite (id, company_id) FK pattern already
-- proven in migration 014, so a cross-company link is rejected at the
-- database level, not merely by application-layer convention.
--
-- Accepted, Founder-ratified trust-boundary exception (Architecture
-- Contract Sec 11.2): assigned_user_id has NO database-level composite
-- tenant guard. users has no company_id column, and every uniqueness
-- index on memberships is partial (WHERE department_id IS NULL / IS
-- NOT NULL), so PostgreSQL cannot use either as an FK target. The
-- database can only prove the assigned user EXISTS (plain FK to
-- users(id)); same-company active-membership validation is a Slice 2
-- domain-service responsibility (MembershipRepository.get_active_membership),
-- not a database constraint. Recorded here, not papered over.
--
-- due_at is deliberately absent (Founder Decision 2, deferred out of
-- M9 MVP). failed is deliberately absent (Sec 8.1, deferred). No
-- department_id, no Outcome linkage, no JSONB/metadata/payload column
-- on either table (Sec 9.5 anti-creep guard).
--
-- changed_at uses clock_timestamp(), not NOW()/CURRENT_TIMESTAMP
-- (Slice 1 correction, refined after independent re-review). NOW() /
-- CURRENT_TIMESTAMP is frozen at transaction BEGIN, not at the moment
-- a row is actually written. For two writers on the SAME Action row
-- serialized by a future SELECT ... FOR UPDATE (Sec 24.1), a
-- transaction that began earlier but loses the lock race could
-- otherwise record a changed_at from before it ever acquired the
-- lock -- a specific, identified inversion risk. clock_timestamp() is
-- evaluated at actual statement-execution time instead, which removes
-- that specific NOW()-based inversion risk and materially improves
-- audit-time fidelity.
--
-- clock_timestamp() is NOT, by itself, a strict monotonic causal
-- sequence, and this migration makes no such claim:
--   * the underlying system wall clock can step backward (e.g. an NTP
--     correction), which clock_timestamp() does not protect against;
--   * two events can land at or below the practical timestamp
--     resolution and tie, or fall close enough that a display ordering
--     cannot be treated as proof of which happened first;
--   * clock_timestamp() is not an Action-local sequence counter --
--     it is wall-clock time, nothing more.
-- changed_at is therefore audit/display time, not a formal causal
-- version. The authoritative audit evidence for what actually
-- happened is the ledger's persisted from-state/to-state values
-- themselves (from_status/to_status, from_assigned_user_id/
-- to_assigned_user_id), written under a future locked-row read of the
-- true prior state (Sec 24.1) -- truthful from-state capture, not
-- changed_at, is what makes the ledger honest. No sequence, version,
-- ordinal, or Lamport-clock column is introduced by this slice; if
-- live validation ever shows one is genuinely required by an accepted
-- contract invariant, that is a Founder-level decision, not an
-- engineering one to make unilaterally here.
--
-- ome_action_change_events is append-only as an ARCHITECTURE invariant
-- (Sec 9.3/9.5), not a database-enforced one at this slice: there is no
-- REVOKE, no immutability trigger, and no repository yet to own write
-- discipline. Slice 1 simply provides no UPDATE/DELETE API surface for
-- this table (none exists at all yet). Enforcement arrives with the
-- repository/service layer in a later slice, mirroring how migration
-- 014's OME tables rely on the same layered discipline today.
--
-- Every index below exists because Architecture Contract Sec 21.4 names
-- it explicitly as an M9 access path; none is speculative (see the
-- per-index comment next to each CREATE INDEX).


CREATE TABLE IF NOT EXISTS ome_actions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id            UUID NOT NULL,
    decision_memory_id    UUID NOT NULL,

    title                 TEXT NOT NULL,
    instructions          TEXT NULL,

    status                TEXT NOT NULL DEFAULT 'pending',

    assigned_user_id      UUID NULL,
    created_by_user_id    UUID NOT NULL,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at          TIMESTAMPTZ NULL,
    cancelled_at          TIMESTAMPTZ NULL,

    CONSTRAINT fk_ome_actions_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),

    -- Tenant-safe: an Action can only reference a decision that
    -- belongs to the same company (composite FK against migration
    -- 014's uq_ome_decision_memories_id_company).
    CONSTRAINT fk_ome_actions_decision_same_company
        FOREIGN KEY (decision_memory_id, company_id)
        REFERENCES ome_decision_memories (id, company_id),

    -- Plain FK only (Sec 11.2 / 11.3): no company-scoped composite
    -- target is structurally available for a client-supplied assignee.
    -- Same-company active-membership validation is a Slice 2
    -- domain-service responsibility, not a database constraint.
    CONSTRAINT fk_ome_actions_assigned_user
        FOREIGN KEY (assigned_user_id)
        REFERENCES users(id),

    -- JWT-derived, never client-supplied -- plain FK, matching the
    -- migration 014 actor-column precedent (created_by_user_id /
    -- decided_by_user_id / recorded_by_user_id).
    CONSTRAINT fk_ome_actions_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),

    CONSTRAINT chk_ome_actions_status
        CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),

    CONSTRAINT chk_ome_actions_title_not_blank
        CHECK (length(trim(title)) > 0),

    -- Terminal-timestamp invariants (Architecture Contract Sec 7.1 /
    -- 21.3): completed_at is set iff status = 'completed'; cancelled_at
    -- is set iff status = 'cancelled'. Together these two CHECKs also
    -- fully imply that a pending/in_progress Action has BOTH timestamps
    -- NULL -- no third constraint is needed to state that separately.
    CONSTRAINT chk_ome_actions_completed_at_consistent
        CHECK (
            (status = 'completed' AND completed_at IS NOT NULL)
            OR
            (status <> 'completed' AND completed_at IS NULL)
        ),

    CONSTRAINT chk_ome_actions_cancelled_at_consistent
        CHECK (
            (status = 'cancelled' AND cancelled_at IS NOT NULL)
            OR
            (status <> 'cancelled' AND cancelled_at IS NULL)
        ),

    -- Enables tenant-safe composite FK from ome_action_change_events.
    CONSTRAINT uq_ome_actions_id_company
        UNIQUE (id, company_id)
);

-- Sec 21.4: "the primary access path: list actions for a decision."
CREATE INDEX IF NOT EXISTS idx_ome_actions_company_decision
    ON ome_actions (company_id, decision_memory_id);

-- Sec 21.4: "open-work views."
CREATE INDEX IF NOT EXISTS idx_ome_actions_company_status
    ON ome_actions (company_id, status);

-- Sec 21.4: "recent actions."
CREATE INDEX IF NOT EXISTS idx_ome_actions_company_created_at
    ON ome_actions (company_id, created_at DESC);

-- Sec 21.4: "included in MVP; drives 'what am I responsible for'."
CREATE INDEX IF NOT EXISTS idx_ome_actions_company_assigned_user
    ON ome_actions (company_id, assigned_user_id);


CREATE TABLE IF NOT EXISTS ome_action_change_events (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id               UUID NOT NULL,
    action_id                UUID NOT NULL,

    change_type              TEXT NOT NULL,

    from_status               TEXT NULL,
    to_status                  TEXT NULL,

    from_assigned_user_id     UUID NULL,
    to_assigned_user_id       UUID NULL,

    changed_by_user_id        UUID NOT NULL,

    -- clock_timestamp(), not NOW() -- see this migration's header
    -- comment. Removes the NOW()-based transaction-start inversion
    -- risk and improves audit-time fidelity; it is audit/display time,
    -- not a strict monotonic causal sequence or version counter.
    changed_at                 TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),

    CONSTRAINT fk_ome_action_change_events_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),

    -- Tenant-safe: a change event can only reference an Action that
    -- belongs to the same company.
    CONSTRAINT fk_ome_action_change_events_action_same_company
        FOREIGN KEY (action_id, company_id)
        REFERENCES ome_actions (id, company_id),

    CONSTRAINT fk_ome_action_change_events_changed_by_user
        FOREIGN KEY (changed_by_user_id)
        REFERENCES users(id),

    CONSTRAINT fk_ome_action_change_events_from_assigned_user
        FOREIGN KEY (from_assigned_user_id)
        REFERENCES users(id),

    CONSTRAINT fk_ome_action_change_events_to_assigned_user
        FOREIGN KEY (to_assigned_user_id)
        REFERENCES users(id),

    -- Closed two-value discriminator (Architecture Contract Sec 9.5
    -- anti-creep guard). Adding a third value requires a Founder
    -- ratification, not an engineering decision.
    CONSTRAINT chk_ome_action_change_events_change_type
        CHECK (change_type IN ('status', 'assignment')),

    CONSTRAINT chk_ome_action_change_events_to_status
        CHECK (to_status IS NULL OR to_status IN ('pending', 'in_progress', 'completed', 'cancelled')),

    -- Slice 1 correction: from_status was previously unconstrained,
    -- which would have let a bogus historical value such as
    -- 'bogus' -> 'pending' pass the database boundary. from_status is
    -- NULL only for an Action's very first status event (no prior
    -- state to name); DB shape validation cannot know which row is
    -- "the first one" for a given action_id (that requires seeing
    -- sibling rows, which a CHECK cannot do) -- enforcing "NULL only on
    -- creation, and specifically NULL -> pending on creation" is a
    -- Slice 2 write-path invariant, not a schema-level one. This CHECK
    -- only proves that WHEN from_status is present, it names a real
    -- M9 status.
    CONSTRAINT chk_ome_action_change_events_from_status
        CHECK (from_status IS NULL OR from_status IN ('pending', 'in_progress', 'completed', 'cancelled')),

    -- Discriminated-union shape (Sec 9.4 / 21.3): a 'status' event
    -- carries to_status and NO assignment fields; an 'assignment'
    -- event carries NO status fields and a genuine from/to change. A
    -- row can never represent both change types, and never neither.
    CONSTRAINT chk_ome_action_change_events_shape
        CHECK (
            (
                change_type = 'status'
                AND to_status IS NOT NULL
                AND from_assigned_user_id IS NULL
                AND to_assigned_user_id IS NULL
            )
            OR
            (
                change_type = 'assignment'
                AND from_status IS NULL
                AND to_status IS NULL
                AND from_assigned_user_id IS DISTINCT FROM to_assigned_user_id
            )
        ),

    CONSTRAINT chk_ome_action_change_events_no_self_transition
        CHECK (from_status IS NULL OR from_status <> to_status)
);

-- Sec 21.4: the change-event table's one named index -- the unified
-- per-Action chronological read (Sec 9.3).
CREATE INDEX IF NOT EXISTS idx_ome_action_change_events_company_action_changed_at
    ON ome_action_change_events (company_id, action_id, changed_at);
