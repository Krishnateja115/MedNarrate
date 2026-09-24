import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset
from app.models.admin import AdminAuditLog
from app.models.user import User

router = APIRouter()


@router.get("/audit-logs")
async def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    result_status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("audit_logs:read")),
):
    limit = clamp_limit(limit)
    query = select(AdminAuditLog)

    if action:
        query = query.where(AdminAuditLog.action.ilike(f"%{action}%"))
    if actor_id:
        try:
            actor_uuid = uuid.UUID(actor_id)
            query = query.where(AdminAuditLog.actor_admin_id == actor_uuid)
        except ValueError:
            pass
    if resource_type:
        query = query.where(AdminAuditLog.resource_type == resource_type)
    if result_status:
        query = query.where(AdminAuditLog.result == result_status)
    if search:
        query = query.where(
            or_(
                AdminAuditLog.action.ilike(f"%{search}%"),
                AdminAuditLog.resource_id.ilike(f"%{search}%"),
                AdminAuditLog.reason.ilike(f"%{search}%"),
            )
        )

    # Total count
    count_stmt = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paginate and order
    query = (
        query.order_by(desc(AdminAuditLog.timestamp))
        .offset(page_to_offset(page, limit))
        .limit(limit)
    )
    res = await db.execute(query)
    logs = res.scalars().all()

    # Pre-fetch actor emails/names
    actor_ids = list({log.actor_admin_id for log in logs if log.actor_admin_id})
    actors_map = {}
    if actor_ids:
        u_stmt = select(User).where(User.id.in_(actor_ids))
        u_res = await db.execute(u_stmt)
        for u in u_res.scalars().all():
            actors_map[str(u.id)] = {"email": u.email, "full_name": u.full_name}

    items = []
    for log in logs:
        actor_info = (
            actors_map.get(
                str(log.actor_admin_id),
                {"email": "System / Unknown", "full_name": None},
            )
            if log.actor_admin_id
            else {"email": "System / Automated", "full_name": "System"}
        )
        items.append(
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "actor": {
                    "id": str(log.actor_admin_id) if log.actor_admin_id else None,
                    "email": actor_info["email"],
                    "full_name": actor_info["full_name"],
                },
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "permission_used": log.permission_used,
                "result": log.result,
                "reason": log.reason,
                "request_id": log.request_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "metadata": log.metadata_payload or {},
                "sensitive_access_flag": log.sensitive_access_flag,
            }
        )

    return build_pagination_response(items, total, page, limit)


@router.get("/audit-logs/{log_id}")
async def get_audit_log_detail(
    log_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("audit_logs:read")),
):
    try:
        l_uuid = uuid.UUID(log_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log ID format")

    res = await db.execute(select(AdminAuditLog).where(AdminAuditLog.id == l_uuid))
    log = res.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    actor_info = {"email": "System / Automated", "full_name": "System"}
    if log.actor_admin_id:
        u_res = await db.execute(select(User).where(User.id == log.actor_admin_id))
        user = u_res.scalar_one_or_none()
        if user:
            actor_info = {"email": user.email, "full_name": user.full_name}

    return {
        "id": str(log.id),
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "actor": {
            "id": str(log.actor_admin_id) if log.actor_admin_id else None,
            "email": actor_info["email"],
            "full_name": actor_info["full_name"],
        },
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "permission_used": log.permission_used,
        "result": log.result,
        "reason": log.reason,
        "request_id": log.request_id,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "metadata": log.metadata_payload or {},
        "sensitive_access_flag": log.sensitive_access_flag,
    }
