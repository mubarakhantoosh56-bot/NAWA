-- NAWA Operational Feedback Loop Phase 1.
-- Groups tenant-scoped operational timeline events into operational state clusters.

CREATE TABLE IF NOT EXISTS operational_situations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    situation_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    time_window_start TIMESTAMPTZ NOT NULL,
    time_window_end TIMESTAMPTZ NOT NULL,
    department_id UUID NULL,
    detection_method TEXT NOT NULL DEFAULT 'rule_based',
    source_type TEXT NOT NULL DEFAULT 'manual_rule',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_operational_situations_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_operational_situations_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT chk_operational_situations_type
        CHECK (situation_type IN ('risk', 'bottleneck', 'positive_signal', 'anomaly')),
    CONSTRAINT chk_operational_situations_severity
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_operational_situations_status
        CHECK (status IN ('active', 'monitoring', 'resolved')),
    CONSTRAINT chk_operational_situations_detection_method
        CHECK (detection_method IN ('rule_based')),
    CONSTRAINT chk_operational_situations_source_type
        CHECK (source_type IN ('manual_rule', 'scheduled_rule', 'future_ai')),
    CONSTRAINT chk_operational_situations_time_window
        CHECK (time_window_start <= time_window_end)
);

CREATE TABLE IF NOT EXISTS situation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    situation_id UUID NOT NULL,
    event_id UUID NOT NULL,
    role TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_situation_events_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_situation_events_situation
        FOREIGN KEY (situation_id)
        REFERENCES operational_situations(id),
    CONSTRAINT fk_situation_events_event
        FOREIGN KEY (event_id)
        REFERENCES operational_events(id),
    CONSTRAINT uq_situation_events_company_situation_event
        UNIQUE (company_id, situation_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_operational_situations_company_status_window
    ON operational_situations (company_id, status, time_window_end DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_operational_situations_company_department_status_window
    ON operational_situations (company_id, department_id, status, time_window_end DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_situation_events_company_situation
    ON situation_events (company_id, situation_id);

CREATE INDEX IF NOT EXISTS idx_situation_events_company_event
    ON situation_events (company_id, event_id);
