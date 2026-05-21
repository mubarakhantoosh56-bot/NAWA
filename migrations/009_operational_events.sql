-- NAWA Live Operational Timeline Phase 1.
-- Stores tenant-scoped operational events for timeline, correlation, and future AI actions.

CREATE TABLE IF NOT EXISTS operational_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    department_id UUID NULL,
    created_by_user_id UUID NOT NULL,

    event_type TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_ref TEXT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_operational_events_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_operational_events_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_operational_events_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT chk_operational_events_priority
        CHECK (priority IN ('low', 'normal', 'watch', 'high', 'critical')),
    CONSTRAINT chk_operational_events_payload_object
        CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT chk_operational_events_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_operational_events_company_timestamp
    ON operational_events (company_id, event_timestamp DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_operational_events_company_department_timestamp
    ON operational_events (company_id, department_id, event_timestamp DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_operational_events_company_category_timestamp
    ON operational_events (company_id, category, event_timestamp DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_operational_events_company_priority_timestamp
    ON operational_events (company_id, priority, event_timestamp DESC)
    WHERE deleted_at IS NULL;
