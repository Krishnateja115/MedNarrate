from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.admin_auth import AdminContext, get_admin_context, require_permission, require_any_permission
from app.services.audit import log_admin_action
from app.models.admin import AdminAuditLog, SensitiveAccessGrant, AdminRoleAssignment
from app.models.user import User, UserRole
from app.models.privacy import PrivacyDataRequest

router = APIRouter()

@router.get("/overview")
async def get_security_overview(
    request: Request,
    admin_ctx: AdminContext = Depends(require_any_permission(["security.view", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    await log_admin_action(
        db=db,
        action="VIEW_SECURITY_OVERVIEW",
        actor_admin_id=admin_ctx.user.id,
        permission_used="security.view",
        request=request
    )
    await db.commit()

    # Total Admin Accounts
    stmt_admins = select(func.count(User.id)).where(User.role == UserRole.admin)
    total_admins = (await db.execute(stmt_admins)).scalar() or 0

    # Active Break-glass Grants
    stmt_grants = select(func.count(SensitiveAccessGrant.id)).where(SensitiveAccessGrant.status == "active")
    active_grants = (await db.execute(stmt_grants)).scalar() or 0

    # Total Audit Logs
    stmt_audits = select(func.count(AdminAuditLog.id))
    total_audits = (await db.execute(stmt_audits)).scalar() or 0

    # Pending Privacy Requests
    stmt_privacy = select(func.count(PrivacyDataRequest.id)).where(PrivacyDataRequest.status.in_(["requested", "under_review"]))
    pending_privacy_requests = (await db.execute(stmt_privacy)).scalar() or 0

    # Security Events in Audit Logs
    stmt_sec_events = select(func.count(AdminAuditLog.id)).where(
        AdminAuditLog.action.in_([
            "FAILED_ADMIN_LOGIN", "ADMIN_LOGIN_SUCCESS", "SESSION_REVOCATION",
            "ROLE_CHANGE", "PERMISSION_CHANGE", "SUSPICIOUS_ACCESS", "BREAK_GLASS_ACCESS"
        ])
    )
    total_security_events = (await db.execute(stmt_sec_events)).scalar() or 0

    return {
        "status": "ok",
        "total_admins": total_admins,
        "active_breakglass_grants": active_grants,
        "total_audit_logs": total_audits,
        "pending_privacy_requests": pending_privacy_requests,
        "total_security_events": total_security_events
    }

@router.get("/events")
async def get_security_events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    admin_ctx: AdminContext = Depends(require_any_permission(["security.view", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AdminAuditLog).order_by(desc(AdminAuditLog.timestamp))
    
    if event_type:
        stmt = stmt.where(AdminAuditLog.action == event_type)
    else:
        # Default to security-relevant event types
        stmt = stmt.where(
            AdminAuditLog.action.in_([
                "FAILED_ADMIN_LOGIN", "ADMIN_LOGIN_SUCCESS", "SESSION_REVOCATION",
                "ROLE_CHANGE", "PERMISSION_CHANGE", "SUSPICIOUS_ACCESS", "BREAK_GLASS_ACCESS",
                "DEACTIVATE_ADMIN", "REACTIVATE_ADMIN", "CREATE_ADMIN", "FORCE_LOGOUT_ADMIN"
            ])
        )

    if result:
        stmt = stmt.where(AdminAuditLog.result == result)

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    events_out = []
    for log in logs:
        # Never expose secrets/passwords/tokens/secrets in events
        events_out.append({
            "id": str(log.id),
            "timestamp": log.timestamp.isoformat(),
            "actor_admin_id": str(log.actor_admin_id) if log.actor_admin_id else "System",
            "event": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "result": log.result,
            "reason": log.reason,
            "request_id": log.request_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "metadata": log.metadata_payload or {}
        })

    await log_admin_action(
        db=db,
        action="VIEW_SECURITY_EVENTS",
        actor_admin_id=admin_ctx.user.id,
        permission_used="security.view",
        request=request
    )
    await db.commit()

    return events_out
