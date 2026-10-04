"""Idempotent setup for the initial super administrator.

The account-creation script and permission bootstrap must use the same email.
Keeping the RBAC setup here prevents an account from being labelled ``admin``
but being unable to enter the administration portal.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.user import User, UserRole

SUPER_ADMIN_PERMISSION = "super_admin"
SUPER_ADMIN_ROLE = "Super Admin"


async def ensure_super_admin_access(session: AsyncSession, user: User) -> bool:
    """Ensure an existing admin has the minimum portal bootstrap role.

    The operation is safe to run again. It deliberately refuses to elevate a
    non-admin account so a typo cannot grant administrator access.
    """
    if user.role != UserRole.admin:
        raise ValueError("Only accounts whose application role is admin can be bootstrapped.")

    changed = False

    permission = (
        await session.execute(
            select(AdminPermission).where(
                AdminPermission.name == SUPER_ADMIN_PERMISSION
            )
        )
    ).scalars().first()
    if permission is None:
        permission = AdminPermission(
            name=SUPER_ADMIN_PERMISSION,
            description="Full access to all systems",
        )
        session.add(permission)
        await session.flush()
        changed = True

    role = (
        await session.execute(
            select(AdminRole).where(AdminRole.name == SUPER_ADMIN_ROLE)
        )
    ).scalars().first()
    if role is None:
        role = AdminRole(
            name=SUPER_ADMIN_ROLE,
            description="Administrator with full access",
        )
        session.add(role)
        await session.flush()
        changed = True

    role_permission = (
        await session.execute(
            select(AdminRolePermission).where(
                AdminRolePermission.role_id == role.id,
                AdminRolePermission.permission_id == permission.id,
            )
        )
    ).scalars().first()
    if role_permission is None:
        session.add(
            AdminRolePermission(role_id=role.id, permission_id=permission.id)
        )
        changed = True

    assignment = (
        await session.execute(
            select(AdminRoleAssignment).where(
                AdminRoleAssignment.user_id == user.id,
                AdminRoleAssignment.role_id == role.id,
            )
        )
    ).scalars().first()
    if assignment is None:
        session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
        changed = True

    return changed
