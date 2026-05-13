"""Auth runtime service for register and login internals."""

import hashlib
import hmac
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator
from uuid import UUID, uuid4

import asyncpg

from app.core.config import settings
from app.core.passwords import hash_password, verify_password
from app.core.security import create_token
from app.repositories.company_repository import CompanyRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.company_bootstrap_service import CompanyBootstrapService

RowDict = dict[str, object]


class AuthService:
    """Coordinates MVP register and login auth internals."""

    def __init__(
        self,
        db: asyncpg.Pool | asyncpg.Connection,
        access_token_hours: int = 24,
        refresh_token_days: int = 30,
    ) -> None:
        """Initialize the auth service with database and token lifetimes."""
        self.db = db
        self.access_token_hours = access_token_hours
        self.refresh_token_days = refresh_token_days

    async def register(
        self,
        company_slug: str,
        company_name: str,
        owner_email: str,
        owner_full_name: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RowDict:
        """Register a company owner and return safe auth payload fields."""
        normalized_slug = self._normalize_slug(company_slug)
        normalized_email = self._normalize_email(owner_email)
        password_hash = hash_password(password)

        await self._validate_existing_user_for_register(
            email=normalized_email,
            password=password,
        )

        bootstrap = CompanyBootstrapService(self.db)
        try:
            bootstrap_result = await bootstrap.register_company_owner(
                company_slug=normalized_slug,
                company_name=company_name.strip(),
                owner_email=normalized_email,
                owner_full_name=owner_full_name.strip(),
                owner_password_hash=password_hash,
            )
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

        company = bootstrap_result["company"]
        user = bootstrap_result["user"]
        membership = bootstrap_result["membership"]

        tokens = await self._issue_tokens(
            company_id=company["id"],
            user_id=user["id"],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            **tokens,
            "company": company,
            "user": self._without_password_hash(user),
            "membership": membership,
        }

    async def login(
        self,
        email: str,
        password: str,
        company_slug: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RowDict:
        """Authenticate a user for one company and return safe auth payload fields."""
        normalized_email = self._normalize_email(email)
        normalized_slug = self._normalize_slug(company_slug)

        async with self._connection() as conn:
            company_repo = CompanyRepository(conn)
            user_repo = UserRepository(conn)
            membership_repo = MembershipRepository(conn)

            user = await user_repo.get_by_email(normalized_email)
            if user is None or not self._verify_user_password(password, user):
                raise ValueError("invalid email, password, or company")

            company = await company_repo.get_by_slug(normalized_slug)
            if company is None:
                raise ValueError("invalid email, password, or company")

            membership = await membership_repo.get_active_membership(
                company_id=company["id"],
                user_id=user["id"],
            )
            if membership is None:
                raise ValueError("invalid email, password, or company")

            await user_repo.record_login(user_id=user["id"])

        tokens = await self._issue_tokens(
            company_id=company["id"],
            user_id=user["id"],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            **tokens,
            "company": company,
            "user": self._without_password_hash(user),
            "membership": membership,
        }

    async def get_current_context(self, company_id: str, user_id: str) -> RowDict:
        """Return the authenticated user's active company context."""
        try:
            company_uuid = UUID(company_id)
            user_uuid = UUID(user_id)
        except ValueError as exc:
            raise ValueError("invalid authenticated context") from exc

        async with self._connection() as conn:
            company_repo = CompanyRepository(conn)
            user_repo = UserRepository(conn)
            membership_repo = MembershipRepository(conn)
            role_repo = RoleRepository(conn)

            company = await company_repo.get_by_id(company_uuid)
            if company is None:
                raise ValueError("invalid authenticated context")

            user = await user_repo.get_by_id(user_uuid)
            if user is None:
                raise ValueError("invalid authenticated context")

            membership = await membership_repo.get_active_membership(
                company_id=company_uuid,
                user_id=user_uuid,
            )
            if membership is None:
                raise ValueError("invalid authenticated context")

            role = await role_repo.get_accessible_role_by_id(
                company_id=company_uuid,
                role_id=membership["role_id"],
            )
            if role is None:
                raise ValueError("invalid authenticated context")

        return {
            "company": company,
            "user": self._without_password_hash(user),
            "membership": membership,
            "role": role,
        }

    async def _validate_existing_user_for_register(self, email: str, password: str) -> None:
        async with self._connection() as conn:
            user_repo = UserRepository(conn)
            existing_user = await user_repo.get_by_email(email)

        if existing_user is None:
            return

        if not self._verify_user_password(password, existing_user):
            raise ValueError("invalid registration credentials")

    async def _issue_tokens(
        self,
        company_id: UUID,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RowDict:
        raw_refresh_token = secrets.token_urlsafe(64)
        refresh_token_hash = self._hash_refresh_token(raw_refresh_token)
        family_id = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_days)

        async with self._connection() as conn:
            refresh_repo = RefreshTokenRepository(conn)
            refresh_token = await refresh_repo.create_refresh_token(
                company_id=company_id,
                user_id=user_id,
                token_hash=refresh_token_hash,
                family_id=family_id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return {
            "access_token": create_token(
                company_id=str(company_id),
                user_id=str(user_id),
                expires_in_hours=self.access_token_hours,
            ),
            "refresh_token": raw_refresh_token,
            "refresh_token_id": refresh_token["id"],
            "refresh_token_expires_at": refresh_token["expires_at"],
            "token_type": "bearer",
        }

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[asyncpg.Connection]:
        if isinstance(self.db, asyncpg.Pool):
            async with self.db.acquire() as conn:
                yield conn
            return

        yield self.db

    @staticmethod
    def _hash_refresh_token(refresh_token: str) -> str:
        digest = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            refresh_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest

    @staticmethod
    def _normalize_email(email: str) -> str:
        normalized = email.strip().lower()
        if not normalized:
            raise ValueError("email is required")
        return normalized

    @staticmethod
    def _normalize_slug(slug: str) -> str:
        normalized = slug.strip().lower()
        if not normalized:
            raise ValueError("company slug is required")
        return normalized

    @staticmethod
    def _verify_user_password(password: str, user: RowDict) -> bool:
        password_hash = user.get("password_hash")
        if not isinstance(password_hash, str):
            return False
        return verify_password(password, password_hash)

    @staticmethod
    def _without_password_hash(user: RowDict) -> RowDict:
        safe_user = dict(user)
        safe_user.pop("password_hash", None)
        return safe_user
