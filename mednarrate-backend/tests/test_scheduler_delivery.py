"""Regression tests for the scheduler started by the API lifespan."""

from datetime import datetime, timezone

import pytest

from app.models.medication_schedule import MedicationSchedule
from app.models.push_token import PushToken
from app.core.config import settings
from app.services import scheduler as reminder_scheduler


@pytest.mark.asyncio
async def test_active_due_reminder_uses_registered_device_token(
    db_session, db_session_factory, target_user, monkeypatch
):
    reminder_time = datetime.now(timezone.utc).strftime("%H:%M")
    db_session.add(
        MedicationSchedule(
            user_id=target_user.id,
            medication_name="Test medicine",
            dosage="10 mg",
            times_of_day=[reminder_time],
            is_active=True,
        )
    )
    db_session.add(
        PushToken(
            user_id=target_user.id,
            device_token="registered-device-token",
            platform="android",
        )
    )
    await db_session.commit()

    sent = []

    async def fake_send(token, title, body, data):
        sent.append((token, title, body, data))
        return True

    monkeypatch.setattr(reminder_scheduler, "AsyncSessionLocal", db_session_factory)
    monkeypatch.setattr(reminder_scheduler, "send_push_notification", fake_send)

    await reminder_scheduler.check_medication_reminders()

    assert len(sent) == 1
    assert sent[0][0] == "registered-device-token"
    assert sent[0][1] == "Medication Reminder"


@pytest.mark.asyncio
async def test_inactive_reminder_is_not_sent(
    db_session, db_session_factory, target_user, monkeypatch
):
    reminder_time = datetime.now(timezone.utc).strftime("%H:%M")
    db_session.add(
        MedicationSchedule(
            user_id=target_user.id,
            medication_name="Inactive medicine",
            times_of_day=[reminder_time],
            is_active=False,
        )
    )
    db_session.add(
        PushToken(
            user_id=target_user.id,
            device_token="registered-device-token",
            platform="android",
        )
    )
    await db_session.commit()

    sent = []

    async def fake_send(*args, **kwargs):
        sent.append(args)
        return True

    monkeypatch.setattr(reminder_scheduler, "AsyncSessionLocal", db_session_factory)
    monkeypatch.setattr(reminder_scheduler, "send_push_notification", fake_send)

    await reminder_scheduler.check_medication_reminders()

    assert sent == []


def test_production_rejects_server_reminders_without_user_timezones(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://app.example.com"])
    monkeypatch.setattr(settings, "JWT_SECRET", "x" * 40)
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost/mednarrate",
    )
    monkeypatch.setattr(settings, "ANALYSIS_EXECUTION_MODE", "worker")
    monkeypatch.setattr(settings, "SERVER_MEDICATION_PUSH_ENABLED", True)

    with pytest.raises(ValueError, match="per-user timezone"):
        settings.validate_production_security()


def test_server_scheduler_stays_off_when_mobile_alerts_are_primary(monkeypatch):
    monkeypatch.setattr(settings, "SERVER_MEDICATION_PUSH_ENABLED", False)
    reminder_scheduler.start_scheduler()
    assert reminder_scheduler.scheduler.running is False
