"""Admin maintenance and announcements reach the mobile API correctly."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.job_execution import JobExecution
from app.models.system_setting import MaintenanceMode
from app.services import scheduler


@pytest.mark.asyncio
async def test_global_maintenance_blocks_app_but_keeps_recovery_available(
    client: AsyncClient, admin_token_and_user
) -> None:
    headers, _ = admin_token_and_user
    enabled = await client.post(
        "/api/v1/admin/maintenance",
        json={"is_enabled": True, "scope": "all", "message": "Scheduled work in progress"},
        headers=headers,
    )
    assert enabled.status_code == 200, enabled.text

    status = await client.get("/api/v1/maintenance/status")
    assert status.status_code == 200
    assert status.headers["cache-control"] == "no-store"
    assert status.json() == {
        "is_enabled": True, "scope": "all", "message": "Scheduled work in progress"
    }

    app_response = await client.get("/api/v1/users/me")
    assert app_response.status_code == 503
    assert app_response.json()["detail"]["message"] == "Scheduled work in progress"
    assert (await client.get("/api/v1/admin/maintenance", headers=headers)).status_code == 200

    disabled = await client.post(
        "/api/v1/admin/maintenance",
        json={"is_enabled": False, "scope": "all"}, headers=headers,
    )
    assert disabled.status_code == 200
    assert (await client.get("/api/v1/maintenance/status")).json()["is_enabled"] is False
    assert (await client.get("/api/v1/users/me")).status_code != 503


@pytest.mark.asyncio
async def test_notification_scope_only_pauses_notifications(
    client: AsyncClient, admin_token_and_user
) -> None:
    headers, _ = admin_token_and_user
    response = await client.post(
        "/api/v1/admin/maintenance",
        json={"is_enabled": True, "scope": "notifications"}, headers=headers,
    )
    assert response.status_code == 200
    assert (await client.get("/api/v1/notifications/medication-schedules")).status_code == 503
    assert (await client.get("/api/v1/users/me")).status_code != 503


@pytest.mark.asyncio
async def test_notification_scope_skips_background_push(
    db_session, db_session_factory, monkeypatch
) -> None:
    db_session.add(MaintenanceMode(is_enabled=True, scope="notifications"))
    await db_session.commit()
    monkeypatch.setattr(scheduler, "AsyncSessionLocal", db_session_factory)

    await scheduler.check_medication_reminders()

    count = (await db_session.execute(select(func.count()).select_from(JobExecution))).scalar_one()
    assert count == 0


@pytest.mark.asyncio
async def test_published_announcement_is_visible_to_phone_with_language_fallback(
    client: AsyncClient, admin_token_and_user
) -> None:
    headers, _ = admin_token_and_user
    now = datetime.now(timezone.utc)
    local_offset = timezone(timedelta(hours=5, minutes=30))
    created = await client.post(
        "/api/v1/admin/announcements",
        json={
            "title": "Service notice",
            "message": "An update is available in the app.",
            "audience": "all", "language": "en", "status": "published",
            "start_time": (now - timedelta(minutes=1)).astimezone(local_offset).isoformat(),
            "end_time": (now + timedelta(days=1)).astimezone(local_offset).isoformat(),
        },
        headers=headers,
    )
    assert created.status_code == 200, created.text
    response = await client.get(
        "/api/v1/admin/announcements/active/public?audience=patients&language=hi"
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert [item["title"] for item in response.json()["active_announcements"]] == [
        "Service notice"
    ]
