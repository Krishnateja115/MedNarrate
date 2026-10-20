"""Groq / Cerebras / OpenRouter / GitHub Models share one request shape."""
import pytest

from app.core.config import settings
from app.services import llm_client


class _FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": " OK "}}]}


def _fake_client(captured):
    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json=None, headers=None):
            captured["url"], captured["payload"], captured["headers"] = url, json, headers
            return _FakeResponse()

    return _Client


@pytest.mark.asyncio
async def test_groq_gpt_oss_uses_low_reasoning_effort(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test")
    monkeypatch.setattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", _fake_client(captured))

    result = await llm_client.OpenAICompatibleProvider("groq").generate("hello")

    assert result["content"] == "OK"
    assert captured["payload"]["model"] == "openai/gpt-oss-120b"
    assert captured["payload"]["reasoning_effort"] == "low"
    assert captured["headers"]["Authorization"] == "Bearer gsk_test"


@pytest.mark.asyncio
async def test_other_models_and_providers_get_no_reasoning_parameter(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test")
    monkeypatch.setattr(settings, "GROQ_MODEL", "some-other-model")
    monkeypatch.setattr(settings, "CEREBRAS_API_KEY", "csk_test")
    monkeypatch.setattr(settings, "CEREBRAS_MODEL", "gpt-oss-120b")
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", _fake_client(captured))

    await llm_client.OpenAICompatibleProvider("groq").generate("hello")
    assert "reasoning_effort" not in captured["payload"]

    await llm_client.OpenAICompatibleProvider("cerebras").generate("hello")
    assert "reasoning_effort" not in captured["payload"]


@pytest.mark.asyncio
async def test_groq_qwen_shares_the_groq_key_and_strips_thinking(monkeypatch):
    captured = {}

    class _Thinking(_FakeResponse):
        def json(self):
            return {"choices": [{"message": {"content": "<think>let me reason</think>\nThe answer is 42."}}]}

    base = _fake_client(captured)

    class _Client(base):
        async def post(self, url, json=None, headers=None):
            await super().post(url, json=json, headers=headers)
            return _Thinking()

    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test")
    monkeypatch.setattr(settings, "GROQ_QWEN_MODEL", "qwen/qwen3.8-27b")
    monkeypatch.setattr(llm_client.httpx, "AsyncClient", _Client)

    result = await llm_client.OpenAICompatibleProvider("groq_qwen").generate("hello")

    assert result["content"] == "The answer is 42."
    assert captured["payload"]["model"] == "qwen/qwen3.8-27b"
    assert captured["headers"]["Authorization"] == "Bearer gsk_test"
    assert "reasoning_effort" not in captured["payload"]
    assert "groq_qwen" in llm_client.OPENAI_COMPATIBLE
