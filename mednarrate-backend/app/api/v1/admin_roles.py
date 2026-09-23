from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.admin_auth import AdminContext, get_admin_context, require_permission, require_any_permission
from app.services.audit import log_admin_action
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment

router = APIRouter()

class RoleCreateReq(BaseModel):
    name: str
    description: Optional[str] = None
    permission_names: List[str] = []

class RoleUpdateReq(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_names: List[str] = []

DEFAULT_PERMISSIONS = [
    ("dashboard.view", "View admin dashboard and general metrics"),
    ("security.view", "View security overview and security event logs"),
    ("admins.view", "View admin accounts list"),
    ("admins.manage", "Create, deactivate, reactivate, and assign roles to admins"),
    ("roles.view", "View roles and permission matrix"),
    ("roles.manage", "Create and update roles and permissions"),
    ("audit.view", "View immutable audit logs"),
    ("breakglass.request", "Request temporary sensitive data access"),
    ("breakglass.manage", "Approve or revoke break-glass grants"),
    ("privacy.view", "View privacy data requests and sensitive access history"),
    ("privacy.manage", "Manage data access, export, and deletion requests"),
    ("feature_flags.view", "View feature flags"),
    ("feature_flags.manage", "Create and update feature flags"),
    ("ai.view", "View AI configuration and diagnostic telemetry"),
    ("ai.manage", "Update AI configuration and provider settings"),
    ("settings.view", "View system settings and maintenance status"),
    ("settings.manage", "Update operational settings and maintenance mode"),
    ("announcements.manage", "Create and manage system announcements"),
    ("reports.view", "View reports list and diagnostics"),
    ("users.view", "View registered user profiles"),
    ("users.manage", "Manage user status and roles"),
    ("support.manage", "Manage support tickets and help articles"),
]

@router.get("/permissions")
async def list_permissions(
    request: Request,
    admin_ctx: AdminContext = Depends(require_any_permission(["roles.view", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdminPermission)
    res = await db.execute(stmt)
    perms = res.scalars().all()

    # Seed default permissions if table is empty
    if not perms:
        for name, desc in DEFAULT_PERMISSIONS:
            p = AdminPermission(name=name, description=desc)
            db.add(p)
        await db.commit()
        res = await db.execute(select(AdminPermission))
        perms = res.scalars().all()

    return [{"id": str(p.id), "name": p.name, "description": p.description} for p in perms]

@router.get("")
async def list_roles(
    request: Request,
    admin_ctx: AdminContext = Depends(require_any_permission(["roles.view", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdminRole)
    res = await db.execute(stmt)
    roles = res.scalars().all()

    out = []
    for r in roles:
        # Fetch perms
        stmt_perms = (
            select(AdminPermission)
            .join(AdminRolePermission, AdminPermission.id == AdminRolePermission.permission_id)
            .where(AdminRolePermission.role_id == r.id)
        )
        perms = (await db.execute(stmt_perms)).scalars().all()

        # Count assigned admins
        stmt_count = select(AdminRoleAssignment).where(AdminRoleAssignment.role_id == r.id)
        assigned_count = len((await db.execute(stmt_count)).scalars().all())

        out.append({
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "permissions": [p.name for p in perms],
            "assigned_admins_count": assigned_count
        })

    await log_admin_action(
        db=db,
        action="LIST_ROLES",
        actor_admin_id=admin_ctx.user.id,
        permission_used="roles.view",
        request=request
    )
    await db.commit()

    return out

@router.post("", status_code=201)
async def create_role(
    req: RoleCreateReq,
    request: Request,
    admin_ctx: AdminContext = Depends(require_any_permission(["roles.manage", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    # Self-escalation check
    if not admin_ctx.is_super_admin:
        missing = [p for p in req.permission_names if p not in admin_ctx.permissions]
        if missing:
            await log_admin_action(
                db=db,
                action="CREATE_ROLE_SELF_ESCALATION_BLOCKED",
                actor_admin_id=admin_ctx.user.id,
                result="denied",
                reason=f"Cannot create role with unheld permissions: {missing}",
                request=request
            )
            await db.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Self-escalation blocked: You cannot grant permissions you do not possess ({missing})."
            )

    new_role = AdminRole(name=req.name, description=req.description)
    db.add(new_role)
    await db.flush()

    for p_name in req.permission_names:
        stmt = select(AdminPermission).where(AdminPermission.name == p_name)
        perm = (await db.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name=p_name, description=f"Permission {p_name}")
            db.add(perm)
            await db.flush()
        rp = AdminRolePermission(role_id=new_role.id, permission_id=perm.id)
        db.add(rp)

    await log_admin_action(
        db=db,
        action="CREATE_ROLE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="AdminRole",
        resource_id=str(new_role.id),
        permission_used="roles.manage",
        request=request,
        metadata={"role_name": req.name, "permissions": req.permission_names}
    )
    await db.commit()

    return {"status": "ok", "id": str(new_role.id), "name": new_role.name}

@router.put("/{id}")
async def update_role(
    id: str,
    req: RoleUpdateReq,
    request: Request,
    admin_ctx: AdminContext = Depends(require_any_permission(["roles.manage", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        role_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID.")

    stmt = select(AdminRole).where(AdminRole.id == role_uuid)
    role = (await db.execute(stmt)).scalars().first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")

    # Self-escalation check
    if not admin_ctx.is_super_admin:
        missing = [p for p in req.permission_names if p not in admin_ctx.permissions]
        if missing:
            await log_admin_action(
                db=db,
                action="UPDATE_ROLE_SELF_ESCALATION_BLOCKED",
                actor_admin_id=admin_ctx.user.id,
                resource_type="AdminRole",
                resource_id=id,
                result="denied",
                reason=f"Cannot grant permissions unheld by requesting admin: {missing}",
                request=request
            )
            await db.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Self-escalation blocked: You cannot grant permissions you do not possess ({missing})."
            )

    if req.name:
        role.name = req.name
    if req.description is not None:
        role.description = req.description

    # Update role permissions
    await db.execute(delete(AdminRolePermission).where(AdminRolePermission.role_id == role_uuid))
    for p_name in req.permission_names:
        stmt_p = select(AdminPermission).where(AdminPermission.name == p_name)
        perm = (await db.execute(stmt_p)).scalars().first()
        if not perm:
            perm = AdminPermission(name=p_name, description=f"Permission {p_name}")
            db.add(perm)
            await db.flush()
        rp = AdminRolePermission(role_id=role_uuid, permission_id=perm.id)
        db.add(rp)

    await log_admin_action(
        db=db,
        action="PERMISSION_CHANGE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="AdminRole",
        resource_id=id,
        permission_used="roles.manage",
        request=request,
        metadata={"role_name": role.name, "permissions": req.permission_names}
    )
    await db.commit()

    return {"status": "ok", "message": "Role permissions updated."}
