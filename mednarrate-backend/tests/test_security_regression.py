import pytest
from httpx import AsyncClient
import io
import os
from app.core.config import settings
from unittest.mock import patch

@pytest.fixture
async def auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "sec1@example.com", "password": "StrongP@ssword1", "full_name": "Sec User 1"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "sec1@example.com", "password": "StrongP@ssword1"}
    )
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

@pytest.fixture
async def other_auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "sec2@example.com", "password": "StrongP@ssword1", "full_name": "Sec User 2"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "sec2@example.com", "password": "StrongP@ssword1"}
    )
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

async def test_malicious_filename_crlf_injection(client: AsyncClient, auth_headers):
    """Verify that CRLF and path traversals in filenames are stripped."""
    malicious_names = [
        "evil\\r\\nX-Test: injected.pdf",
        "../../secret.pdf",
        "..\\\\..\\\\secret.pdf",
        "quoted\"name.pdf",
        "<test>.pdf",
    ]
    
    for m_name in malicious_names:
        file_content = b"%PDF-1.4 dummy"
        files = {"file": (m_name, file_content, "application/pdf")}
        data = {
            "title": "Malicious Test",
            "report_date": "2024-01-01",
            "report_type": "blood"
        }
        
        resp = await client.post("/api/v1/reports/upload", headers=auth_headers, files=files, data=data)
        assert resp.status_code == 201
        
        report_id = resp.json()["id"]
        # Fetch the report to check the stored filename
        get_resp = await client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
        stored_filename = get_resp.json()["file_name"]
        
        # Ensure it was sanitized
        assert "\\r" not in stored_filename
        assert "\\n" not in stored_filename
        assert ".." not in stored_filename
        assert "/" not in stored_filename
        assert "<" not in stored_filename

async def test_cross_user_analysis_authorization(client: AsyncClient, auth_headers, other_auth_headers):
    """Verify that a user cannot access another user's analysis."""
    # User 1 uploads
    files = {"file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    data = {"title": "Auth Test", "report_date": "2024-01-01", "report_type": "blood"}
    resp = await client.post("/api/v1/reports/upload", headers=auth_headers, files=files, data=data)
    assert resp.status_code == 201
    report_id = resp.json()["id"]
    
    # User 2 attempts to get analysis
    get_analysis_resp = await client.get(f"/api/v1/reports/{report_id}/analysis", headers=other_auth_headers)
    assert get_analysis_resp.status_code == 403



@pytest.fixture
def mock_llm_client_fallback():
    # Force auto mode and disable keys to trigger fallback
    original_provider = getattr(settings, "PRIMARY_LLM_PROVIDER", None)
    settings.PRIMARY_LLM_PROVIDER = "fallback"
    yield
    settings.PRIMARY_LLM_PROVIDER = original_provider

async def test_chat_fallback_behavior(client: AsyncClient, auth_headers, mock_llm_client_fallback):
    """
    Test that when the LLM provider fails or is unconfigured (falling back to FallbackAIProvider),
    a chat request does not return a medical report summary template, but rather a safe unavailable message.
    """
    # 1. Create a chat session
    session_resp = await client.post(
        "/api/v1/chat/sessions", headers=auth_headers,
        json={"title": "Test Chat", "report_id": None}
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    # 2. Send "hello" message
    chat_resp = await client.post(
        f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_headers,
        json={"content": "hello"}
    )
    assert chat_resp.status_code == 200
    resp_data = chat_resp.json()

    # 3. Verify response is the safe unavailable message, NOT a report template
    assistant_msg = resp_data["message"]["content"]
    assert "What Your Report Says" not in assistant_msg
    assert "Your blood report data has been processed" not in assistant_msg
    assert assistant_msg == "AI service is temporarily unavailable. Please try again."
