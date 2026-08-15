import pytest
from httpx import AsyncClient

@pytest.fixture
async def auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "rag@example.com", "password": "StrongP@ssword1", "full_name": "RAG User"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "rag@example.com", "password": "StrongP@ssword1"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

async def test_create_chat_session(client: AsyncClient, auth_headers):
    # Setup report
    resp = await client.post(
        "/api/v1/reports/upload", 
        headers=auth_headers, 
        files={"file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")},
        data={"title": "Test Report", "report_date": "2024-01-01", "report_type": "blood"}
    )
    report_id = resp.json()["id"]

    # Create chat session
    chat_resp = await client.post(
        "/api/v1/chat/sessions",
        headers=auth_headers,
        json={"report_id": report_id, "title": "Chat"}
    )
    assert chat_resp.status_code == 201
    assert chat_resp.json()["report_id"] == report_id

async def test_chat_session_ownership(client: AsyncClient, auth_headers):
    # Setup session
    resp = await client.post(
        "/api/v1/chat/sessions",
        headers=auth_headers,
        json={"report_id": None, "title": "Chat"}
    )
    session_id = resp.json()["id"]

    # Other user
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "otherrag@example.com", "password": "StrongP@ssword1", "full_name": "Other RAG User"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "otherrag@example.com", "password": "StrongP@ssword1"}
    )
    other_token = login_resp.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Attempt to send message
    msg_resp = await client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers=other_headers,
        json={"content": "Hello"}
    )
    assert msg_resp.status_code == 403
