-- AIMX SaaS foundation system role templates draft.
-- Review-only migration: do not execute until approved.
--
-- Depends on:
-- - 001_saas_foundation_schema.sql
-- - 002_saas_foundation_indexes.sql

INSERT INTO roles (
    company_id,
    name,
    slug,
    description,
    permissions,
    is_system_role
)
VALUES
    (
        NULL,
        'Owner',
        'owner',
        'System role template with full tenant administration access.',
        '["*"]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Admin',
        'admin',
        'System role template for tenant administrators.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "departments.manage",
            "users.read",
            "users.invite",
            "roles.read"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Member',
        'member',
        'System role template for standard tenant members.',
        '[
            "ai.chat",
            "memory.read"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Department Operator',
        'department_operator',
        'System role template for users operating department-scoped AI workflows.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "agents.finance_ai.use",
            "agents.hr_ai.use",
            "agents.marketing_ai.use",
            "agents.operations_ai.use"
        ]'::jsonb,
        TRUE
    )
ON CONFLICT (slug)
    WHERE company_id IS NULL
      AND deleted_at IS NULL
DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    permissions = EXCLUDED.permissions,
    is_system_role = EXCLUDED.is_system_role,
    updated_at = NOW();
