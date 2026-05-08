import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.security import create_token

client = TestClient(app)


@patch("app.api.chat.ai_engine.chat")
def test_valid_jwt_matching_company_id_succeeds(mock_chat):
    """Test 1: Valid JWT + matching company_id reaches service, returns 200."""
    mock_chat.return_value = {"ok": True}

    company_id = "company_123"
    user_id = "user_456"
    token = create_token(company_id=company_id, user_id=user_id)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company_id": company_id,
        "session_id": "session_789",
        "message": "Hello",
    }

    response = client.post("/ai/chat", json=payload, headers=headers)

    # Auth passes, route reaches service
    assert response.status_code == 200, f"Got {response.status_code}: {response.json()}"
    # Service was called
    mock_chat.assert_called_once()


@patch("app.api.chat.ai_engine.chat")
def test_valid_jwt_mismatched_company_id_returns_403(mock_chat):
    """Test 2: Valid JWT + mismatched company_id returns 403 (before service call)."""
    company_id = "company_123"
    user_id = "user_456"
    token = create_token(company_id=company_id, user_id=user_id)

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "company_id": "company_999",  # Different from token
        "session_id": "session_789",
        "message": "Hello",
    }

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
