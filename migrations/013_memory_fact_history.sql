-- ENG-CONF-001 (S1): durable conflict/resolution representation for memory_facts.
--
-- Records conflict *events* only -- assertions that collided with an existing
-- value for the same (company_id, fact_key) -- with both sides of the
-- conflict captured in sources_weighed at the moment it occurred. This is
-- deliberately narrower than a general history-of-every-update ledger:
-- R4 / AF-1 (history preservation for *all* memory_facts updates, not just
-- contested ones) is explicitly out of ENG-CONF-001 scope and is not
-- implemented by this table.
--
-- conflict_with is tenant-safety enforced at the database level: it can only
-- reference a prior history row belonging to the same company_id (composite
-- FK against a composite unique constraint), not merely by convention.

CREATE TABLE IF NOT EXISTS public.memory_fact_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    session_id TEXT NULL,
    fact_type TEXT NOT NULL DEFAULT 'other',
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 0,
    source_event_id TEXT NULL,
    status TEXT NOT NULL,
    conflict_with UUID NULL,
    resolution_basis TEXT NULL,
    sources_weighed JSONB NOT NULL DEFAULT '[]'::jsonb,
    residual_uncertainty TEXT NULL,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_memory_fact_history_status
        CHECK (status IN ('conflict_replaced', 'conflict_kept')),
    CONSTRAINT chk_memory_fact_history_sources_weighed_array
        CHECK (jsonb_typeof(sources_weighed) = 'array'),
    CONSTRAINT chk_memory_fact_history_provenance_object
        CHECK (jsonb_typeof(provenance) = 'object'),
    CONSTRAINT uq_memory_fact_history_id_company
        UNIQUE (id, company_id),
    CONSTRAINT fk_memory_fact_history_conflict_with_same_company
        FOREIGN KEY (conflict_with, company_id)
        REFERENCES public.memory_fact_history (id, company_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_fact_history_company_key_created
    ON public.memory_fact_history (company_id, fact_key, created_at DESC);
