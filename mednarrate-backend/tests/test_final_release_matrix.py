import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin import AdminRole, AdminRoleAssignment
from app.models.user import User, UserRole


@pytest.fixture
async def release_super_admin(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email=f"rel_super_{uuid.uuid4()}@test.com",
        hashed_password=hash_password("SuperPass123!"),
        full_name="Release Super Admin",
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Super Admin Role
    sa_role = (
        await db_session.execute(
            select(AdminRole).where(AdminRole.name == "Super Admin")
        )
    ).scalar_one_or_none()
    if not sa_role:
        sa_role = AdminRole(
            id=uuid.uuid4(),
            name="Super Admin",
            description="Full Governance Super Admin",
        )
        db_session.add(sa_role)
        await db_session.flush()

    assignment = AdminRoleAssignment(
        id=uuid.uuid4(), user_id=user.id, role_id=sa_role.id
    )
    db_session.add(assignment)
    await db_session.commit()

    token = create_access_token(subject=str(user.id))
    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.mark.asyncio
async def test_analytics_endpoint_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/admin/analytics")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_analytics_endpoint_success(
    client: AsyncClient, release_super_admin: dict
):
    headers = release_super_admin["headers"]
    response = await client.get("/api/v1/admin/analytics?timeframe=7d", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "product" in data
    assert "reports" in data
    assert "ai" in data
    assert "chat" in data
    assert "notifications" in data
    assert data["product"]["total_users"] >= 1


@pytest.mark.asyncio
async def test_global_search_endpoint(client: AsyncClient, release_super_admin: dict):
    headers = release_super_admin["headers"]
    response = await client.get("/api/v1/admin/search?q=Release", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "results" in data
    assert len(data["results"]) >= 1
    assert data["results"][0]["type"] == "user"


@pytest.mark.asyncio
async def test_alerts_endpoint_and_acknowledge(
    client: AsyncClient, release_super_admin: dict
):
    headers = release_super_admin["headers"]
    # 1. Fetch alerts
    response = await client.get("/api/v1/admin/alerts", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "alerts" in data

    # 2. Acknowledge alert
    ack_res = await client.post(
        "/api/v1/admin/alerts/test_alert_id/acknowledge", headers=headers
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["alert_id"] == "test_alert_id"
