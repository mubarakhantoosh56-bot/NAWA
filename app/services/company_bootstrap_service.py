"""Company bootstrap service for SaaS registration workflows."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

import asyncpg

from app.repositories.company_repository import CompanyRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.department_service import DepartmentService

RowDict = dict[str, object]


class CompanyBootstrapService:
    """Orchestrates atomic creation of a company and its owner membership."""

    def __init__(self, db: asyncpg.Pool | asyncpg.Connection) -> None:
        """Initialize the service with an asyncpg pool or connection."""
        self.db = db

    async def register_company_owner(
        self,
        company_slug: str,
        company_name: str,
        owner_email: str,
        owner_full_name: str,
        owner_password_hash: str | None = None,
        company_plan: str = "mvp",
        company_metadata: dict[str, object] | None = None,
    ) -> RowDict:
        """Register a new company and assign the owner system role.

        Raises:
            ValueError: If the company slug already exists, the owner role is
                missing, or an owner membership already exists.
        """
        async with self._transaction_connection() as conn:
            company_repo = CompanyRepository(conn)
            user_repo = UserRepository(conn)
            role_repo = RoleRepository(conn)
            membership_repo = MembershipRepository(conn)

            if await company_repo.slug_exists(company_slug):
                raise ValueError("duplicate company slug")

            try:
                company = await company_repo.create_company(
                    slug=company_slug,
                    name=company_name,
                    plan=company_plan,
                    metadata=company_metadata,
                )
            except asyncpg.UniqueViolationError as exc:
                raise ValueError("duplicate company slug") from exc

            user = await user_repo.get_by_email(owner_email)
            if user is None:
                user = await user_repo.create_user(
                    email=owner_email,
                    full_name=owner_full_name,
                    password_hash=owner_password_hash,
                )

            owner_role = await role_repo.get_system_role_by_slug("owner")
            if owner_role is None:
                raise ValueError("missing owner role")

            existing_membership = await membership_repo.get_active_membership(
                company_id=company["id"],
                user_id=user["id"],
            )
            if existing_membership is not None:
                raise ValueError("existing membership conflict")

            membership = await membership_repo.create_membership(
                company_id=company["id"],
                user_id=user["id"],
                role_id=owner_role["id"],
                status="active",
                accepted_at=datetime.now(timezone.utc),
                created_by_user_id=user["id"],
            )

            try:
                department_service = DepartmentService(conn)
                departments = await department_service.create_default_departments(
                    company_id=company["id"],
                    created_by_user_id=user["id"],
                )
            except ValueError as exc:
                raise ValueError("department bootstrap failed") from exc

            return {
                "company": company,
                "user": self._without_password_hash(user),
                "role": owner_role,
                "membership": membership,
                "departments": departments,
            }

    @asynccontextmanager
    async def _transaction_connection(self) -> AsyncIterator[asyncpg.Connection]:
        if isinstance(self.db, asyncpg.Pool):
            async with self.db.acquire() as conn:
                async with conn.transaction():
                    yield conn
            return

        async with self.db.transaction():
            yield self.db

    @staticmethod
    def _without_password_hash(user: RowDict) -> RowDict:
        safe_user = dict(user)
        safe_user.pop("password_hash", None)
        return safe_user
