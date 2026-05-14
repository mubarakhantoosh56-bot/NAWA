-- AIMX RAG foundation files schema draft.
-- Review-only migration: do not execute until approved.
--
-- Depends on:
-- - 001_saas_foundation_schema.sql

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    department_id UUID NULL,
    uploaded_by_user_id UUID NOT NULL,

    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_files_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_files_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_files_uploaded_by_user
        FOREIGN KEY (uploaded_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_files_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_files_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_files_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id),
    CONSTRAINT chk_files_status
        CHECK (status IN ('uploaded', 'processing', 'ready', 'failed', 'deleted')),
    CONSTRAINT chk_files_size_positive
        CHECK (file_size_bytes >= 0)
);

CREATE TABLE IF NOT EXISTS file_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    file_id UUID NOT NULL,
    department_id UUID NULL,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ready',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_file_chunks_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_file_chunks_file
        FOREIGN KEY (file_id)
        REFERENCES files(id),
    CONSTRAINT fk_file_chunks_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT chk_file_chunks_status
        CHECK (status IN ('ready', 'failed')),
    CONSTRAINT chk_file_chunks_index_nonnegative
        CHECK (chunk_index >= 0),
    CONSTRAINT chk_file_chunks_token_count_nonnegative
        CHECK (token_count IS NULL OR token_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_files_company_active
    ON files (company_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_files_company_department_active
    ON files (company_id, department_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_files_company_status_active
    ON files (company_id, status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_file_chunks_company_file_active
    ON file_chunks (company_id, file_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_file_chunks_company_department_active
    ON file_chunks (company_id, department_id)
    WHERE deleted_at IS NULL;
