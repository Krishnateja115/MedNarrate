"""Timing recorder, provider time cap and summary thinking level."""

import asyncio
import json
import time

import pytest


class _Boom(Exception):
    pass


def _chain_client(monkeypatch, providers):
    from app.core.config import settings
    from app.services import llm_client as lc
    from app.services.provider_health import provider_health

    provider_health.reset()
    client = lc.LLMClient()
    client.providers.update(providers)
    for k, v in {
        "ENVIRONMENT": "development",
        "OPENAI_API_KEY": "k1",
        "MISTRAL_API_KEY": "k2",
        "ANTHROPIC_API_KEY": None,
        "GEMINI_API_KEY": None,
        "VERTEX_PROJECT_ID": None,
        "LLM_PROVIDER_CHAIN": "",
        "ENABLE_LLM_FALLBACK": True,
    }.items():
        monkeypatch.setattr(settings, k, v, raising=False)

    async def cfg():
        return {
            "primary_provider": "openai",
            "fallback_provider": "mistral",
            "enable_fallback": True,
            "model_name": "m",
            "api_key": None,
            "temperature": 0.2,
            "max_tokens": 64,
        }

    monkeypatch.setattr(lc, "get_resolved_ai_config", cfg)
    return client


def test_hung_primary_is_abandoned_after_the_provider_cap(monkeypatch):
    from app.core.config import settings
    from app.services.provider_health import provider_health

    monkeypatch.setattr(settings, "LLM_PROVIDER_TIMEOUT_SECONDS", 0.2, raising=False)
    seen = {}

    class Hung:
        async def generate(self, prompt, **kw):
            seen["hung_timeout"] = kw["timeout"]
            await asyncio.sleep(30)

    class Good:
        async def generate(self, prompt, **kw):
            seen["good_timeout"] = kw["timeout"]
            return {"provider": "mistral", "model": "m", "content": "ok", "latency_ms": 1}

    client = _chain_client(monkeypatch, {"openai": Hung(), "mistral": Good()})
    started = time.perf_counter()
    res = asyncio.run(client.generate_with_metadata("hi", timeout=60))
    elapsed = time.perf_counter() - started

    assert res["provider"] == "mistral"
    assert elapsed < 10, "the hung provider must not hold the request for the full 60s"
    assert seen["hung_timeout"] == pytest.approx(0.2)
    # the last provider in the chain keeps the full timeout
    assert seen["good_timeout"] == 60
    provider_health.reset()


def test_provider_cap_can_be_disabled(monkeypatch):
    from app.core.config import settings
    from app.services.provider_health import provider_health

    monkeypatch.setattr(settings, "LLM_PROVIDER_TIMEOUT_SECONDS", 0, raising=False)
    seen = {}

    class Good:
        async def generate(self, prompt, **kw):
            seen["timeout"] = kw["timeout"]
            return {"provider": "openai", "model": "m", "content": "ok", "latency_ms": 1}

    client = _chain_client(monkeypatch, {"openai": Good(), "mistral": Good()})
    asyncio.run(client.generate_with_metadata("hi", timeout=60))
    assert seen["timeout"] == 60
    provider_health.reset()


def test_summaries_use_configured_thinking_level(monkeypatch):
    from app.core.config import settings
    from app.services import analysis_pipeline as ap

    assert settings.ANALYSIS_THINKING_LEVEL == "LOW"
    levels = []

    async def fake(prompt, **kw):
        levels.append(kw["thinking_level"])
        return {"content": "x"}

    monkeypatch.setattr(ap, "generate_with_timeout_metadata", fake)
    asyncio.run(ap.generate_core_summaries("a", "b", "c", "d", "rid"))
    assert levels == ["LOW", "LOW"]

    monkeypatch.setattr(settings, "ANALYSIS_THINKING_LEVEL", "HIGH", raising=False)
    levels.clear()
    asyncio.run(ap.generate_core_summaries("a", "b", "c", "d", "rid"))
    assert levels == ["HIGH", "HIGH"]


def test_timing_record_writes_json_line_without_payloads(monkeypatch, tmp_path):
    from app.core import timing

    target = tmp_path / "logs" / "timing.jsonl"
    monkeypatch.setenv("TIMING_LOG_PATH", str(target))
    timing.record("CHAT", "report_chat", 1234, llm_ms=1000, language="en", skipped=None)

    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["kind"] == "CHAT"
    assert rows[0]["total_ms"] == 1234
    assert rows[0]["llm_ms"] == 1000
    assert "skipped" not in rows[0]


def test_timing_record_never_raises(monkeypatch, tmp_path):
    from app.core import timing

    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    monkeypatch.setenv("TIMING_LOG_PATH", str(blocker / "timing.jsonl"))
    timing.record("HTTP", "GET /x", 5, status=200)  # must not raise


def test_stopwatch_laps_add_up():
    from app.core.timing import Stopwatch

    watch = Stopwatch()
    time.sleep(0.02)
    first = watch.lap("a")
    watch.add("b", 7)
    assert first >= 15
    assert watch.laps_ms["b"] == 7
    assert watch.total_ms() >= first


def test_http_requests_get_a_timing_header(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("TIMING_LOG_PATH", str(tmp_path / "t.jsonl"))
    client = TestClient(app)  # no lifespan: no database needed for a 404
    resp = client.get("/api/v1/does-not-exist")
    assert "x-process-time-ms" in {k.lower() for k in resp.headers}
    rows = [json.loads(line) for line in (tmp_path / "t.jsonl").read_text().splitlines()]
    assert any(r["kind"] == "HTTP" and r["status"] == 404 for r in rows)
