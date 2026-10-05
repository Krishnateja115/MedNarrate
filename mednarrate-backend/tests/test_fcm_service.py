import logging

import pytest

from app.core.config import settings
from app.services.fcm_service import send_push_notification

pytestmark = pytest.mark.asyncio

TOKEN = "abcdef1234567890SECRETDEVICETOKEN"


async def test_unconfigured_production_does_not_claim_delivery(monkeypatch, caplog):
    monkeypatch.setattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", None, raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with caplog.at_level(logging.DEBUG):
        assert await send_push_notification(TOKEN, "t", "b") is False
    assert "SECRETDEVICETOKEN" not in caplog.text


async def test_unconfigured_development_does_not_claim_delivery(monkeypatch, caplog):
    monkeypatch.setattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", None, raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    with caplog.at_level(logging.DEBUG):
        assert await send_push_notification(TOKEN, "t", "b") is False
    assert "SECRETDEVICETOKEN" not in caplog.text


async def test_missing_token_returns_false():
    assert await send_push_notification("", "t", "b") is False
