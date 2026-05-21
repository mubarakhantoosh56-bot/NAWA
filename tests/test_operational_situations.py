import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.api.situations import get_operational_situation_service
from app.core.security import create_token
from app.main import app
from app.services.operational_situation_service import OperationalSituationService


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


class _OperationalSituationServiceStub:
    def __init__(self) -> None:
        self.group_company_id: UUID | None = None
        self.list_company_id: UUID | None = None
        self.detail_company_id: UUID | None = None
        self.situation = _situation_row(company_id=uuid4())

    async def group_recent_events(self, **kwargs) -> dict:
        self.group_company_id = kwargs["company_id"]
        now = datetime.now(timezone.utc)
        situation = _situation_row(company_id=kwargs["company_id"])
        return {
            "created_situations": [situation],
            "created_count": 1,
            "duplicate_clusters_skipped": 0,
            "analyzed_event_count": 2,
            "window_start": now - timedelta(hours=72),
            "window_end": now,
        }

    async def list_situations(self, **kwargs) -> list[dict]:
        self.list_company_id = kwargs["company_id"]
        return [_situation_row(company_id=kwargs["company_id"])]

    async def get_situation(self, **kwargs) -> dict:
        self.detail_company_id = kwargs["company_id"]
        situation = _situation_row(company_id=kwargs["company_id"])
        situation["events"] = [_event_row(company_id=kwargs["company_id"])]
        return situation


class _FakeSituationRepository:
    def __init__(self, events: list[dict], duplicate: bool = False) -> None:
        self.events = events
        self.duplicate = duplicate
        self.created: list[dict] = []
        self.links: list[dict] = []

    async def list_recent_events_for_grouping(self, **kwargs) -> list[dict]:
        return self.events

    async def find_active_situations_for_events(self, **kwargs) -> list[dict]:
        if self.duplicate:
            return [{"id": uuid4(), "company_id": kwargs["company_id"]}]
        return []

    async def create_situation(self, **kwargs) -> dict:
        now = datetime.now(timezone.utc)
        row = {
            "id": uuid4(),
            "created_at": now,
            "updated_at": now,
            **kwargs,
        }
        self.created.append(row)
        return row

    async def link_situation_events(self, **kwargs) -> None:
        self.links.append(kwargs)

    async def list_situations(self, **kwargs) -> list[dict]:
        return []

    async def get_situation(self, **kwargs) -> dict | None:
        return None

    async def list_situation_events(self, **kwargs) -> list[dict]:
        return []


class _FakeDepartmentRepository:
    async def get_by_id(self, company_id: UUID, department_id: UUID) -> dict | None:
        return {"id": department_id, "company_id": company_id}


