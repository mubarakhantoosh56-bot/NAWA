-- NAWA Phase 1A: AI-proposed operational event drafts.
-- Stores per-file draft events proposed by the file operational analyzer.
-- No record is written to operational_events without explicit human confirmation.
-- Full extracted text is NOT stored here; it remains in file_chunks/RAG layer.

CREATE TABLE IF NOT EXISTS operational_event_drafts (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id           UUID NOT NULL,
    file_id              UUID NOT NULL,
    department_id        UUID NULL,
    created_by_user_id   UUID NOT NULL,

    -- AI proposal (no extracted text stored; only the short evidence fragment)
    proposed_title       TEXT NOT NULL,
    proposed_category    TEXT NOT NULL DEFAULT 'daily_update',
    proposed_priority    TEXT NOT NULL DEFAULT 'normal',
    proposed_summary     TEXT NOT NULL,
    evidence_quote       TEXT NULL,
    confidence           INTEGER NOT NULL DEFAULT 0,
    needs_clarification  BOOLEAN NOT NULL DEFAULT FALSE,
    clarification_hint   TEXT NULL,

    -- lifecycle: pending until human acts
    status               TEXT NOT NULL DEFAULT 'pending',
    user_edits           JSONB NOT NULL DEFAULT '{}'::jsonb,
    confirmed_event_id   UUID NULL,
    confirmed_by_user_id UUID NULL,
    confirmed_at         TIMESTAMPTZ NULL,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_event_drafts_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),

    CONSTRAINT fk_event_drafts_file
        FOREIGN KEY (file_id)
        REFERENCES files(id) ON DELETE CASCADE,

    CONSTRAINT fk_event_drafts_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),

    CONSTRAINT chk_event_drafts_status
        CHECK (status IN ('pending', 'confirmed', 'rejected')),

    CONSTRAINT chk_event_drafts_confidence
        CHECK (confidence BETWEEN 0 AND 100),

    CONSTRAINT chk_event_drafts_category
        CHECK (proposed_category IN (
            'daily_update', 'kpi', 'issue', 'decision', 'report', 'alert', 'note'
        )),

    CONSTRAINT chk_event_drafts_priority
        CHECK (proposed_priority IN ('low', 'normal', 'watch', 'high', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_event_drafts_company_file
    ON operational_event_drafts (company_id, file_id);

CREATE INDEX IF NOT EXISTS idx_event_drafts_company_status
    ON operational_event_drafts (company_id, status, created_at DESC);
