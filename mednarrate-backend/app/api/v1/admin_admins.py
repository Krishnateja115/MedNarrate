import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from sqlalchemy import delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_any_permission
from app.core.database import get_db
from app.core.security import hash_password
from app.models.admin import (
    AdminAuditLog,
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.services.audit import log_admin_action

router = APIRouter()


class AdminCreateReq(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_ids: List[str] = []


class RoleAssignReq(BaseModel):
    role_ids: List[str]


@router.get("")
async def list_admins(
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.view", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(User).where(User.role == UserRole.admin).order_by(desc(User.created_at))
    )
    res = await db.execute(stmt)
    admins = res.scalars().all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session_counts = dict(
        (
            await db.execute(
                select(RefreshToken.user_id, func.count(RefreshToken.id))
                .where(RefreshToken.revoked.is_(False), RefreshToken.expires_at > now)
                .group_by(RefreshToken.user_id)
            )
        ).all()
    )
    last_logins = dict(
        (
            await db.execute(
                select(AdminAuditLog.actor_admin_id, func.max(AdminAuditLog.timestamp))
                .where(AdminAuditLog.action == "ADMIN_LOGIN_SUCCESS")
                .group_by(AdminAuditLog.actor_admin_id)
            )
        ).all()
    )

    out = []
    for admin in admins:
        # Fetch assigned roles
        stmt_roles = (
            select(AdminRole)
            .join(AdminRoleAssignment, AdminRole.id == AdminRoleAssignment.role_id)
            .where(AdminRoleAssignment.user_id == admin.id)
        )
        roles = (await db.execute(stmt_roles)).scalars().all()
        role_list = [{"id": str(r.id), "name": r.name} for r in roles]
        role_names = [role["name"] for role in role_list]

        out.append(
            {
                "id": str(admin.id),
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role.value,
                "is_active": admin.is_active,
                "created_at": (
                    admin.created_at.isoformat() if admin.created_at else None
                ),
                "assigned_roles": role_list,
                "roles": role_names,
                "is_super_admin": "Super Admin" in role_names,
                "last_login_at": (
                    last_logins.get(admin.id).isoformat()
                    if last_logins.get(admin.id)
                    else None
                ),
                "active_sessions": session_counts.get(admin.id, 0),
            }
        )

    await log_admin_action(
        db=db,
        action="LIST_ADMINS",
        actor_admin_id=admin_ctx.user.id,
        permission_used="admins.view",
        request=request,
    )
    await db.commit()
    return {"admins": out}


@router.post("", status_code=201)
async def create_admin(
    req: AdminCreateReq,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    # Self-escalation check: check if requesting admin possesses the permissions of all requested roles
    if not admin_ctx.is_super_admin:
        for r_id in req.role_ids:
            try:
                role_uuid = uuid.UUID(r_id)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid role ID format: {r_id}"
                )

            stmt_role_perms = (
                select(AdminPermission.name)
                .join(
                    AdminRolePermission,
                    AdminPermission.id == AdminRolePermission.permission_id,
                )
                .where(AdminRolePermission.role_id == role_uuid)
            )
            r_perms = (await db.execute(stmt_role_perms)).scalars().all()
            missing = [p for p in r_perms if p not in admin_ctx.permissions]
            if missing:
                await log_admin_action(
                    db=db,
                    action="CREATE_ADMIN_SELF_ESCALATION_BLOCKED",
                    actor_admin_id=admin_ctx.user.id,
                    result="denied",
                    reason=f"Cannot assign role with unheld permissions: {missing}",
                    request=request,
                )
                await db.commit()
                raise HTTPException(
                    status_code=403,
                    detail=f"Self-escalation blocked: You cannot assign a role with permissions you do not possess ({missing}).",
                )

    # Check email exists
    stmt_check = select(User).where(User.email == req.email)
    existing = (await db.execute(stmt_check)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=409, detail="User with this email already exists."
        )

    new_admin = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=UserRole.admin,
        is_active=True,
    )
    db.add(new_admin)
    await db.flush()

    for r_id in req.role_ids:
        try:
            role_uuid = uuid.UUID(r_id)
            assign = AdminRoleAssignment(
                user_id=new_admin.id,
                role_id=role_uuid,
                assigned_by_id=admin_ctx.user.id,
            )
            db.add(assign)
        except ValueError:
            pass

    await log_admin_action(
        db=db,
        action="CREATE_ADMIN",
        actor_admin_id=admin_ctx.user.id,
        resource_type="User",
        resource_id=str(new_admin.id),
        permission_used="admins.manage",
        request=request,
        metadata={"created_email": req.email, "role_ids": req.role_ids},
    )
    await db.commit()

    return {"status": "ok", "id": str(new_admin.id), "email": new_admin.email}


@router.post("/{id}/deactivate")
async def deactivate_admin(
    id: str,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        admin_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID.")

    if admin_uuid == admin_ctx.user.id:
        raise HTTPException(
            status_code=400, detail="You cannot deactivate your own admin account."
        )

    stmt = select(User).where(User.id == admin_uuid, User.role == UserRole.admin)
    target_admin = (await db.execute(stmt)).scalars().first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Admin account not found.")

    target_admin.is_active = False

    # Remove all refresh sessions; the admin action records the revocation count.
    revoked_sessions = (
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == admin_uuid))
    ).rowcount or 0

    await log_admin_action(
        db=db,
        action="DEACTIVATE_ADMIN",
        actor_admin_id=admin_ctx.user.id,
        resource_type="User",
        resource_id=id,
        permission_used="admins.manage",
        request=request,
        metadata={"revoked_sessions": revoked_sessions},
    )
    await db.commit()

    return {
        "status": "ok",
        "message": f"Admin {target_admin.email} deactivated and sessions revoked.",
    }


