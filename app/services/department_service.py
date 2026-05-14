"""Department service for tenant-scoped department runtime internals."""

import re
from uuid import UUID

import asyncpg

from app.repositories.department_repository import DepartmentRepository

RowDict = dict[str, object]

ALLOWED_DEPARTMENT_TYPES = {
    "finance_ai",
    "sales_ai",
    "hr_ai",
    "marketing_ai",
    "warehouse_ai",
    "production_ai",
    "operations_ai",
    "custom",
}

DEFAULT_DEPARTMENTS = [
    ("Finance", "finance_ai"),
    ("Sales", "sales_ai"),
    ("HR", "hr_ai"),
    ("Marketing", "marketing_ai"),
    ("Warehouse", "warehouse_ai"),
    ("Production", "production_ai"),
    ("Operations", "operations_ai"),
]


class DepartmentService:
    """Business logic for tenant-scoped departments."""

    def __init__(self, db: asyncpg.Connection | asyncpg.Pool) -> None:
        """Initialize the service with an asyncpg connection or pool."""
        self.department_repo = DepartmentRepository(db)

    async def create_default_departments(
        self,
        company_id: UUID,
        created_by_user_id: UUID | None = None,
    ) -> list[RowDict]:
        """Create missing default departments for one tenant."""
        departments = []
        for name, department_type in DEFAULT_DEPARTMENTS:
            slug = self.normalize_slug(name)
            existing_department = await self.department_repo.get_by_slug(
                company_id=company_id,
                slug=slug,
            )
            if existing_department is not None:
                departments.append(existing_department)
                continue

            department = await self.create_department(
                company_id=company_id,
                name=name,
                department_type=department_type,
                created_by_user_id=created_by_user_id,
            )
            departments.append(department)

        return departments

    async def list_departments(self, company_id: UUID) -> list[RowDict]:
        """Return active departments for one tenant."""
        return await self.department_repo.list_by_company(company_id=company_id)

    async def create_department(
        self,
        company_id: UUID,
        name: str,
        department_type: str,
        description: str | None = None,
        ai_agent_enabled: bool = False,
        ai_agent_config: dict[str, object] | None = None,
        created_by_user_id: UUID | None = None,
    ) -> RowDict:
        """Create a validated department in one tenant."""
        normalized_name = self._normalize_name(name)
        normalized_slug = self.normalize_slug(normalized_name)
        normalized_type = self.validate_department_type(department_type)

        if await self.department_repo.slug_exists(company_id, normalized_slug):
            raise ValueError("duplicate department slug")

        try:
            return await self.department_repo.create_department(
                company_id=company_id,
                name=normalized_name,
                slug=normalized_slug,
                department_type=normalized_type,
                description=description,
                ai_agent_enabled=ai_agent_enabled,
                ai_agent_config=ai_agent_config,
                created_by_user_id=created_by_user_id,
            )
        except asyncpg.UniqueViolationError as exc:
            raise ValueError("duplicate department slug") from exc

    async def update_department(
        self,
        company_id: UUID,
        department_id: UUID,
        name: str | None = None,
        description: str | None = None,
        department_type: str | None = None,
        ai_agent_enabled: bool | None = None,
        ai_agent_config: dict[str, object] | None = None,
        updated_by_user_id: UUID | None = None,
    ) -> RowDict | None:
        """Update a validated department in one tenant."""
        normalized_name = self._normalize_name(name) if name is not None else None
        normalized_slug = self.normalize_slug(normalized_name) if normalized_name else None
        normalized_type = (
            self.validate_department_type(department_type)
            if department_type is not None
            else None
        )

        if normalized_slug is not None:
            existing_department = await self.department_repo.get_by_slug(
                company_id=company_id,
                slug=normalized_slug,
            )
            if existing_department is not None and existing_department["id"] != department_id:
                raise ValueError("duplicate department slug")

        try:
            return await self.department_repo.update_department(
                company_id=company_id,
                department_id=department_id,
                name=normalized_name,
                slug=normalized_slug,
                description=description,
                department_type=normalized_type,
                ai_agent_enabled=ai_agent_enabled,
                ai_agent_config=ai_agent_config,
                updated_by_user_id=updated_by_user_id,
            )
        except asyncpg.UniqueViolationError as exc:
            raise ValueError("duplicate department slug") from exc

    async def soft_delete_department(
        self,
        company_id: UUID,
        department_id: UUID,
        deleted_by_user_id: UUID,
    ) -> bool:
        """Soft-delete a department in one tenant."""
        return await self.department_repo.soft_delete_department(
            company_id=company_id,
            department_id=department_id,
            deleted_by_user_id=deleted_by_user_id,
        )

    @staticmethod
    def validate_department_type(department_type: str) -> str:
        """Validate and return a supported department type."""
        normalized_type = department_type.strip().lower()
        if normalized_type not in ALLOWED_DEPARTMENT_TYPES:
            raise ValueError("invalid department type")
        return normalized_type

    @staticmethod
    def normalize_slug(value: str) -> str:
        """Normalize display text into a URL-safe department slug."""
        slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
        if not slug:
            raise ValueError("department slug is required")
        return slug

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("department name is required")
        return normalized_name
