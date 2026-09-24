import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.user import User, UserRole


@pytest.fixture
async def analytics_admin(db_session: AsyncSession):
    user = User(
        email=f"analytics_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Analytics Admin",
        role=UserRole.admin,
    )
    db_session.add(user)

    role = AdminRole(name=f"Analytics Admin_{uuid.uuid4()}")
    db_session.add(role)

    stmt = select(AdminPermission).where(AdminPermission.name == "analytics.view")
    perm = (await db_session.execute(stmt)).scalars().first()
    if not perm:
        perm = AdminPermission(name="analytics.view")
        db_session.add(perm)

    await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_analytics_avoids_fabricated_data(
    client: AsyncClient, analytics_admin: User
):
    """Ensure the analytics endpoint returns real data and handles division by zero safely."""
    token = create_access_token(subject=str(analytics_admin.id))

    resp = await client.get(
        "/api/v1/admin/analytics?timeframe=7d",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "ok"

    # Verify we aren't getting the hardcoded 85.0% or 4.2s anymore when there's no data
    if data["reports"]["total_uploads"] == 0:
        assert data["reports"]["success_rate_pct"] is None
        assert data["reports"]["failure_rate_pct"] is None
        assert data["reports"]["avg_processing_time_sec"] is None

    if data["ai"]["total_requests"] == 0:
        assert data["ai"]["success_rate_pct"] is None
        assert data["ai"]["avg_latency_ms"] is None
