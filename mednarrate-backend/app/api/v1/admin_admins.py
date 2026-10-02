import uuid
from collections import defaultdict
from typing import Dict, List, Sequence, Set

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
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
    role_ids: List[str] = Field(default_factory=list)


class RoleAssignReq(BaseModel):
    role_ids: List[str]


SUPER_ADMIN_ROLE_NAME = "Super Admin"


def _parse_admin_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid admin ID.") from exc


def _parse_role_ids(values: Sequence[str]) -> List[uuid.UUID]:
    parsed: List[uuid.UUID] = []
    for value in values:
        try:
            role_id = uuid.UUID(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid role ID format: {value}"
            ) from exc
        if role_id not in parsed:
            parsed.append(role_id)
    return parsed


async def _get_admin_or_404(db: AsyncSession, admin_id: uuid.UUID) -> User:
    admin = (
        await db.execute(
            select(User).where(User.id == admin_id, User.role == UserRole.admin)
        )
    ).scalars().first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin account not found.")
    return admin


async def _load_roles_for_users(
    db: AsyncSession, user_ids: Sequence[uuid.UUID]
) -> Dict[uuid.UUID, List[AdminRole]]:
    roles_by_user: Dict[uuid.UUID, List[AdminRole]] = defaultdict(list)
    if not user_ids:
        return roles_by_user
    rows = (
        await db.execute(
            select(AdminRoleAssignment.user_id, AdminRole)
            .join(AdminRole, AdminRole.id == AdminRoleAssignment.role_id)
            .where(AdminRoleAssignment.user_id.in_(user_ids))
        )
    ).all()
    for user_id, role in rows:
        roles_by_user[user_id].append(role)
    return roles_by_user


async def _load_permissions_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> Set[str]:
    permissions = (
        await db.execute(
            select(AdminPermission.name)
            .select_from(AdminRoleAssignment)
            .join(
                AdminRolePermission,
                AdminRoleAssignment.role_id == AdminRolePermission.role_id,
            )
            .join(
                AdminPermission,
                AdminPermission.id == AdminRolePermission.permission_id,
            )
            .where(AdminRoleAssignment.user_id == user_id)
        )
    ).scalars().all()
    return set(permissions)


async def _assert_can_manage_target(
    db: AsyncSession,
    admin_ctx: AdminContext,
    target: User,
    *,
    block_self: bool = False,
) -> List[AdminRole]:
    if block_self and target.id == admin_ctx.user.id:
        raise HTTPException(
            status_code=400, detail="You cannot perform this action on your own account."
        )

    target_roles = (await _load_roles_for_users(db, [target.id])).get(target.id, [])
    target_is_super = any(role.name == SUPER_ADMIN_ROLE_NAME for role in target_roles)
    if target_is_super and not admin_ctx.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="Only a Super Admin can manage another Super Admin account.",
        )

    if not admin_ctx.is_super_admin:
        target_permissions = await _load_permissions_for_user(db, target.id)
        if not target_permissions.issubset(admin_ctx.permissions):
            raise HTTPException(
                status_code=403,
                detail="You cannot manage an administrator with greater privileges.",
            )
    return target_roles


async def _active_super_admin_count(db: AsyncSession) -> int:
    count = await db.scalar(
        select(func.count(func.distinct(User.id)))
        .select_from(User)
        .join(AdminRoleAssignment, AdminRoleAssignment.user_id == User.id)
        .join(AdminRole, AdminRole.id == AdminRoleAssignment.role_id)
        .where(
            User.role == UserRole.admin,
            User.is_active.is_(True),
            AdminRole.name == SUPER_ADMIN_ROLE_NAME,
        )
    )
    return int(count or 0)


