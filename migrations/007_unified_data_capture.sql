-- NAWA Unified Data Capture Architecture MVP.
-- Stores every operational input before parsing/classification.

CREATE TABLE IF NOT EXISTS raw_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    division_id UUID NULL,
    department_id UUID NULL,
    source_type VARCHAR(40) NOT NULL,
    source_ref TEXT NULL,
    raw_content TEXT NOT NULL,
    file_id UUID NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_status VARCHAR(40) NOT NULL DEFAULT 'pending',
    language VARCHAR(20) NULL,

    CONSTRAINT fk_raw_inputs_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_raw_inputs_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_raw_inputs_file
        FOREIGN KEY (file_id)
        REFERENCES files(id),
    CONSTRAINT fk_raw_inputs_created_by
        FOREIGN KEY (created_by)
        REFERENCES users(id),
    CONSTRAINT chk_raw_inputs_source_type
        CHECK (source_type IN ('chat', 'form', 'file', 'integration', 'automation')),
    CONSTRAINT chk_raw_inputs_processing_status
        CHECK (processing_status IN ('pending', 'parsed', 'failed'))
);

CREATE TABLE IF NOT EXISTS parsed_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_input_id UUID NOT NULL,
    entity_type VARCHAR(40) NOT NULL,
    entity_value TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_parsed_entities_raw_input
        FOREIGN KEY (raw_input_id)
        REFERENCES raw_inputs(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_parsed_entities_entity_type
        CHECK (
            entity_type IN (
                'hall',
                'product',
                'sku',
                'quantity',
                'date',
                'issue',
                'kpi',
                'department',
                'division',
                'severity',
                'person',
                'customer',
                'supplier'
            )
        ),
    CONSTRAINT chk_parsed_entities_confidence
        CHECK (confidence BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS parsed_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_input_id UUID NOT NULL UNIQUE,
    inferred_department TEXT NULL,
    inferred_division TEXT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    severity TEXT NOT NULL,
    related_departments JSONB NOT NULL DEFAULT '[]'::jsonb,
    operational_signal TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_parsed_classifications_raw_input
        FOREIGN KEY (raw_input_id)
        REFERENCES raw_inputs(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_parsed_classifications_related_departments_array
        CHECK (jsonb_typeof(related_departments) = 'array'),
    CONSTRAINT chk_parsed_classifications_signal
        CHECK (operational_signal IN ('risk', 'issue', 'positive', 'opportunity', 'neutral')),
    CONSTRAINT chk_parsed_classifications_confidence
        CHECK (confidence BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS structured_record_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    raw_input_id UUID NOT NULL,
    division_id UUID NULL,
    department_id UUID NULL,
    record_type TEXT NOT NULL,
    extracted_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(40) NOT NULL DEFAULT 'draft',
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_structured_record_drafts_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_structured_record_drafts_raw_input
        FOREIGN KEY (raw_input_id)
        REFERENCES raw_inputs(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_structured_record_drafts_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_structured_record_drafts_created_by
        FOREIGN KEY (created_by)
        REFERENCES users(id),
    CONSTRAINT chk_structured_record_drafts_status
        CHECK (status IN ('draft', 'confirmed', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_raw_inputs_company_created_at
    ON raw_inputs (company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_raw_inputs_company_department
    ON raw_inputs (company_id, department_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_raw_inputs_file
    ON raw_inputs (file_id)
    WHERE file_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_parsed_entities_raw_input
    ON parsed_entities (raw_input_id);

CREATE INDEX IF NOT EXISTS idx_parsed_entities_type_value
    ON parsed_entities (entity_type, entity_value);

CREATE INDEX IF NOT EXISTS idx_structured_record_drafts_raw_input
    ON structured_record_drafts (raw_input_id);
