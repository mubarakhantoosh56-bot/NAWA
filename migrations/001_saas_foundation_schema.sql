-- AIMX SaaS foundation schema draft.
-- Review-only migration: do not execute until approved.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(120) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    plan VARCHAR(50) NOT NULL DEFAULT 'mvp',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    password_hash TEXT NULL,
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    external_subject VARCHAR(255) NULL,
    last_login_at TIMESTAMPTZ NULL,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    description TEXT NULL,
    department_type VARCHAR(80) NULL,
    ai_agent_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ai_agent_config JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_departments_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_departments_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_departments_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_departments_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id)
);

COMMENT ON COLUMN departments.department_type IS
    'MVP: allowed values such as finance_ai, hr_ai, marketing_ai, operations_ai, and custom are controlled at the application level.';

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NULL,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    description TEXT NULL,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_system_role BOOLEAN NOT NULL DEFAULT FALSE,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_roles_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_roles_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_roles_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_roles_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id),
    CONSTRAINT chk_roles_permissions_array
        CHECK (jsonb_typeof(permissions) = 'array'),
    CONSTRAINT chk_roles_system_scope
        CHECK (
            (is_system_role = TRUE AND company_id IS NULL)
            OR (is_system_role = FALSE AND company_id IS NOT NULL)
        )
);

CREATE TABLE IF NOT EXISTS memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    department_id UUID NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    invited_by_user_id UUID NULL,
    invited_at TIMESTAMPTZ NULL,
    accepted_at TIMESTAMPTZ NULL,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_memberships_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_memberships_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_memberships_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id),
    CONSTRAINT fk_memberships_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id),
    CONSTRAINT fk_memberships_invited_by_user
        FOREIGN KEY (invited_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_memberships_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_memberships_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_memberships_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id),
    CONSTRAINT chk_memberships_status
        CHECK (status IN ('invited', 'active', 'suspended', 'revoked'))
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    user_id UUID NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    family_id UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,
    replaced_by_token_id UUID NULL,
    ip_address INET NULL,
    user_agent TEXT NULL,

    created_by_user_id UUID NULL,
    updated_by_user_id UUID NULL,
    deleted_by_user_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT fk_refresh_tokens_company
        FOREIGN KEY (company_id)
        REFERENCES companies(id),
    CONSTRAINT fk_refresh_tokens_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),
    CONSTRAINT fk_refresh_tokens_replaced_by_token
        FOREIGN KEY (replaced_by_token_id)
        REFERENCES refresh_tokens(id),
    CONSTRAINT fk_refresh_tokens_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_refresh_tokens_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    CONSTRAINT fk_refresh_tokens_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id),
    CONSTRAINT chk_refresh_tokens_expiry
        CHECK (expires_at > issued_at)
);

ALTER TABLE companies
    ADD CONSTRAINT fk_companies_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    ADD CONSTRAINT fk_companies_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    ADD CONSTRAINT fk_companies_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id);

ALTER TABLE users
    ADD CONSTRAINT fk_users_created_by_user
        FOREIGN KEY (created_by_user_id)
        REFERENCES users(id),
    ADD CONSTRAINT fk_users_updated_by_user
        FOREIGN KEY (updated_by_user_id)
        REFERENCES users(id),
    ADD CONSTRAINT fk_users_deleted_by_user
        FOREIGN KEY (deleted_by_user_id)
        REFERENCES users(id);