@router.post("/{id}/reactivate")
async def reactivate_admin(
    id: str,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        admin_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID.")

    stmt = select(User).where(User.id == admin_uuid, User.role == UserRole.admin)
    target_admin = (await db.execute(stmt)).scalars().first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Admin account not found.")

    target_admin.is_active = True

    await log_admin_action(
        db=db,
        action="REACTIVATE_ADMIN",
        actor_admin_id=admin_ctx.user.id,
        resource_type="User",
        resource_id=id,
        permission_used="admins.manage",
        request=request,
    )
    await db.commit()

    return {"status": "ok", "message": f"Admin {target_admin.email} reactivated."}


@router.post("/{id}/roles")
async def assign_admin_roles(
    id: str,
    req: RoleAssignReq,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        admin_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID.")

    # Self-escalation check: non-super admin cannot grant unheld permissions
    if not admin_ctx.is_super_admin:
        for r_id in req.role_ids:
            try:
                role_uuid = uuid.UUID(r_id)
            except ValueError:
                continue
            stmt_role_perms = (
                select(AdminPermission.name)
                .join(
                    AdminRolePermission,
                    AdminPermission.id == AdminRolePermission.permission_id,
                )
                .where(AdminRolePermission.role_id == role_uuid)
            )
            r_perms = (await db.execute(stmt_role_perms)).scalars().all()
            missing = [p for p in r_perms if p not in admin_ctx.permissions]
            if missing:
                await log_admin_action(
                    db=db,
                    action="ROLE_ASSIGN_SELF_ESCALATION_BLOCKED",
                    actor_admin_id=admin_ctx.user.id,
                    resource_type="User",
                    resource_id=id,
                    result="denied",
                    reason=f"Cannot assign role with unheld permissions: {missing}",
                    request=request,
                )
                await db.commit()
                raise HTTPException(
                    status_code=403,
                    detail=f"Self-escalation blocked: You cannot assign a role with permissions you do not possess ({missing}).",
                )

    # Re-assign roles
    await db.execute(
        delete(AdminRoleAssignment).where(AdminRoleAssignment.user_id == admin_uuid)
    )
    for r_id in req.role_ids:
        try:
            role_uuid = uuid.UUID(r_id)
            assign = AdminRoleAssignment(
                user_id=admin_uuid, role_id=role_uuid, assigned_by_id=admin_ctx.user.id
            )
            db.add(assign)
        except ValueError:
            pass

    await log_admin_action(
        db=db,
        action="ROLE_CHANGE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="User",
        resource_id=id,
        permission_used="admins.manage",
        request=request,
        metadata={"assigned_role_ids": req.role_ids},
    )
    await db.commit()

    return {"status": "ok", "message": "Admin roles updated."}


@router.post("/{id}/force-logout")
async def force_logout_admin(
    id: str,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        admin_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID.")

    revoked_sessions = (
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == admin_uuid))
    ).rowcount or 0

    await log_admin_action(
        db=db,
        action="FORCE_LOGOUT_ADMIN",
        actor_admin_id=admin_ctx.user.id,
        resource_type="User",
        resource_id=id,
        permission_used="admins.manage",
        request=request,
        metadata={"revoked_sessions": revoked_sessions},
    )
    await db.commit()

    return {"status": "ok", "message": "Active sessions revoked for admin."}


@router.get("/{id}/audit_logs")
async def get_admin_audit_logs(
    id: str,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.view", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        admin_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID.")

    from app.models.admin import AdminAuditLog

    stmt = (
        select(AdminAuditLog)
        .where(AdminAuditLog.actor_admin_id == admin_uuid)
        .order_by(desc(AdminAuditLog.timestamp))
    )
    logs = (await db.execute(stmt)).scalars().all()

    return {
        "status": "ok",
        "logs": [
            {
                "id": str(l.id),
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "metadata_payload": l.metadata_payload,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ],
    }


@router.get("/{id}/support_tickets")
async def get_admin_support_tickets(
    id: str,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.view", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        admin_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID.")

    from app.models.support import SupportTicket

    stmt = (
        select(SupportTicket)
        .where(SupportTicket.assigned_to_id == admin_uuid)
        .order_by(desc(SupportTicket.created_at))
    )
    tickets = (await db.execute(stmt)).scalars().all()

    return {
        "status": "ok",
        "tickets": [
            {
                "id": str(t.id),
                "subject": t.subject,
                "status": t.status.value if t.status else "unknown",
                "priority": t.priority.value if t.priority else "unknown",
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ],
    }
