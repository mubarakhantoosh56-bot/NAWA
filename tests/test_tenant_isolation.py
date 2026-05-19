import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.main import app
from app.core.security import create_token

client = TestClient(app)


def _chat_response(company_id: str, session_id: str) -> dict:
    return {
        "ceo_text": "ok",
        "logic_json": {},
        "followup_question": None,
        "meta": {
            "company_id": company_id,
            "session_id": session_id,
            "context": {},
            "parse_ok": True,
            "memory_injected": False,
            "events_count": 0,
        },
    }


class _PermissionAuthService:
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
                "permissions": ["ai.chat", "workspace.ceo"],
            },
        }


@patch("app.api.chat.ai_engine.chat")
def test_valid_jwt_matching_company_id_succeeds(mock_chat):
    """Test 1: Valid JWT + matching company_id reaches service, returns 200."""
    company_id = str(uuid4())
    session_id = "session_789"
    user_id = str(uuid4())
    mock_chat.return_value = _chat_response(company_id=company_id, session_id=session_id)
    token = create_token(company_id=company_id, user_id=user_id)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company_id": company_id,
        "session_id": session_id,
        "message": "Hello",
    }

    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_PermissionAuthService()),
    ):
        response = client.post("/ai/chat", json=payload, headers=headers)

    # Auth passes, route reaches service
    assert response.status_code == 200, f"Got {response.status_code}: {response.json()}"
    # Service was called
    mock_chat.assert_called_once()


@patch("app.api.chat.ai_engine.chat")
def test_valid_jwt_mismatched_company_id_returns_403(mock_chat):
    """Test 2: Valid JWT + mismatched company_id returns 403 (before service call)."""
    company_id = str(uuid4())
    user_id = str(uuid4())
    token = create_token(company_id=company_id, user_id=user_id)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company_id": str(uuid4()),  # Different from token
        "session_id": "session_789",
        "message": "Hello",
    }

    with patch(
        "app.core.permissions._get_permission_auth_service",
        new=AsyncMock(return_value=_PermissionAuthService()),
    ):
        response = client.post("/ai/chat", json=payload, headers=headers)

    # Company isolation blocks request before reaching service
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    # Service never called
    mock_chat.assert_not_called()


def test_no_authorization_header_returns_401():
    """Test 3: No Authorization header returns 401."""
    payload = {
        "company_id": "company_123",
        "session_id": "session_789",
        "message": "Hello",
    }

    response = client.post("/ai/chat", json=payload)

    # Auth required
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_health_returns_ok():
    """Health endpoint is public and lightweight."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
