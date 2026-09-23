import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, String
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission, require_all_permissions
from app.models.user import User, UserRole
from app.models.admin import AdminAuditLog
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.core.security import hash_password

router = APIRouter()

class ChangeRoleRequest(BaseModel):
    role: UserRole

async def log_admin_action(
    db: AsyncSession,
    admin_ctx: AdminContext,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata_payload: dict,
    request: Request
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    audit_log = AdminAuditLog(
        actor_admin_id=admin_ctx.user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_payload=metadata_payload,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    await db.commit()

@router.get("")
async def get_users(
    request: Request,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
):
    stmt = select(User)
    
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.id.cast(String).ilike(search_term) if search.replace('-', '').isalnum() else False
            )
        )
        
    if role:
        stmt = stmt.where(User.role == role)
        
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        
    # Count total matching records
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    # Paginate and fetch
    stmt = stmt.order_by(desc(User.created_at)).offset(offset).limit(limit)
    users = (await db.execute(stmt)).scalars().all()
    
    return {
        "status": "ok",
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "preferred_language": u.preferred_language,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None
            } for u in users
        ],
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/{user_id}")
async def get_user_detail(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    # Fetch report count for this user
    from app.models.report import Report
    report_count_stmt = select(func.count(Report.id)).where(Report.user_id == user_id)
    report_count = (await db.execute(report_count_stmt)).scalar() or 0
    
    # Check last login (approximate via latest refresh token created_at)
    last_login_stmt = select(RefreshToken.created_at).where(RefreshToken.user_id == user_id).order_by(desc(RefreshToken.created_at)).limit(1)
    last_login = (await db.execute(last_login_stmt)).scalar()
    
    return {
        "status": "ok",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "preferred_language": user.preferred_language,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "reports_count": report_count,
            "last_login": last_login.isoformat() if last_login else None
        }
    }

@router.post("/{user_id}/actions/suspend")
async def suspend_user(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == admin_ctx.user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
        
    user.is_active = False
    await log_admin_action(db, admin_ctx, "USER_SUSPEND", "user", str(user.id), {"email": user.email}, request)
    
    return {"status": "ok", "message": f"User {user.email} suspended"}

@router.post("/{user_id}/actions/activate")
async def activate_user(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = True
    await log_admin_action(db, admin_ctx, "USER_ACTIVATE", "user", str(user.id), {"email": user.email}, request)
    
    return {"status": "ok", "message": f"User {user.email} activated"}

@router.post("/{user_id}/actions/force_logout")
async def force_logout(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    tokens = (await db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))).scalars().all()
    count = 0
    for t in tokens:
        if not t.revoked:
            t.revoked = True
            count += 1
            
    await log_admin_action(db, admin_ctx, "USER_FORCE_LOGOUT", "user", str(user.id), {"sessions_revoked": count}, request)
    
    return {"status": "ok", "message": f"Revoked {count} active sessions"}

@router.post("/{user_id}/actions/change_role")
async def change_role(
    request: Request,
    user_id: uuid.UUID,
    payload: ChangeRoleRequest,
    admin_ctx: AdminContext = Depends(require_all_permissions(["users.manage", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == admin_ctx.user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
        
    old_role = user.role
    user.role = payload.role
    
    await log_admin_action(db, admin_ctx, "USER_ROLE_CHANGE", "user", str(user.id), {"old_role": old_role.value, "new_role": payload.role.value}, request)
    
    return {"status": "ok", "message": f"Role changed from {old_role.value} to {payload.role.value}"}

@router.post("/{user_id}/actions/reset_password")
async def reset_password(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    import secrets
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_password(raw_token)
    
    pr_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(pr_token)
    
    await log_admin_action(db, admin_ctx, "USER_PASSWORD_RESET_GENERATED", "user", str(user.id), {}, request)
    
    # Return the raw token for the admin to distribute securely
    reset_link = f"https://app.mednarrate.com/reset-password?token={raw_token}"
    return {"status": "ok", "reset_link": reset_link, "message": "Password reset link generated securely."}
