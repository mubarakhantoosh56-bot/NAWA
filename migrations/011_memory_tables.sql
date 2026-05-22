-- NAWA operational memory tables used by Company Brain memory repositories.

CREATE TABLE IF NOT EXISTS public.memory_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    session_id TEXT NULL,
    event_type TEXT NOT NULL DEFAULT 'decision',
    user_message TEXT NULL,
    executive_summary TEXT NULL,
    logic_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
    idempotency_key TEXT UNIQUE NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.memory_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id TEXT NOT NULL,
    session_id TEXT NULL,
    fact_type TEXT NOT NULL DEFAULT 'other',
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 0,
    source_event_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT memory_facts_company_key_unique UNIQUE (company_id, fact_key)
);

CREATE INDEX IF NOT EXISTS idx_memory_events_company_created_at
    ON public.memory_events (company_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_events_company_session_created_at
    ON public.memory_events (company_id, session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_facts_company_updated_at
    ON public.memory_facts (company_id, updated_at DESC);
