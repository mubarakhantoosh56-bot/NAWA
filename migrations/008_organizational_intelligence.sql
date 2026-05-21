-- NAWA Organizational Intelligence Architecture MVP.
-- Models the company as a living operational organization, with ERP as one input source.

CREATE TABLE IF NOT EXISTS company_divisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    parent_division_id UUID NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    division_type TEXT NOT NULL DEFAULT 'business_unit',
    description TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_company_divisions_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_company_divisions_parent
        FOREIGN KEY (parent_division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_company_divisions_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_company_divisions_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_company_divisions_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id),
    CONSTRAINT uq_company_divisions_slug_active
        UNIQUE (company_id, slug)
);

CREATE TABLE IF NOT EXISTS operational_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    department_id UUID NULL,
    name TEXT NOT NULL,
    unit_type TEXT NOT NULL,
    location TEXT NULL,
    capacity_label TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_operational_units_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_operational_units_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_operational_units_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS department_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    source_department_id UUID NULL,
    source_department_key TEXT NOT NULL,
    target_department_id UUID NULL,
    target_department_key TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    dependency_direction TEXT NOT NULL DEFAULT 'source_depends_on_target',
    description TEXT NOT NULL,
    strength INTEGER NOT NULL DEFAULT 70,
    risk_if_broken TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_department_relationships_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_department_relationships_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_department_relationships_source_department
        FOREIGN KEY (source_department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_department_relationships_target_department
        FOREIGN KEY (target_department_id)
        REFERENCES departments(id),
    CONSTRAINT chk_department_relationships_strength
        CHECK (strength BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS operational_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    owning_department_id UUID NULL,
    name TEXT NOT NULL,
    workflow_type TEXT NOT NULL,
    description TEXT NOT NULL,
    trigger_source TEXT NOT NULL DEFAULT 'native_input',
    input_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    kpi_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_operational_workflows_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_operational_workflows_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_operational_workflows_owning_department
        FOREIGN KEY (owning_department_id)
        REFERENCES departments(id),
    CONSTRAINT chk_operational_workflows_input_sources_array
        CHECK (jsonb_typeof(input_sources) = 'array'),
    CONSTRAINT chk_operational_workflows_kpi_keys_array
        CHECK (jsonb_typeof(kpi_keys) = 'array')
);

CREATE TABLE IF NOT EXISTS kpi_ownerships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    department_id UUID NULL,
    user_id UUID NULL,
    workflow_id UUID NULL,
    kpi_key TEXT NOT NULL,
    kpi_label TEXT NOT NULL,
    ownership_type TEXT NOT NULL DEFAULT 'accountable',
    target_label TEXT NULL,
    cadence TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_kpi_ownerships_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_kpi_ownerships_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_kpi_ownerships_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_kpi_ownerships_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_kpi_ownerships_workflow
        FOREIGN KEY (workflow_id)
        REFERENCES operational_workflows(id)
);

CREATE TABLE IF NOT EXISTS user_operational_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role_id UUID NULL,
    department_id UUID NULL,
    division_id UUID NULL,
    operational_impact TEXT NULL,
    kpi_ownership JSONB NOT NULL DEFAULT '[]'::jsonb,
    related_workflows JSONB NOT NULL DEFAULT '[]'::jsonb,
    issues_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    activity_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_user_operational_profiles_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_user_operational_profiles_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_user_operational_profiles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id),
    CONSTRAINT fk_user_operational_profiles_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_user_operational_profiles_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT uq_user_operational_profiles_company_user
        UNIQUE (company_id, user_id),
    CONSTRAINT chk_user_operational_profiles_kpi_array
        CHECK (jsonb_typeof(kpi_ownership) = 'array'),
    CONSTRAINT chk_user_operational_profiles_workflows_array
        CHECK (jsonb_typeof(related_workflows) = 'array'),
    CONSTRAINT chk_user_operational_profiles_issues_array
        CHECK (jsonb_typeof(issues_history) = 'array')
);

CREATE TABLE IF NOT EXISTS hr_shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    department_id UUID NULL,
    user_id UUID NULL,
    shift_name TEXT NOT NULL,
    starts_at TIMESTAMPTZ NULL,
    ends_at TIMESTAMPTZ NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_hr_shifts_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_hr_shifts_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_hr_shifts_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_hr_shifts_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS hr_attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    user_id UUID NOT NULL,
    department_id UUID NULL,
    division_id UUID NULL,
    shift_id UUID NULL,
    attendance_date DATE NOT NULL,
    status TEXT NOT NULL,
    check_in_at TIMESTAMPTZ NULL,
    check_out_at TIMESTAMPTZ NULL,
    source_type TEXT NOT NULL DEFAULT 'native_input',
    source_ref TEXT NULL,
    productivity_signal TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_hr_attendance_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_hr_attendance_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_hr_attendance_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_hr_attendance_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_hr_attendance_shift
        FOREIGN KEY (shift_id)
        REFERENCES hr_shifts(id)
);

CREATE TABLE IF NOT EXISTS hr_leave_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    user_id UUID NOT NULL,
    department_id UUID NULL,
    division_id UUID NULL,
    leave_type TEXT NOT NULL,
    starts_on DATE NOT NULL,
    ends_on DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'requested',
    operational_impact TEXT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_hr_leave_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_hr_leave_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_hr_leave_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_hr_leave_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT chk_hr_leave_dates
        CHECK (ends_on >= starts_on)
);

CREATE TABLE IF NOT EXISTS hr_performance_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    user_id UUID NOT NULL,
    department_id UUID NULL,
    division_id UUID NULL,
    note_type TEXT NOT NULL DEFAULT 'performance_note',
    note TEXT NOT NULL,
    productivity_signal TEXT NULL,
    operational_impact TEXT NULL,
    created_by UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT fk_hr_performance_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_hr_performance_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_hr_performance_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_hr_performance_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT fk_hr_performance_created_by
        FOREIGN KEY (created_by)
        REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS integration_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    provider_key TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    source_system TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    native_fallback_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sync_mode TEXT NOT NULL DEFAULT 'manual',
    mapped_entities JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_integration_sources_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_integration_sources_division
        FOREIGN KEY (division_id)
        REFERENCES company_divisions(id),
    CONSTRAINT chk_integration_sources_mapped_entities_array
        CHECK (jsonb_typeof(mapped_entities) = 'array')
);

CREATE INDEX IF NOT EXISTS idx_company_divisions_company_active
    ON company_divisions (company_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_operational_units_company_division
    ON operational_units (company_id, division_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_department_relationships_company_source
    ON department_relationships (company_id, source_department_key)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_operational_workflows_company_department
    ON operational_workflows (company_id, owning_department_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_kpi_ownerships_company_department
    ON kpi_ownerships (company_id, department_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_user_operational_profiles_company_user
    ON user_operational_profiles (company_id, user_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_hr_attendance_company_date
    ON hr_attendance_records (company_id, attendance_date DESC);

CREATE INDEX IF NOT EXISTS idx_integration_sources_company_status
    ON integration_sources (company_id, status)
    WHERE deleted_at IS NULL;
