import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.user import User, UserRole
from app.services.admin_bootstrap import ensure_super_admin_access


@pytest.mark.asyncio
async def test_bootstrap_grants_named_admin_one_complete_super_admin_role(
    db_session: AsyncSession,
) -> None:
    user = User(
        email=f"bootstrap-{uuid.uuid4().hex}@example.com",
        hashed_password="not-used-by-this-test",
        full_name="Bootstrap Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.flush()

    assert await ensure_super_admin_access(db_session, user) is True
    await db_session.commit()
    assert await ensure_super_admin_access(db_session, user) is False

    permission_count = await db_session.scalar(
        select(func.count()).select_from(AdminPermission).where(
            AdminPermission.name == "super_admin"
        )
    )
    role = (
        await db_session.execute(
            select(AdminRole).where(AdminRole.name == "Super Admin")
        )
    ).scalars().one()
    assignment_count = await db_session.scalar(
        select(func.count()).select_from(AdminRoleAssignment).where(
            AdminRoleAssignment.user_id == user.id,
            AdminRoleAssignment.role_id == role.id,
        )
    )
    role_permission_count = await db_session.scalar(
        select(func.count()).select_from(AdminRolePermission).where(
            AdminRolePermission.role_id == role.id
        )
    )

    assert permission_count == 1
    assert assignment_count == 1
    assert role_permission_count == 1


@pytest.mark.asyncio
async def test_bootstrap_refuses_to_elevate_a_non_admin_account(
    db_session: AsyncSession,
) -> None:
    user = User(
        email=f"patient-{uuid.uuid4().hex}@example.com",
        hashed_password="not-used-by-this-test",
        full_name="Patient",
        role=UserRole.patient,
    )
    db_session.add(user)
    await db_session.flush()

    with pytest.raises(ValueError, match="Only accounts"):
        await ensure_super_admin_access(db_session, user)