def _serialize_admin(
    admin: User,
    roles: Sequence[AdminRole],
    session_count: int = 0,
    last_login: datetime | None = None,
) -> dict:
    role_list = [{"id": str(role.id), "name": role.name} for role in roles]
    role_names = [role["name"] for role in role_list]
    return {
        "id": str(admin.id),
        "email": admin.email,
        "full_name": admin.full_name,
        "role": admin.role.value,
        "is_active": admin.is_active,
        "created_at": admin.created_at.isoformat() if admin.created_at else None,
        "assigned_roles": role_list,
        "roles": role_names,
        "is_super_admin": SUPER_ADMIN_ROLE_NAME in role_names,
        "last_login_at": last_login.isoformat() if last_login else None,
        "active_sessions": session_count,
    }


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
    admin_ids = [admin.id for admin in admins]

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

    roles_by_user = await _load_roles_for_users(db, admin_ids)
    out = []
    for admin in admins:
        out.append(
            _serialize_admin(
                admin,
                roles_by_user.get(admin.id, []),
                session_counts.get(admin.id, 0),
                last_logins.get(admin.id),
            )
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


@router.get("/{id}")
async def get_admin(
    id: str,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.view", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    admin_uuid = _parse_admin_id(id)
    admin = await _get_admin_or_404(db, admin_uuid)
    roles = (await _load_roles_for_users(db, [admin_uuid])).get(admin_uuid, [])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session_count = await db.scalar(
        select(func.count(RefreshToken.id)).where(
            RefreshToken.user_id == admin_uuid,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
    )
    last_login = await db.scalar(
        select(func.max(AdminAuditLog.timestamp)).where(
            AdminAuditLog.actor_admin_id == admin_uuid,
            AdminAuditLog.action == "ADMIN_LOGIN_SUCCESS",
        )
    )
    return _serialize_admin(admin, roles, int(session_count or 0), last_login)


@router.post("", status_code=201)
async def create_admin(
    req: AdminCreateReq,
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["admins.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    role_ids = _parse_role_ids(req.role_ids)
    if not role_ids:
        raise HTTPException(status_code=400, detail="At least one role must be assigned during admin creation.")

    roles = (
        (
            await db.execute(select(AdminRole).where(AdminRole.id.in_(role_ids)))
        ).scalars().all()
    )
    if len(roles) != len(role_ids):
        raise HTTPException(status_code=400, detail="One or more roles do not exist.")

    # Self-escalation check: requesting admin must possess every granted permission.
    if not admin_ctx.is_super_admin:
        if any(role.name == SUPER_ADMIN_ROLE_NAME for role in roles):
            raise HTTPException(
                status_code=403, detail="Only a Super Admin can grant Super Admin."
            )
        requested_permissions = (
            (
                await db.execute(
                    select(AdminPermission.name)
                    .join(
                        AdminRolePermission,
                        AdminPermission.id == AdminRolePermission.permission_id,
                    )
                    .where(AdminRolePermission.role_id.in_(role_ids))
                )
            ).scalars().all()
            if role_ids
            else []
        )
        missing = sorted(
            permission
            for permission in set(requested_permissions)
            if not admin_ctx.has_permission(permission)
        )
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
                detail=f"Self-escalation blocked: unheld permissions {missing}.",
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

    for role_id in role_ids:
        db.add(
            AdminRoleAssignment(
                user_id=new_admin.id,
                role_id=role_id,
                assigned_by_id=admin_ctx.user.id,
            )
        )

    await log_admin_action(
        db=db,
        action="ADMIN_CREATED",
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
    admin_uuid = _parse_admin_id(id)
    target_admin = await _get_admin_or_404(db, admin_uuid)
    target_roles = await _assert_can_manage_target(
        db, admin_ctx, target_admin, block_self=True
    )
    target_is_super = any(role.name == SUPER_ADMIN_ROLE_NAME for role in target_roles)
    if (
        target_admin.is_active
        and target_is_super
        and await _active_super_admin_count(db) <= 1
    ):
        raise HTTPException(
            status_code=409,
            detail="Cannot deactivate the final active Super Admin.",
        )

    target_admin.is_active = False

    # Remove all refresh sessions; the admin action records the revocation count.
    revoked_sessions = (
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == admin_uuid))
    ).rowcount or 0

    await log_admin_action(
        db=db,
        action="ADMIN_DEACTIVATED",
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
    admin_uuid = _parse_admin_id(id)
    target_admin = await _get_admin_or_404(db, admin_uuid)
    await _assert_can_manage_target(db, admin_ctx, target_admin)

    target_admin.is_active = True

    await log_admin_action(
        db=db,
        action="ADMIN_REACTIVATED",
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
    admin_uuid = _parse_admin_id(id)
    target_admin = await _get_admin_or_404(db, admin_uuid)
    current_roles = await _assert_can_manage_target(db, admin_ctx, target_admin)
    role_ids = _parse_role_ids(req.role_ids)
    requested_roles = (
        (
            await db.execute(select(AdminRole).where(AdminRole.id.in_(role_ids)))
        ).scalars().all()
        if role_ids
        else []
    )
    if len(requested_roles) != len(role_ids):
        raise HTTPException(status_code=400, detail="One or more roles do not exist.")

    currently_super = any(role.name == SUPER_ADMIN_ROLE_NAME for role in current_roles)
    remains_super = any(
        role.name == SUPER_ADMIN_ROLE_NAME for role in requested_roles
    )
    if (
        target_admin.is_active
        and currently_super
        and not remains_super
        and await _active_super_admin_count(db) <= 1
    ):
        raise HTTPException(
            status_code=409,
            detail="Cannot remove Super Admin from the final active Super Admin.",
        )

    # Self-escalation check: non-super admin cannot grant unheld permissions
    if not admin_ctx.is_super_admin:
        if any(role.name == SUPER_ADMIN_ROLE_NAME for role in requested_roles):
            raise HTTPException(
                status_code=403, detail="Only a Super Admin can grant Super Admin."
            )
        requested_permissions = (
            (
                await db.execute(
                    select(AdminPermission.name)
                    .join(
                        AdminRolePermission,
                        AdminPermission.id == AdminRolePermission.permission_id,
                    )
                    .where(AdminRolePermission.role_id.in_(role_ids))
                )
            ).scalars().all()
            if role_ids
            else []
        )
        missing = sorted(
            permission
            for permission in set(requested_permissions)
            if not admin_ctx.has_permission(permission)
        )
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
                detail=f"Self-escalation blocked: unheld permissions {missing}.",
            )

    # Re-assign roles
    await db.execute(
        delete(AdminRoleAssignment).where(AdminRoleAssignment.user_id == admin_uuid)
    )
    for role_id in role_ids:
        db.add(
            AdminRoleAssignment(
                user_id=admin_uuid,
                role_id=role_id,
                assigned_by_id=admin_ctx.user.id,
            )
        )

    await log_admin_action(
        db=db,
        action="ADMIN_ROLE_CHANGED",
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
    admin_uuid = _parse_admin_id(id)
    target_admin = await _get_admin_or_404(db, admin_uuid)
    await _assert_can_manage_target(db, admin_ctx, target_admin, block_self=True)

    revoked_sessions = (
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == admin_uuid))
    ).rowcount or 0

    await log_admin_action(
        db=db,
        action="ADMIN_FORCE_LOGOUT",
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

    from app.models.user import User, UserRole

    admin_exists = (
        (
            await db.execute(
                select(User.id).where(
                    User.id == admin_uuid, User.role == UserRole.admin
                )
            )
        )
        .scalars()
        .first()
    )
    if not admin_exists:
        raise HTTPException(status_code=404, detail="Admin not found.")

    from app.models.support import SupportTicket

    stmt = (
        select(SupportTicket)
        .where(SupportTicket.assigned_admin_id == admin_uuid)
        .order_by(desc(SupportTicket.created_at))
    )
    tickets = (await db.execute(stmt)).scalars().all()

    return {
        "status": "ok",
        "tickets": [
            {
                "id": str(t.id),
                "subject": t.title,
                "status": t.status.value if t.status else "unknown",
                "priority": t.priority.value if t.priority else "unknown",
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ],
    }
