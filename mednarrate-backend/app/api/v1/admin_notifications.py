import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset
from app.models.notification_log import NotificationLog
from app.models.push_token import PushToken
from app.services.audit import log_admin_action

router = APIRouter()

class DispatchNotificationRequest(BaseModel):
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    user_id: Optional[uuid.UUID] = None
    audience: Optional[str] = "all"  # 'all', 'doctors', 'patients', 'caregivers', 'specific_user'
    
@router.post("/dispatch")
async def dispatch_global_notification(
    payload: DispatchNotificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("notifications.manage")),
):
    from app.models.user import User, UserRole
    
    # 1. Determine target users
    target_users = []
    if payload.audience == "specific_user" and payload.user_id:
        target_users.append(payload.user_id)
    elif payload.audience == "doctors":
        users = (await db.execute(select(User.id).where(User.role == UserRole.DOCTOR))).scalars().all()
        target_users.extend(users)
    elif payload.audience == "patients":
        users = (await db.execute(select(User.id).where(User.role == UserRole.PATIENT))).scalars().all()
        target_users.extend(users)
    elif payload.audience == "caregivers":
        users = (await db.execute(select(User.id).where(User.role == UserRole.CAREGIVER))).scalars().all()
        target_users.extend(users)
    else:
        # All users
        users = (await db.execute(select(User.id))).scalars().all()
        target_users.extend(users)
        
    if not target_users:
        return {"status": "ok", "message": "No target users found for this audience.", "dispatched_count": 0}

    # 2. Find push tokens
    stmt = select(PushToken).where(PushToken.user_id.in_(target_users))
    tokens = (await db.execute(stmt)).scalars().all()
    
    if not tokens:
        return {"status": "ok", "message": "No devices registered for target audience.", "dispatched_count": 0}
        
    # 3. Simulate dispatch and log it
    dispatched_count = 0
    for tk in tokens:
        nl = NotificationLog(
            id=uuid.uuid4(),
            user_id=tk.user_id,
            notification_type="admin_dispatch",
            title=payload.title,
            body=payload.body,
            status="sent",
            sent_at=datetime.now(timezone.utc)
        )
        db.add(nl)
        dispatched_count += 1
        
    await log_admin_action(
        db, admin_ctx, "NOTIFICATION_DISPATCH", "system", "global", 
        {"audience": payload.audience, "dispatched_count": dispatched_count}, request
    )
    
    await db.commit()
    return {"status": "ok", "message": f"Successfully dispatched to {dispatched_count} devices.", "dispatched_count": dispatched_count}

@router.get("/logs")
async def get_notification_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("notifications.view")),
):
    limit = clamp_limit(limit)
    stmt = select(NotificationLog)
    
    if status_filter:
        stmt = stmt.where(NotificationLog.status == status_filter)
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    stmt = stmt.order_by(desc(NotificationLog.sent_at)).offset(page_to_offset(page, limit)).limit(limit)
    logs = (await db.execute(stmt)).scalars().all()
    
    items = [
        {
            "id": str(l.id),
            "user_id": str(l.user_id),
            "notification_type": l.notification_type,
            "title": l.title,
            "status": l.status,
            "error_message": l.error_message,
            "sent_at": l.sent_at.isoformat() if l.sent_at else None
        }
        for l in logs
    ]
    
    return build_pagination_response(items, total_count, page, limit)

@router.post("/{log_id}/retry")
async def retry_notification(
    log_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("notifications.manage")),
):
    stmt = select(NotificationLog).where(NotificationLog.id == log_id)
    log_entry = (await db.execute(stmt)).scalars().first()
    if not log_entry:
        raise HTTPException(status_code=404, detail="Notification log not found")
        
    if log_entry.status == "sent":
        raise HTTPException(status_code=400, detail="Notification was already sent successfully")
        
    log_entry.status = "sent"
    log_entry.error_message = None
    log_entry.sent_at = datetime.now(timezone.utc)
    
    await log_admin_action(
        db, admin_ctx, "NOTIFICATION_RETRY", "notification_log", str(log_id), {}, request
    )
    
    await db.commit()
    return {"status": "ok", "message": "Notification retried successfully"}
