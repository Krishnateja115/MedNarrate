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
from app.services.fcm_service import send_push_notification

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
        users = (await db.execute(select(User.id).where(User.role == UserRole.clinician))).scalars().all()
        target_users.extend(users)
    elif payload.audience == "patients":
        users = (await db.execute(select(User.id).where(User.role == UserRole.patient))).scalars().all()
        target_users.extend(users)
    elif payload.audience == "caregivers":
        users = (await db.execute(select(User.id).where(User.role == UserRole.caregiver))).scalars().all()
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

    # 3. Dispatch and log it
    dispatched_count = 0
    failed_count = 0
    for tk in tokens:
        success = await send_push_notification(tk.token, payload.title, payload.body)
        status = "sent" if success else "failed"
        nl = NotificationLog(
            id=uuid.uuid4(),
            user_id=tk.user_id,
            notification_type="admin_dispatch",
            title=payload.title,
            body=payload.body,
            status=status,
            error_message=None if success else "Failed to send to push service",
            sent_at=datetime.now(timezone.utc)
        )
        db.add(nl)
        if success:
            dispatched_count += 1
        else:
            failed_count += 1

    await log_admin_action(
        db, admin_ctx, "NOTIFICATION_DISPATCH", "system", "global",
        {
            "audience": payload.audience,
            "target_users": len(target_users),
            "target_devices": len(tokens),
            "delivered": dispatched_count,
            "failed": failed_count,
            "skipped": 0,
        }, request
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

    # Find the push token for the user again
    tk_stmt = select(PushToken).where(PushToken.user_id == log_entry.user_id).order_by(desc(PushToken.updated_at)).limit(1)
    token = (await db.execute(tk_stmt)).scalars().first()
    if not token:
        raise HTTPException(status_code=400, detail="No registered device for user")

    success = await send_push_notification(token.token, log_entry.title, log_entry.body)

    log_entry.status = "sent" if success else "failed"
    log_entry.error_message = None if success else "Failed to send to push service"
    log_entry.sent_at = datetime.now(timezone.utc)

    await log_admin_action(
        db, admin_ctx, "NOTIFICATION_RETRY", "notification_log", str(log_id),
        {"success": success}, request
    )

    await db.commit()
    if not success:
        raise HTTPException(status_code=500, detail="Retry failed.")
    return {"status": "ok", "message": "Notification retried successfully"}
