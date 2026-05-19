"""MVP role and permission helpers for NAWA operational workspaces."""

from __future__ import annotations


CEO_WORKSPACE_PERMISSION = "workspace.ceo"
OPERATIONAL_FORM_SUBMIT_PERMISSION = "operational.forms.submit"
OPERATIONAL_FORM_READ_PERMISSION = "operational.forms.read"
INTEGRATIONS_READ_PERMISSION = "integrations.read"
INTEGRATIONS_INGEST_PERMISSION = "integrations.ingest"

DEPARTMENT_AGENT_PERMISSIONS = {
    "production_ai": "agents.production_ai.use",
    "sales_ai": "agents.sales_ai.use",
    "finance_ai": "agents.finance_ai.use",
    "marketing_ai": "agents.marketing_ai.use",
    "operations_ai": "agents.operations_ai.use",
    "warehouse_ai": "agents.warehouse_ai.use",
    "hr_ai": "agents.hr_ai.use",
}

OPERATIONAL_ROLE_TEMPLATES: dict[str, dict[str, object]] = {
    "ceo": {
        "name": "CEO",
        "description": "Executive operational intelligence across departments.",
        "permissions": [
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            CEO_WORKSPACE_PERMISSION,
            OPERATIONAL_FORM_READ_PERMISSION,
            OPERATIONAL_FORM_SUBMIT_PERMISSION,
            INTEGRATIONS_READ_PERMISSION,
            "agents.production_ai.use",
            "agents.sales_ai.use",
            "agents.finance_ai.use",
            "agents.marketing_ai.use",
        ],
    },
    "production_manager": {
        "name": "Production Manager",
        "description": "Production workspace access and daily production inputs.",
        "permissions": [
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            OPERATIONAL_FORM_SUBMIT_PERMISSION,
            "agents.production_ai.use",
        ],
    },
    "sales_manager": {
        "name": "Sales Manager",
        "description": "Sales workspace access and daily sales inputs.",
        "permissions": [
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            OPERATIONAL_FORM_SUBMIT_PERMISSION,
            "agents.sales_ai.use",
        ],
    },
    "finance_manager": {
        "name": "Finance Manager",
        "description": "Finance workspace access and daily finance inputs.",
        "permissions": [
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            OPERATIONAL_FORM_SUBMIT_PERMISSION,
            "agents.finance_ai.use",
        ],
    },
    "marketing_manager": {
        "name": "Marketing Manager",
        "description": "Marketing workspace access and daily marketing inputs.",
        "permissions": [
            "ai.chat",
            "memory.read",
            "memory.write",
            "departments.read",
            "files.read",
            "files.upload",
            OPERATIONAL_FORM_SUBMIT_PERMISSION,
            "agents.marketing_ai.use",
        ],
    },
    "employee": {
        "name": "Employee",
        "description": "Restricted employee access to assigned operational workspaces.",
        "permissions": [
            "ai.chat",
            "memory.read",
            "departments.read",
        ],
    },
}


def visible_department_types(permissions: list[object]) -> set[str] | None:
    """Return visible department types, or None when the user can see all."""
    normalized = {item.strip() for item in permissions if isinstance(item, str) and item.strip()}
    if "*" in normalized or CEO_WORKSPACE_PERMISSION in normalized:
        return None

    visible = {
        department_type
        for department_type, permission in DEPARTMENT_AGENT_PERMISSIONS.items()
        if permission in normalized
    }
    return visible
