import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.privacy import PrivacyDataRequest
from app.models.admin import AdminAuditLog
from app.models.user import User
from app.core.admin_auth import AdminContext, require_permission
from app.services.audit import log_admin_action

router = APIRouter()

class PrivacyStatusUpdate(BaseModel):
    status: str  # under_review, approved, processing, completed, rejected
    admin_notes: Optional[str] = None

@router.get("/privacy/requests")
async def list_privacy_requests(
    request: Request,
    request_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("privacy:read"))
):
    query = select(PrivacyDataRequest).order_by(desc(PrivacyDataRequest.requested_at))
    if request_type:
        query = query.where(PrivacyDataRequest.request_type == request_type)
    if status:
        query = query.where(PrivacyDataRequest.status == status)

    res = await db.execute(query)
    reqs = res.scalars().all()

    user_ids = list({r.user_id for r in reqs if r.user_id})
    users_map = {}
    if user_ids:
        u_stmt = select(User).where(User.id.in_(user_ids))
        u_res = await db.execute(u_stmt)
        for u in u_res.scalars().all():
            users_map[str(u.id)] = {"email": u.email, "full_name": u.full_name}

    items = []
    for r in reqs:
        u_info = users_map.get(str(r.user_id), {"email": "Unknown User", "full_name": None})
        items.append({
            "id": str(r.id),
            "user_id": str(r.user_id),
            "user_email": u_info["email"],
            "user_full_name": u_info["full_name"],
            "request_type": r.request_type,
            "status": r.status,
            "reason": r.reason,
            "admin_notes": r.admin_notes,
            "requested_at": r.requested_at.isoformat() if r.requested_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })

    return {"requests": items}

@router.patch("/privacy/requests/{req_id}/status")
async def update_privacy_request_status(
    req_id: str,
    payload: PrivacyStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("privacy:manage"))
):
    try:
        r_uuid = uuid.UUID(req_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")

    res = await db.execute(select(PrivacyDataRequest).where(PrivacyDataRequest.id == r_uuid))
    p_req = res.scalar_one_or_none()
    if not p_req:
        raise HTTPException(status_code=404, detail="Privacy request not found")

    valid_statuses = ["requested", "under_review", "approved", "processing", "completed", "rejected"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    p_req.status = payload.status
    if payload.admin_notes is not None:
        p_req.admin_notes = payload.admin_notes
    p_req.reviewed_at = now
    p_req.reviewed_by_id = admin_ctx.user_id

    if payload.status in ["completed", "rejected"]:
        p_req.completed_at = now

    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="privacy_request_status_update",
        resource_type="privacy_request",
        resource_id=str(p_req.id),
        permission_used="privacy:manage",
        result="success",
        reason=f"Status updated to {payload.status}",
        request=request,
        metadata={"new_status": payload.status, "admin_notes": payload.admin_notes},
        sensitive_access_flag=True
    )

    return {"message": "Privacy request status updated successfully", "request_id": str(p_req.id), "status": p_req.status}

@router.get("/privacy/sensitive-access-history")
async def get_sensitive_access_history(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("privacy:read"))
):
    stmt = select(AdminAuditLog).where(AdminAuditLog.sensitive_access_flag == True).order_by(desc(AdminAuditLog.timestamp)).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": str(log.id),
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "actor_admin_id": str(log.actor_admin_id) if log.actor_admin_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "reason": log.reason,
            "result": log.result,
            "ip_address": log.ip_address,
        })

    return {"sensitive_access_logs": items}
