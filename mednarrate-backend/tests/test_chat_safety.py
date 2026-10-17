from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.services.prompts import CHAT_EMERGENCY_RESPONSE, CHAT_REFUSAL_RESPONSE


@pytest.mark.asyncio
async def test_chat_safety_emergency_routing(
    client: AsyncClient, token_headers: dict, db_session
):
    # Create a chat session
    resp = await client.post(
        "/api/v1/chat/sessions", json={"title": "Test Chat"}, headers=token_headers
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    # Mock the LLM to return 'emergency'
    with patch("app.api.v1.chat.generate", return_value="emergency"):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "I have severe chest pain"},
            headers=token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"]["content"] == CHAT_EMERGENCY_RESPONSE


@pytest.mark.asyncio
async def test_chat_safety_diagnosis_routing(
    client: AsyncClient, token_headers: dict, db_session
):
    # Create a chat session
    resp = await client.post(
        "/api/v1/chat/sessions", json={"title": "Test Chat"}, headers=token_headers
    )
    session_id = resp.json()["id"]

    # Mock the LLM to return 'diagnosis'
    with patch("app.api.v1.chat.generate", return_value="diagnosis"):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "Do I have cancer?"},
            headers=token_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"]["content"] == CHAT_REFUSAL_RESPONSE


@pytest.mark.asyncio
async def test_general_chat_without_report_is_a_health_assistant(
    client: AsyncClient, token_headers: dict, db_session
):
    """A chat with no report uses the general health prompt, not report-only."""
    resp = await client.post(
        "/api/v1/chat/sessions", json={"title": "General"}, headers=token_headers
    )
    session_id = resp.json()["id"]
    captured = {}

    async def fake_generate(prompt, system_instruction=None, **kwargs):
        captured["prompt"] = prompt
        captured["system"] = system_instruction
        return "Start with 3 days a week of brisk walking and light strength work."

    with patch("app.api.v1.chat.generate", side_effect=fake_generate):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "Give me a beginner workout plan"},
            headers=token_headers,
        )
    assert resp.status_code == 200
    assert "walking" in resp.json()["message"]["content"]
    assert "health assistant" in captured["system"]
    assert "only answer based on the provided report" not in captured["system"].lower()
    assert "<REPORT_OVERVIEW>" in captured["prompt"]

    # A follow-up sees the earlier turn.
    with patch("app.api.v1.chat.generate", side_effect=fake_generate):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": "make it shorter"},
            headers=token_headers,
        )
    assert resp.status_code == 200
    assert "beginner workout plan" in captured["prompt"]


@pytest.mark.asyncio
async def test_chat_rejects_blank_and_oversized_messages(client, token_headers):
    created = await client.post(
        "/api/v1/chat/sessions", headers=token_headers, json={"title": "t"}
    )
    sid = created.json()["id"]
    for content in ["", "   ", "x" * 2001]:
        resp = await client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            headers=token_headers,
            json={"content": content},
        )
        assert resp.status_code == 422, content[:10]
