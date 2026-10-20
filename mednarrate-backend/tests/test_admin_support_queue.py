"""Support queue filters: unassigned, open-only and search by e-mail must really filter."""

import pytest
from httpx import AsyncClient

from app.models.support import SupportTicket, TicketCategory, TicketPriority, TicketStatus


def _ticket(user_id, title, status=TicketStatus.new, assigned=None):
    return SupportTicket(
        user_id=user_id, title=title, description="d",
        category=TicketCategory.other, priority=TicketPriority.p3,
        status=status, assigned_admin_id=assigned,
    )


@pytest.mark.asyncio
async def test_support_queue_filters(client: AsyncClient, admin_token_and_user, target_user, db_session):
    headers, admin = admin_token_and_user
    user = target_user[0] if isinstance(target_user, tuple) else target_user
    db_session.add_all([
        _ticket(user.id, "open-unassigned"),
        _ticket(user.id, "open-assigned", TicketStatus.investigating, admin.id),
        _ticket(user.id, "done", TicketStatus.resolved),
    ])
    await db_session.commit()

    async def titles(query):
        res = await client.get(f"/api/v1/admin/support?{query}", headers=headers)
        assert res.status_code == 200, res.text
        return {i["title"] for i in res.json()["items"]}

    assert await titles("") == {"open-unassigned", "open-assigned", "done"}
    assert await titles("open_only=true") == {"open-unassigned", "open-assigned"}
    assert await titles("unassigned=true") == {"open-unassigned", "done"}
    assert await titles("open_only=true&unassigned=true") == {"open-unassigned"}
    assert await titles("status=Resolved&open_only=true") == {"done"}  # explicit status wins
    assert await titles(f"search={user.email[:12]}") == {"open-unassigned", "open-assigned", "done"}
    assert await titles("search=nobody-has-this") == set()


@pytest.mark.asyncio
async def test_admin_reply_reaches_the_app_and_internal_notes_stay_private(
    client: AsyncClient, admin_token_and_user, token_headers, db_session
):
    from sqlalchemy import select
    from app.models.user import User

    headers, _admin = admin_token_and_user
    owner = (await db_session.execute(select(User).where(User.email == "test_part3@example.com"))).scalars().one()
    ticket = _ticket(owner.id, "needs-reply")
    db_session.add(ticket)
    await db_session.commit()

    public = await client.post(
        f"/api/v1/admin/support/{ticket.id}/reply",
        json={"content": "We are on it", "is_internal": False}, headers=headers,
    )
    assert public.status_code == 200, public.text
    note = await client.post(
        f"/api/v1/admin/support/{ticket.id}/reply",
        json={"content": "INTERNAL ONLY", "is_internal": True}, headers=headers,
    )
    assert note.status_code == 200, note.text

    app_view = await client.get(f"/api/v1/support/{ticket.id}", headers=token_headers)
    assert app_view.status_code == 200, app_view.text
    body = app_view.text
    assert "We are on it" in body
    assert "INTERNAL ONLY" not in body


@pytest.mark.asyncio
async def test_assign_and_unassign_ticket(client: AsyncClient, admin_token_and_user, target_user, db_session):
    headers, admin = admin_token_and_user
    ticket = _ticket(target_user.id, "assign-me")
    db_session.add(ticket)
    await db_session.commit()
    url = f"/api/v1/admin/support/{ticket.id}"

    res = await client.patch(url, json={"assigned_admin_id": str(admin.id)}, headers=headers)
    assert res.status_code == 200, res.text
    assert (await client.get(url, headers=headers)).json()["ticket"]["assigned_admin_id"] == str(admin.id)

    res = await client.patch(url, json={"status": "Resolved"}, headers=headers)
    assert res.json()["changes"] == ["Status changed to Resolved"]

    assert (await client.patch(url, json={"assigned_admin_id": "nonsense"}, headers=headers)).status_code == 422

    res = await client.patch(url, json={"assigned_admin_id": ""}, headers=headers)
    assert res.status_code == 200, res.text
    assert (await client.get(url, headers=headers)).json()["ticket"]["assigned_admin_id"] is None
