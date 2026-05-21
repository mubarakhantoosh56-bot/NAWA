import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.api.operational_events import get_operational_event_service
from app.main import app
from app.core.security import create_token
from app.services.operational_event_service import OperationalEventService


client = TestClient(app)


class _PermissionAuthService:
    def __init__(self, permissions: list[str]) -> None:
        self.permissions = permissions

    async def get_current_context(self, company_id: str, user_id: str) -> dict:
        return {
            "company": {"id": company_id},
            "user": {"id": user_id},
            "membership": {
                "id": uuid4(),
                "company_id": company_id,
                "user_id": user_id,
                "role_id": uuid4(),
                "status": "active",
            },
            "role": {
                "id": uuid4(),
                "slug": "ceo",
                "permissions": self.permissions,
            },
        }


class _OperationalEventServiceStub:
    def __init__(self) -> None:
        self.created: dict | None = None

    async def create_event(self, **kwargs) -> dict:
        self.created = kwargs
        now = datetime.now(timezone.utc)
        return {
            "id": uuid4(),
            "company_id": kwargs["company_id"],
            "department_id": kwargs.get("department_id"),
            "created_by_user_id": kwargs["user_id"],
            "event_type": kwargs["event_type"],
            "category": kwargs["category"],
            "priority": kwargs["priority"],
            "title": kwargs["title"],
            "summary": kwargs["summary"],
            "event_timestamp": kwargs.get("event_timestamp") or now,
            "source_type": kwargs["source_type"],
            "source_ref": kwargs.get("source_ref"),
            "payload": kwargs.get("payload") or {},
            "metadata": kwargs.get("metadata") or {},
            "created_at": now,
            "updated_at": now,
        }

    async def list_events(self, **kwargs) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": uuid4(),
                "company_id": kwargs["company_id"],
                "department_id": kwargs.get("department_id"),
                "created_by_user_id": uuid4(),
                "event_type": "operational.production.issue",
                "category": "issue",
                "priority": "watch",
                "title": "Production delay",
                "summary": "Line 2 delay reported.",
                "event_timestamp": now,
                "source_type": "manual",
                "source_ref": None,
                "payload": {},
                "metadata": {},
                "created_at": now,
                "updated_at": now,
            }
        ]


class _FakeDepartmentRepository:
    def __init__(self, exists: bool = True) -> None:
        self.exists = exists
        self.calls: list[tuple[UUID, UUID]] = []

    async def get_by_id(self, company_id: UUID, department_id: UUID) -> dict | None:
        self.calls.append((company_id, department_id))
        if not self.exists:
            return None
        return {"id": department_id, "company_id": company_id}


class _FakeEventRepository:
    def __init__(self) -> None:
        self.created: dict | None = None
        self.list_filters: dict | None = None

    async def create_event(self, **kwargs) -> dict:
        self.created = kwargs
        return {"id": uuid4(), **kwargs}

    async def list_events(self, **kwargs) -> list[dict]:
        self.list_filters = kwargs
        return []


def test_create_operational_event_uses_jwt_company_id_without_body_company_id():
    company_id = uuid4()
    user_id = uuid4()
    token = create_token(company_id=str(company_id), user_id=str(user_id))
    service = _OperationalEventServiceStub()
    app.dependency_overrides[get_operational_event_service] = lambda: service

    try:
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(
                return_value=_PermissionAuthService(["operational.forms.submit"]),
            ),
        ):
            response = client.post(
                "/operational-events",
                json={
                    "event_type": "operational.production.issue",
                    "category": "issue",
                    "priority": "watch",
                    "title": "Production delay",
                    "summary": "Line 2 delay reported.",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201, response.json()
    assert service.created is not None
    assert service.created["company_id"] == company_id
    assert service.created["user_id"] == user_id


def test_create_operational_event_rejects_mismatched_body_company_id():
    company_id = uuid4()
    user_id = uuid4()
    token = create_token(company_id=str(company_id), user_id=str(user_id))
    service = _OperationalEventServiceStub()
    app.dependency_overrides[get_operational_event_service] = lambda: service

    try:
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(
                return_value=_PermissionAuthService(["operational.forms.submit"]),
            ),
        ):
            response = client.post(
                "/operational-events",
                json={
                    "company_id": str(uuid4()),
                    "event_type": "operational.production.issue",
                    "category": "issue",
                    "priority": "watch",
                    "title": "Production delay",
                    "summary": "Line 2 delay reported.",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.created is None


def test_list_operational_events_requires_read_permission_and_returns_jwt_company_events():
    company_id = uuid4()
    user_id = uuid4()
    token = create_token(company_id=str(company_id), user_id=str(user_id))
    service = _OperationalEventServiceStub()
    app.dependency_overrides[get_operational_event_service] = lambda: service

    try:
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(
                return_value=_PermissionAuthService(["operational.forms.read"]),
            ),
        ):
            response = client.get(
                "/operational-events",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["events"]
    assert payload["events"][0]["company_id"] == str(company_id)


def test_operational_event_service_validates_department_scope():
    company_id = uuid4()
    department_id = uuid4()
    event_repo = _FakeEventRepository()
    service = OperationalEventService(db=None)
    service.event_repo = event_repo
    service.department_repo = _FakeDepartmentRepository(exists=True)

    result = asyncio.run(_async_create_event(service, company_id, department_id))

    assert result["department_id"] == department_id
    assert event_repo.created is not None
    assert event_repo.created["company_id"] == company_id


async def _async_create_event(
    service: OperationalEventService,
    company_id: UUID,
    department_id: UUID,
) -> dict:
    return await service.create_event(
        company_id=company_id,
        user_id=uuid4(),
        department_id=department_id,
        event_type="operational.production.issue",
        category="issue",
        priority="watch",
        title="Production delay",
        summary="Line 2 delay reported.",
    )
