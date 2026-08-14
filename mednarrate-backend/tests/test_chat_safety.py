import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.services.prompts import CHAT_EMERGENCY_RESPONSE, CHAT_REFUSAL_RESPONSE

@pytest.mark.asyncio
async def test_chat_safety_emergency_routing(client: AsyncClient, token_headers: dict, db_session):
    # Create a chat session
    resp = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Test Chat"},
        headers=token_headers
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    # Mock the LLM to return 'emergency'
    with patch("app.api.v1.chat.generate", return_value="emergency"):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "I have severe chest pain"},
            headers=token_headers
        )
        assert resp.status_code == 200
        assert resp.json()["message"]["content"] == CHAT_EMERGENCY_RESPONSE

@pytest.mark.asyncio
async def test_chat_safety_diagnosis_routing(client: AsyncClient, token_headers: dict, db_session):
    # Create a chat session
    resp = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Test Chat"},
        headers=token_headers
    )
    session_id = resp.json()["id"]

    # Mock the LLM to return 'diagnosis'
    with patch("app.api.v1.chat.generate", return_value="diagnosis"):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "Do I have cancer?"},
            headers=token_headers
        )
        assert resp.status_code == 200
        assert resp.json()["message"]["content"] == CHAT_REFUSAL_RESPONSE
