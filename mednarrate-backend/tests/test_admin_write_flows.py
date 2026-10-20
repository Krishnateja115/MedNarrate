"""Write paths of the admin portal that previously crashed or accepted bad input."""
import pytest
from httpx import AsyncClient

from app.models.notification_log import NotificationLog
from app.models.push_token import PushToken


@pytest.mark.asyncio
async def test_role_rejects_unknown_permission_names(client: AsyncClient, admin_token_and_user):
    headers, _ = admin_token_and_user
    res = await client.post(
        "/api/v1/admin/roles",
        json={"name": "Typo role", "permission_names": ["support.view", "suport.manage"]},
        headers=headers,
    )
    assert res.status_code == 422
    assert "suport.manage" in res.text

    ok = await client.post(
        "/api/v1/admin/roles",
        json={"name": "Good role", "permission_names": ["support.view", "dashboard.view"]},
        headers=headers,
    )
    assert ok.status_code == 201, ok.text

    bad_update = await client.put(
        f"/api/v1/admin/roles/{ok.json()['id']}",
        json={"permission_names": ["not.a.permission"]},
        headers=headers,
    )
    assert bad_update.status_code == 422


@pytest.mark.asyncio
async def test_notification_dispatch_and_retry_do_not_crash(
    client: AsyncClient, admin_token_and_user, target_user, db_session
):
    from sqlalchemy import select

    headers, _ = admin_token_and_user
    db_session.add(PushToken(user_id=target_user.id, device_token="tok-1234567890", platform="android"))
    await db_session.commit()

    # No Firebase in tests: the send fails, but it must be logged, not crash.
    res = await client.post(
        "/api/v1/admin/notifications/dispatch",
        json={"title": "Hello", "body": "Test", "audience": "patients"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["dispatched_count"] == 0

    log = (await db_session.execute(select(NotificationLog))).scalars().one()
    assert log.status == "failed"

    retry = await client.post(f"/api/v1/admin/automation-ops/notifications/{log.id}/retry", headers=headers)
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] == "failed"

    # The log views must render rows (they referenced a column that does not exist).
    logs = await client.get("/api/v1/admin/notifications/logs", headers=headers)
    assert logs.status_code == 200, logs.text
    assert logs.json()["items"][0]["title"] == "Hello"
    per_user = await client.get(f"/api/v1/admin/users/{target_user.id}/notifications", headers=headers)
    assert per_user.status_code == 200, per_user.text
    assert per_user.json()["items"][0]["title"] == "Hello"
    listing = await client.get("/api/v1/admin/automation-ops/notifications", headers=headers)
    assert listing.status_code == 200, listing.text


@pytest.mark.asyncio
async def test_user_detail_tabs_render_for_a_user_with_data(
    client: AsyncClient, admin_token_and_user, target_user, db_session
):
    """Every tab on the admin user page must work for a user who actually has data
    (several used to read columns that do not exist and returned 500)."""
    from datetime import datetime

    from sqlalchemy import select

    from app.models.chat import ChatSession
    from app.models.medication_schedule import MedicationSchedule
    from app.models.report import Report
    from app.models.report_analysis import ReportAnalysis
    from app.models.support import SupportTicket, TicketCategory, TicketPriority

    headers, _ = admin_token_and_user
    report = (await db_session.execute(select(Report).where(Report.user_id == target_user.id))).scalars().first()
    db_session.add_all(
        [
            ChatSession(user_id=target_user.id, title="My chat"),
            SupportTicket(
                user_id=target_user.id, title="Help me", description="please help me out",
                category=TicketCategory.other, priority=TicketPriority.p3,
            ),
            ReportAnalysis(report_id=report.id, processed_at=datetime.utcnow()),
            MedicationSchedule(user_id=target_user.id, medication_name="Metformin", dosage="500mg", frequency="daily"),
        ]
    )
    await db_session.commit()

    for tab in ("reports", "analyses", "chats", "reminders", "notifications", "support", "security", "sessions"):
        res = await client.get(f"/api/v1/admin/users/{target_user.id}/{tab}", headers=headers)
        assert res.status_code == 200, f"{tab}: {res.status_code} {res.text[:300]}"

    chats = (await client.get(f"/api/v1/admin/users/{target_user.id}/chats", headers=headers)).json()
    assert chats["items"][0]["title"] == "My chat"
    tickets = (await client.get(f"/api/v1/admin/users/{target_user.id}/support", headers=headers)).json()
    assert tickets["items"][0]["subject"] == "Help me"
    analyses = (await client.get(f"/api/v1/admin/users/{target_user.id}/analyses", headers=headers)).json()
    assert analyses["items"][0]["status"] == "completed"
