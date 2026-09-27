import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_token
from app.models.admin import (
    AdminAuditLog,
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from tests.conftest import engine


async def _admin(
    db: AsyncSession,
    *,
    name: str,
    permissions: list[str] | None = None,
    super_admin: bool = False,
    active: bool = True,
) -> User:
    user = User(
        email=f"{name}-{uuid.uuid4()}@example.com",
        hashed_password="unused",
        full_name=name,
        role=UserRole.admin,
        is_active=active,
    )
    db.add(user)
    await db.flush()
    role_name = "Super Admin" if super_admin else f"{name} Role {uuid.uuid4()}"
    role = (await db.execute(select(AdminRole).where(AdminRole.name == role_name))).scalars().first()
    if not role:
        role = AdminRole(name=role_name, description="Admin account control test")
        db.add(role)
        await db.flush()
    db.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    for permission_name in permissions or []:
        permission = (
            await db.execute(
                select(AdminPermission).where(AdminPermission.name == permission_name)
            )
        ).scalars().first()
        if not permission:
            permission = AdminPermission(name=permission_name, description="Test")
            db.add(permission)
            await db.flush()
        existing = await db.get(
            AdminRolePermission,
            {"role_id": role.id, "permission_id": permission.id},
        )
        if not existing:
            db.add(AdminRolePermission(role_id=role.id, permission_id=permission.id))
    await db.commit()
    return user


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


@pytest.mark.asyncio
async def test_authorized_deactivate_revokes_sessions_and_audits(
    client: AsyncClient, db_session: AsyncSession
):
    actor = await _admin(
        db_session, name="Account Manager", permissions=["admins.manage"]
    )
    target = await _admin(db_session, name="Target Admin")
    db_session.add(
        RefreshToken(
            user_id=target.id,
            token_hash=hash_token("target-refresh"),
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/admin/admins/{target.id}/deactivate", headers=_headers(actor)
    )

    assert response.status_code == 200
    await db_session.refresh(target)
    assert target.is_active is False
    assert (
        await db_session.scalar(
            select(RefreshToken).where(RefreshToken.user_id == target.id)
        )
        is None
    )
    audit = (
        await db_session.execute(
            select(AdminAuditLog).where(
                AdminAuditLog.action == "ADMIN_DEACTIVATED",
                AdminAuditLog.resource_id == str(target.id),
            )
        )
    ).scalars().first()
    assert audit is not None
    assert audit.actor_admin_id == actor.id
    assert audit.metadata_payload["revoked_sessions"] == 1


@pytest.mark.asyncio
async def test_deactivate_validation_and_authorization(
    client: AsyncClient, db_session: AsyncSession
):
    manager = await _admin(
        db_session, name="Limited Manager", permissions=["admins.manage"]
    )
    ordinary = await _admin(db_session, name="No Manage Permission")

    assert (
        await client.post(
            f"/api/v1/admin/admins/{manager.id}/deactivate",
            headers=_headers(manager),
        )
    ).status_code == 400
    assert (
        await client.post(
            "/api/v1/admin/admins/not-a-uuid/deactivate", headers=_headers(manager)
        )
    ).status_code == 400
    assert (
        await client.post(
            f"/api/v1/admin/admins/{uuid.uuid4()}/deactivate",
            headers=_headers(manager),
        )
    ).status_code == 404
    assert (
        await client.post(f"/api/v1/admin/admins/{manager.id}/deactivate")
    ).status_code == 401
    assert (
        await client.post(
            f"/api/v1/admin/admins/{manager.id}/deactivate",
            headers=_headers(ordinary),
        )
    ).status_code == 403


@pytest.mark.asyncio
async def test_non_super_cannot_manage_super_admin(
    client: AsyncClient, db_session: AsyncSession
):
    manager = await _admin(
        db_session, name="Non Super Manager", permissions=["admins.manage"]
    )
    super_target = await _admin(db_session, name="Super Target", super_admin=True)

    deactivate = await client.post(
        f"/api/v1/admin/admins/{super_target.id}/deactivate",
        headers=_headers(manager),
    )
    force_logout = await client.post(
        f"/api/v1/admin/admins/{super_target.id}/force-logout",
        headers=_headers(manager),
    )
    roles = await client.post(
        f"/api/v1/admin/admins/{super_target.id}/roles",
        json={"role_ids": []},
        headers=_headers(manager),
    )

    assert deactivate.status_code == 403
    assert force_logout.status_code == 403
    assert roles.status_code == 403


@pytest.mark.asyncio
async def test_final_active_super_admin_cannot_lose_super_role(
    client: AsyncClient, db_session: AsyncSession
):
    target = await _admin(db_session, name="Final Super Target", super_admin=True)
    super_role = (
        await db_session.execute(
            select(AdminRole).where(AdminRole.name == "Super Admin")
        )
    ).scalars().one()
    assignments = (
        await db_session.execute(
            select(User)
            .join(AdminRoleAssignment, AdminRoleAssignment.user_id == User.id)
            .where(
                AdminRoleAssignment.role_id == super_role.id,
                User.id.not_in([target.id]),
            )
        )
    ).scalars().all()
    original_states = {user.id: user.is_active for user in assignments}
    for user in assignments:
        user.is_active = False
    await db_session.commit()
    try:
        response = await client.post(
            f"/api/v1/admin/admins/{target.id}/roles",
            json={"role_ids": []},
            headers=_headers(target),
        )
        assert response.status_code == 409
        assert response.json()["detail"] == (
            "Cannot remove Super Admin from the final active Super Admin."
        )
    finally:
        for user in assignments:
            user.is_active = original_states[user.id]
        await db_session.commit()


@pytest.mark.asyncio
async def test_reactivate_and_force_logout(
    client: AsyncClient, db_session: AsyncSession
):
    actor = await _admin(
        db_session, name="Lifecycle Manager", permissions=["admins.manage"]
    )
    target = await _admin(db_session, name="Lifecycle Target", active=False)
    reactivate = await client.post(
        f"/api/v1/admin/admins/{target.id}/reactivate", headers=_headers(actor)
    )
    assert reactivate.status_code == 200
    await db_session.refresh(target)
    assert target.is_active is True

    db_session.add(
        RefreshToken(
            user_id=target.id,
            token_hash=hash_token("force-logout-token"),
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
    )
    await db_session.commit()
    force_logout = await client.post(
        f"/api/v1/admin/admins/{target.id}/force-logout", headers=_headers(actor)
    )
    assert force_logout.status_code == 200
    assert (
        await db_session.scalar(
            select(RefreshToken).where(RefreshToken.user_id == target.id)
        )
        is None
    )


@pytest.mark.asyncio
async def test_inactive_admin_cannot_refresh_or_use_access_token(
    client: AsyncClient, db_session: AsyncSession
):
    inactive = await _admin(db_session, name="Inactive Admin", active=False)
    db_session.add(
        RefreshToken(
            user_id=inactive.id,
            token_hash=hash_token("inactive-refresh"),
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
    )
    await db_session.commit()

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "inactive-refresh"}
    )
    protected = await client.get("/api/v1/admin/me", headers=_headers(inactive))
    assert refresh.status_code == 401
    assert protected.status_code == 401


@pytest.mark.asyncio
async def test_direct_admin_detail_and_list_query_count_is_constant(
    client: AsyncClient, db_session: AsyncSession
):
    viewer = await _admin(
        db_session, name="Admin Viewer", permissions=["admins.view"]
    )
    target = await _admin(db_session, name="Detail Target")
    detail = await client.get(
        f"/api/v1/admin/admins/{target.id}", headers=_headers(viewer)
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == str(target.id)
    assert "hashed_password" not in detail.json()

    for index in range(3):
        await _admin(db_session, name=f"Query Count Target {index}")

    statements: list[str] = []

    def count_statement(*args):
        statements.append(args[2])

    event.listen(engine.sync_engine, "before_cursor_execute", count_statement)
    try:
        response = await client.get("/api/v1/admin/admins", headers=_headers(viewer))
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", count_statement)
    assert response.status_code == 200
    role_queries = [
        sql
        for sql in statements
        if "admin_role_assignments" in sql.lower()
        and "admin_roles" in sql.lower()
        and "admin_permissions" not in sql.lower()
    ]
    assert len(role_queries) <= 2
