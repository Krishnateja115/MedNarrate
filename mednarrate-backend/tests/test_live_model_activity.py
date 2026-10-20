"""Live model activity is based on safe telemetry, not benchmark scores."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.llm_telemetry import LLMDiagnosticEvent
from app.services import model_activity


@pytest.mark.asyncio
async def test_live_activity_groups_new_models_and_filters_window(
    client: AsyncClient, admin_token_and_user, db_session
) -> None:
    headers, _ = admin_token_and_user
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add_all([
        LLMDiagnosticEvent(request_id="one", provider="dev_gemini", model_name="flash",
                           feature="analysis", status="success", latency_ms=100, timestamp=now),
        LLMDiagnosticEvent(request_id="two", provider="dev_gemini", model_name="flash",
                           feature="translation", status="success", latency_ms=300, timestamp=now),
        LLMDiagnosticEvent(request_id="three", provider="ollama", model_name="new-local-model",
                           feature="translation", status="success", latency_ms=900, timestamp=now),
        LLMDiagnosticEvent(request_id="four", provider="ollama", model_name="new-local-model",
                           feature="translation", status="error", latency_ms=200, timestamp=now),
        LLMDiagnosticEvent(request_id="old", provider="openai", model_name="old-model",
                           feature="analysis", status="success", latency_ms=500,
                           timestamp=now - timedelta(days=8)),
    ])
    await db_session.commit()

    response = await client.get("/api/v1/admin/ml/live-activity?hours=24", headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["total_successful_calls"] == 3
    assert len(body["models"]) == 2
    hosted, local = body["models"]
    assert (hosted["provider"], hosted["model"], hosted["successful_calls"]) == (
        "dev_gemini", "flash", 2
    )
    assert hosted["avg_latency_ms"] == 200
    assert hosted["features"] == {"analysis": 1, "translation": 1}
    assert (local["model"], local["location"], local["successful_calls"]) == (
        "new-local-model", "local", 1
    )
    assert "prompt" not in str(body).lower()
    assert "output" not in str(body).lower()


@pytest.mark.asyncio
async def test_live_activity_requires_admin_and_valid_window(
    client: AsyncClient, admin_token_and_user
) -> None:
    headers, _ = admin_token_and_user
    assert (await client.get("/api/v1/admin/ml/live-activity")).status_code == 401
    assert (await client.get("/api/v1/admin/ml/live-activity?hours=0", headers=headers)).status_code == 422
    assert (await client.get("/api/v1/admin/ml/live-activity?hours=169", headers=headers)).status_code == 422


@pytest.mark.asyncio
async def test_translation_activity_recorder_stores_metadata_only(
    db_session, db_session_factory, monkeypatch
) -> None:
    monkeypatch.setattr(model_activity, "AsyncSessionLocal", db_session_factory)
    await model_activity.record_successful_model_call(
        request_id="translation-1", provider="gemini", model="flash-lite",
        feature="translation", latency_ms=120.5, fallback_used=False,
    )
    from sqlalchemy import select

    event = (await db_session.execute(select(LLMDiagnosticEvent))).scalar_one()
    assert (event.model_name, event.feature, event.status, event.latency_ms) == (
        "flash-lite", "translation", "success", 120.5
    )
