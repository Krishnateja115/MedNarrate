from typing import List, Callable, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment

class AdminContext:
    def __init__(self, user: User, permissions: List[str]):
        self.user = user
        self.permissions = set(permissions)
        self.is_super_admin = "super_admin" in self.permissions or "Super Admin" in self.permissions # Simplified check
        
    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id

    def has_permission(self, permission: str) -> bool:
        if self.is_super_admin:
            return True
        return permission in self.permissions


async def get_admin_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminContext:
    """
    Ensures the user has the 'admin' UserRole and fetches their granular permissions.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")

    # Fetch permissions
    stmt = (
        select(AdminPermission.name)
        .select_from(AdminRoleAssignment)
        .join(AdminRolePermission, AdminRoleAssignment.role_id == AdminRolePermission.role_id)
        .join(AdminPermission, AdminRolePermission.permission_id == AdminPermission.id)
        .where(AdminRoleAssignment.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    permissions = [row[0] for row in result.all()]
    
    # Check if they are a super admin directly by role name (for bootstrap flexibility)
    stmt_roles = (
        select(AdminRole.name)
        .join(AdminRoleAssignment, AdminRole.id == AdminRoleAssignment.role_id)
        .where(AdminRoleAssignment.user_id == current_user.id)
    )
    roles = [row[0] for row in (await db.execute(stmt_roles)).all()]
    if "Super Admin" in roles:
        permissions.append("super_admin")

    return AdminContext(user=current_user, permissions=permissions)


def require_permission(permission: str) -> Callable:
    """
    Dependency that returns the AdminContext if the admin has the specified permission.
    """
    async def _require_permission(admin_ctx: AdminContext = Depends(get_admin_context)) -> AdminContext:
        if not admin_ctx.has_permission(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing required permission: {permission}")
        return admin_ctx
    return _require_permission


def require_any_permission(permissions: List[str]) -> Callable:
    """
    Dependency that returns the AdminContext if the admin has ANY of the specified permissions.
    """
    async def _require_any(admin_ctx: AdminContext = Depends(get_admin_context)) -> AdminContext:
        if admin_ctx.is_super_admin:
            return admin_ctx
        if not any(p in admin_ctx.permissions for p in permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires one of permissions: {permissions}")
        return admin_ctx
    return _require_any


def require_all_permissions(permissions: List[str]) -> Callable:
    """
    Dependency that returns the AdminContext if the admin has ALL of the specified permissions.
    """
    async def _require_all(admin_ctx: AdminContext = Depends(get_admin_context)) -> AdminContext:
        if admin_ctx.is_super_admin:
            return admin_ctx
        missing = [p for p in permissions if p not in admin_ctx.permissions]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing required permissions: {missing}")
        return admin_ctx
    return _require_all
