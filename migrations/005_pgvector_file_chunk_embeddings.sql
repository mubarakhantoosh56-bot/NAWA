-- AIMX pgvector foundation for semantic RAG retrieval.
-- Depends on:
-- - 004_rag_foundation_files.sql

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS file_chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    file_id UUID NOT NULL,
    chunk_id UUID NOT NULL,
    department_id UUID NULL,

    embedding_model TEXT NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_file_chunk_embeddings_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_file_chunk_embeddings_file
        FOREIGN KEY (file_id)
        REFERENCES files(id),
    CONSTRAINT fk_file_chunk_embeddings_chunk
        FOREIGN KEY (chunk_id)
        REFERENCES file_chunks(id),
    CONSTRAINT fk_file_chunk_embeddings_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT chk_file_chunk_embeddings_dimensions_positive
        CHECK (embedding_dimensions > 0),
    CONSTRAINT chk_file_chunk_embeddings_dimensions_expected
        CHECK (embedding_dimensions = 1536)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_file_chunk_embeddings_chunk_model_active_unique
    ON file_chunk_embeddings (chunk_id, embedding_model)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_file_chunk_embeddings_company_active
    ON file_chunk_embeddings (company_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_file_chunk_embeddings_company_department_active
    ON file_chunk_embeddings (company_id, department_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_file_chunk_embeddings_company_file_active
    ON file_chunk_embeddings (company_id, file_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_file_chunk_embeddings_embedding_hnsw
    ON file_chunk_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WHERE deleted_at IS NULL;
