"""AI Operations counts requests, not provider attempts."""
import pytest
from httpx import AsyncClient

from app.models.llm_telemetry import LLMDiagnosticEvent


def _evt(req, provider, status, model="unknown", latency=0.0, fallback=False, cat=None):
    return LLMDiagnosticEvent(
        request_id=req, provider=provider, model_name=model, feature="analysis",
        status=status, latency_ms=latency, fallback_used=fallback, error_category=cat,
    )


@pytest.mark.asyncio
async def test_overview_counts_requests_not_attempts(client: AsyncClient, admin_token_and_user, db_session):
    headers, _ = admin_token_and_user
    db_session.add_all([
        # A: ollama is down, vertex has no key, Gemini answers
        _evt("A", "ollama", "error", cat="LLMConnectionError"),
        _evt("A", "vertex_ai", "error", cat="not_configured", fallback=True),
        _evt("A", "dev_gemini", "success", "gemini-3.1-flash-lite", 1000, fallback=True),
        # B: Gemini answers straight away
        _evt("B", "dev_gemini", "success", "gemini-3.1-flash-lite", 2000),
        # C: nothing answered except the built-in safe fallback
        _evt("C", "dev_gemini", "error", cat="LLMConfigurationError"),
        _evt("C", "fallback", "success", "mednarrate-fallback-v1", 10, fallback=True),
        # D: every provider failed, one timed out
        _evt("D", "dev_gemini", "timeout", cat="Timeout"),
    ])
    await db_session.commit()

    res = await client.get("/api/v1/admin/ai-ops/overview", headers=headers)
    assert res.status_code == 200, res.text
    o = res.json()["overview"]
    assert o["total_requests"] == 4
    assert o["answered_requests"] == 3
    assert o["success_rate"] == pytest.approx(75.0)
    assert o["failure_rate"] == pytest.approx(25.0)
    assert o["timeout_rate"] == pytest.approx(25.0)
    # only answered attempts count towards latency
    assert o["avg_latency_ms"] == pytest.approx((1000 + 2000 + 10) / 3, abs=0.01)
    # requests answered after another provider failed: A and C
    assert o["fallback_usage"] == 2
    served = {(p["provider"], p["model"]): p["requests"] for p in o["providers"]}
    assert served == {("dev_gemini", "gemini-3.1-flash-lite"): 2, ("fallback", "mednarrate-fallback-v1"): 1}
    assert all(p["provider"] != "ollama" for p in o["providers"])


@pytest.mark.asyncio
async def test_failures_report_attempts_by_provider(client: AsyncClient, admin_token_and_user, db_session):
    headers, _ = admin_token_and_user
    db_session.add_all([
        _evt("A", "ollama", "error", cat="LLMConnectionError"),
        _evt("B", "ollama", "error", cat="LLMConnectionError"),
        _evt("B", "dev_gemini", "success", "gemini-3.1-flash-lite", 500),
        _evt("C", "dev_gemini", "success", "gemini-3.1-flash-lite", 500),  # no error category
    ])
    await db_session.commit()
    res = await client.get("/api/v1/admin/ai-ops/failures", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["failures"] == [{"category": "LLMConnectionError", "count": 2}]  # no null bucket
    assert [(r["provider"], r["attempts"]) for r in data["failed_attempts_by_provider"]] == [("ollama", 2)]


@pytest.mark.asyncio
async def test_overview_empty(client: AsyncClient, admin_token_and_user):
    headers, _ = admin_token_and_user
    res = await client.get("/api/v1/admin/ai-ops/overview", headers=headers)
    assert res.status_code == 200
    o = res.json()["overview"]
    assert o["total_requests"] == 0 and o["success_rate"] == 0 and o["providers"] == []
