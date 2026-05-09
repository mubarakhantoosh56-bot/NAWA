-- AIMX SaaS foundation indexes draft.
-- Review-only migration: do not execute until approved.

CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_slug_active_unique
    ON companies (slug)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_active_unique
    ON users (email)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_departments_company_slug_active_unique
    ON departments (company_id, slug)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_system_slug_active_unique
    ON roles (slug)
    WHERE company_id IS NULL
      AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_company_slug_active_unique
    ON roles (company_id, slug)
    WHERE company_id IS NOT NULL
      AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_memberships_company_user_company_active_unique
    ON memberships (company_id, user_id)
    WHERE department_id IS NULL
      AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_memberships_company_user_department_active_unique
    ON memberships (company_id, user_id, department_id)
    WHERE department_id IS NOT NULL
      AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_memberships_company_user_active
    ON memberships (company_id, user_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_memberships_company_role_active
    ON memberships (company_id, role_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_memberships_company_department_active
    ON memberships (company_id, department_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_departments_company_active
    ON departments (company_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_roles_company_active
    ON roles (company_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_company_user_active
    ON refresh_tokens (company_id, user_id)
    WHERE revoked_at IS NULL
      AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family_active
    ON refresh_tokens (family_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_active
    ON refresh_tokens (expires_at)
    WHERE revoked_at IS NULL
      AND deleted_at IS NULL;
