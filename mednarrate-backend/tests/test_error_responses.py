"""The generic 500 response names the failure in local development only."""
import json

import pytest
from starlette.requests import Request

from app.core.config import settings
from app.exceptions import unhandled_exception_handler


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/x", "headers": [], "query_string": b""})


async def _body(exc: Exception) -> dict:
    response = await unhandled_exception_handler(_request(), exc)
    assert response.status_code == 500
    return json.loads(response.body)


@pytest.mark.asyncio
async def test_development_response_names_the_failure(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    body = await _body(RuntimeError("no such table: widgets"))
    assert body["code"] == "internal_server_error"
    assert "no such table: widgets" in body["debug"]


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["production", "staging"])
async def test_production_like_response_never_includes_details(monkeypatch, environment):
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    body = await _body(RuntimeError("no such table: widgets"))
    assert "debug" not in body
    assert "widgets" not in json.dumps(body)


@pytest.mark.asyncio
async def test_secrets_are_redacted_even_in_development(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    body = await _body(RuntimeError("bad key AIzaSyA1234567890abcdefghijklmnopqrstuvw"))
    assert "AIzaSyA1234567890abcdefghijklmnopqrstuvw" not in body["debug"]