def test_group_situations_endpoint_uses_jwt_company_id():
    company_id = uuid4()
    user_id = uuid4()
    token = create_token(company_id=str(company_id), user_id=str(user_id))
    service = _OperationalSituationServiceStub()
    app.dependency_overrides[get_operational_situation_service] = lambda: service

    try:
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(
                return_value=_PermissionAuthService(["operational.forms.read"]),
            ),
        ):
            response = client.post(
                "/situations/group",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.json()
    assert service.group_company_id == company_id
    assert response.json()["created_count"] == 1


def test_list_and_get_situations_return_jwt_company_scope():
    company_id = uuid4()
    user_id = uuid4()
    token = create_token(company_id=str(company_id), user_id=str(user_id))
    service = _OperationalSituationServiceStub()
    app.dependency_overrides[get_operational_situation_service] = lambda: service

    try:
        with patch(
            "app.core.permissions._get_permission_auth_service",
            new=AsyncMock(
                return_value=_PermissionAuthService(["operational.forms.read"]),
            ),
        ):
            list_response = client.get(
                "/situations",
                headers={"Authorization": f"Bearer {token}"},
            )
            detail_response = client.get(
                f"/situations/{uuid4()}",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert list_response.status_code == 200, list_response.json()
    assert detail_response.status_code == 200, detail_response.json()
    assert list_response.json()["situations"][0]["company_id"] == str(company_id)
    assert detail_response.json()["company_id"] == str(company_id)
    assert detail_response.json()["events"][0]["company_id"] == str(company_id)


def test_grouping_uses_structured_fields_not_titles_or_summaries():
    company_id = uuid4()
    now = datetime.now(timezone.utc)
    events = [
        _event_row(
            company_id=company_id,
            title="Same display label",
            summary="Same display summary",
            category="feed_shortage",
            event_type="operational.dairtna.feed_shortage",
            event_timestamp=now - timedelta(hours=2),
        ),
        _event_row(
            company_id=company_id,
            title="Same display label",
            summary="Same display summary",
            category="medicine_delay",
            event_type="operational.dairtna.medicine_delay",
            event_timestamp=now - timedelta(hours=1),
        ),
    ]
    service = OperationalSituationService(db=None)
    repo = _FakeSituationRepository(events)
    service.situation_repo = repo
    service.department_repo = _FakeDepartmentRepository()

    result = asyncio.run(service.group_recent_events(company_id=company_id))

    assert result["created_count"] == 0
    assert repo.created == []


def test_grouping_creates_structured_cluster_and_skips_duplicates():
    company_id = uuid4()
    now = datetime.now(timezone.utc)
    events = [
        _event_row(
            company_id=company_id,
            category="production_delay",
            event_type="operational.dairtna.production_delay",
            priority="high",
            event_timestamp=now - timedelta(hours=4),
        ),
        _event_row(
            company_id=company_id,
            category="production_delay",
            event_type="operational.dairtna.production_delay",
            priority="high",
            event_timestamp=now - timedelta(hours=2),
        ),
    ]
    service = OperationalSituationService(db=None)
    repo = _FakeSituationRepository(events)
    service.situation_repo = repo
    service.department_repo = _FakeDepartmentRepository()

    result = asyncio.run(service.group_recent_events(company_id=company_id))

    assert result["created_count"] == 1
    assert repo.created[0]["situation_type"] == "bottleneck"
    assert repo.created[0]["severity"] == "high"
    assert repo.created[0]["source_type"] == "manual_rule"
    assert len(repo.links[0]["event_links"]) == 2

    duplicate_service = OperationalSituationService(db=None)
    duplicate_repo = _FakeSituationRepository(events, duplicate=True)
    duplicate_service.situation_repo = duplicate_repo
    duplicate_service.department_repo = _FakeDepartmentRepository()

    duplicate_result = asyncio.run(duplicate_service.group_recent_events(company_id=company_id))

    assert duplicate_result["created_count"] == 0
    assert duplicate_result["duplicate_clusters_skipped"] == 1


def _situation_row(company_id: UUID) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "company_id": company_id,
        "title": "Bottleneck: Production Delay cluster (2 events)",
        "summary": "Rule-based grouping found 2 related operational events.",
        "situation_type": "bottleneck",
        "severity": "high",
        "status": "active",
        "time_window_start": now - timedelta(hours=3),
        "time_window_end": now,
        "department_id": None,
        "detection_method": "rule_based",
        "source_type": "manual_rule",
        "event_count": 2,
        "created_at": now,
        "updated_at": now,
    }


def _event_row(
    *,
    company_id: UUID,
    title: str = "Production Delay",
    summary: str = "Reference event",
    category: str = "production_delay",
    event_type: str = "operational.dairtna.production_delay",
    priority: str = "watch",
    event_timestamp: datetime | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "company_id": company_id,
        "department_id": None,
        "created_by_user_id": uuid4(),
        "event_type": event_type,
        "category": category,
        "priority": priority,
        "title": title,
        "summary": summary,
        "event_timestamp": event_timestamp or now,
        "source_type": "manual",
        "source_ref": None,
        "payload": {},
        "metadata": {},
        "created_at": now,
        "updated_at": now,
    }
