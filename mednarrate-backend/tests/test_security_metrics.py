"""Controlled database fixtures for Security Center metric definitions."""

from datetime import datetime, timedelta
import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.admin import (
    AdminAuditLog,
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.services.security_metrics import get_security_metrics


@pytest.mark.asyncio
async def test_security_metrics_are_exact_for_admin_status_and_sessions(
    client, db_session: AsyncSession
):
    """Active admins and active sessions remain distinct database counts."""
    # Controlled zero-admin baseline.  Delete dependent rows first because these
    # fixtures share the test database with the API client.
    await db_session.execute(delete(AdminAuditLog))
    await db_session.execute(delete(RefreshToken))
    await db_session.execute(delete(AdminRoleAssignment))
    await db_session.execute(delete(User))
    await db_session.commit()

    assert await get_security_metrics(db_session) == {
        "total_admins": 0,
        "active_admins": 0,
        "suspended_admins": 0,
        "active_sessions": 0,
        "active_breakglass_grants": 0,
        "pending_privacy_requests": 0,
        "total_security_events": 0,
    }

    security_reader = User(
        email=f"security-reader-{uuid.uuid4()}@example.test",
        full_name="Security Reader",
        hashed_password="unused",
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(security_reader)
    await db_session.flush()
    assert (await get_security_metrics(db_session))["total_admins"] == 1
    assert (await get_security_metrics(db_session))["active_admins"] == 1

    active_admin = User(
        email=f"active-admin-{uuid.uuid4()}@example.test",
        full_name="Active Admin",
        hashed_password="unused",
        role=UserRole.admin,
        is_active=True,
    )
    suspended_admin = User(
        email=f"suspended-admin-{uuid.uuid4()}@example.test",
        full_name="Suspended Admin",
        hashed_password="unused",
        role=UserRole.admin,
        is_active=False,
    )
    db_session.add_all([active_admin, suspended_admin])
    await db_session.flush()

    now = datetime.utcnow()
    db_session.add_all(
        [
            RefreshToken(
                user_id=active_admin.id,
                token_hash="active-session-1",
                expires_at=now + timedelta(hours=1),
                revoked=False,
            ),
            RefreshToken(
                user_id=active_admin.id,
                token_hash="active-session-2",
                expires_at=now + timedelta(hours=1),
                revoked=False,
            ),
            RefreshToken(
                user_id=active_admin.id,
                token_hash="expired-session",
                expires_at=now - timedelta(hours=1),
                revoked=False,
            ),
            RefreshToken(
                user_id=suspended_admin.id,
                token_hash="suspended-session",
                expires_at=now + timedelta(hours=1),
                revoked=False,
            ),
        ]
    )
    db_session.add_all(
        [
            AdminAuditLog(
                actor_admin_id=active_admin.id,
                action="ADMIN_LOGIN_SUCCESS",
                result="success",
            ),
            AdminAuditLog(
                actor_admin_id=active_admin.id,
                action="FAILED_ADMIN_LOGIN",
                result="failure",
            ),
            AdminAuditLog(
                actor_admin_id=security_reader.id,
                action="ROLE_CHANGE",
                result="success",
            ),
        ]
    )

    permission = AdminPermission(
        name=f"security.view.{uuid.uuid4()}", description="Test security access"
    )
    role = AdminRole(name=f"Security Reader {uuid.uuid4()}")
    db_session.add_all([permission, role])
    await db_session.flush()
    db_session.add_all(
        [
            AdminRolePermission(role_id=role.id, permission_id=permission.id),
            AdminRoleAssignment(user_id=security_reader.id, role_id=role.id),
        ]
    )
    await db_session.commit()

    metrics = await get_security_metrics(db_session)
    assert metrics["total_admins"] == 3
    assert metrics["active_admins"] == 2
    assert metrics["suspended_admins"] == 1
    assert metrics["active_sessions"] == 2
    assert metrics["total_security_events"] == 3

    # Super-admin-compatible test permission uses the real endpoint contract.
    # The reader has a role assignment, but security.view itself is intentionally
    # named uniquely, so grant the standard permission for the HTTP assertion.
    standard_permission = (
        (
            await db_session.execute(
                select(AdminPermission).where(AdminPermission.name == "security.view")
            )
        )
        .scalars()
        .first()
    )
    if not standard_permission:
        standard_permission = AdminPermission(
            name="security.view", description="Security"
        )
        db_session.add(standard_permission)
        await db_session.flush()
    db_session.add(
        AdminRolePermission(role_id=role.id, permission_id=standard_permission.id)
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/admin/security/overview",
        headers={
            "Authorization": f"Bearer {create_access_token(str(security_reader.id))}"
        },
    )
    assert response.status_code == 200
    assert response.json()["total_admins"] == 3
    assert response.json()["active_admins"] == 2
    assert response.json()["suspended_admins"] == 1
    assert response.json()["active_sessions"] == 2
