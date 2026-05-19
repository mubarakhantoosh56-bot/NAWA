-- NAWA Operational Intelligence MVP role templates and permissions.
-- Extends RBAC without replacing existing tenant isolation or auth flows.

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
        'CEO',
        'ceo',
        'System role template for executive operational intelligence across departments.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            "workspace.ceo",
            "operational.forms.read",
            "operational.forms.submit",
            "integrations.read",
            "agents.production_ai.use",
            "agents.sales_ai.use",
            "agents.finance_ai.use",
            "agents.marketing_ai.use"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Production Manager',
        'production_manager',
        'System role template for production workspace access and daily production inputs.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            "operational.forms.submit",
            "agents.production_ai.use"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Sales Manager',
        'sales_manager',
        'System role template for sales workspace access and daily sales inputs.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            "operational.forms.submit",
            "agents.sales_ai.use"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Finance Manager',
        'finance_manager',
        'System role template for finance workspace access and daily finance inputs.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            "operational.forms.submit",
            "agents.finance_ai.use"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Marketing Manager',
        'marketing_manager',
        'System role template for marketing workspace access and daily marketing inputs.',
        '[
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            "operational.forms.submit",
            "agents.marketing_ai.use"
        ]'::jsonb,
        TRUE
    ),
    (
        NULL,
        'Employee',
        'employee',
        'System role template for restricted employee access to assigned operational workspaces.',
        '[
            "ai.chat",
            "memory.read",
            "departments.read"
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
