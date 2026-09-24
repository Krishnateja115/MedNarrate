from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_
from typing import Optional
from pydantic import BaseModel
from fastapi import Query
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.notification_log import NotificationLog
from app.models.medication_schedule import MedicationSchedule
from app.models.job_execution import JobExecution
from app.models.push_token import PushToken
from app.services.audit import log_admin_action
from app.services.notification_service import send_push_notification

router = APIRouter()

@router.get("/notifications")
async def list_notifications(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("sent_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("automation.view")),
    db: AsyncSession = Depends(get_db)
):
    limit = clamp_limit(limit)
    stmt = select(NotificationLog)
    
    if status:
        stmt = stmt.where(NotificationLog.status == status)
    if search:
        stmt = stmt.where(or_(
            NotificationLog.user_id.cast(str).ilike(f"%{search}%"),
            NotificationLog.title.ilike(f"%{search}%")
        ))
        
    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = getattr(NotificationLog, sort_by, NotificationLog.sent_at)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)
        
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    items = [
        {
            "id": str(n.id),
            "user_id": str(n.user_id),
            "title": n.title,
            "status": n.status,
            "error_message": n.error_message,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None
        } for n in logs
    ]
    
    return build_pagination_response(items, total, page, limit)

@router.post("/notifications/{log_id}/retry")
async def retry_notification(
    log_id: str,
    admin_ctx: AdminContext = Depends(require_permission("automation.manage")),
    db: AsyncSession = Depends(get_db)
):
    log = await db.get(NotificationLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    # Get user tokens
    tokens_stmt = select(PushToken).where(PushToken.user_id == log.user_id)
    tokens_res = await db.execute(tokens_stmt)
    tokens = tokens_res.scalars().all()
    
    if not tokens:
        log.status = "failed"
        log.error_message = "No device tokens found for user during retry"
        await db.commit()
        return {"status": "failed", "message": "No device tokens found"}
        
    # Re-send via the existing notification service
    # Since a single log represents the notification attempt, we update it based on the outcome of the first token
    # In a fully robust system, each token might have its own log or delivery receipt
    success = False
    for tk in tokens:
        result = await send_push_notification(db, str(log.user_id), tk.device_token, log.title, log.body, existing_log=log)
        if result:
            success = True
    
    await log_admin_action(
        db=db,
        action="NOTIFICATION_RETRY",
        actor_admin_id=admin_ctx.user.id,
        resource_type="NotificationLog",
        resource_id=log.id,
        metadata={"success": success}
    )
    await db.commit()
    
    return {
        "status": "ok" if success else "failed",
        "message": "Notification retry completed",
        "log_status": log.status
    }

@router.get("/medications")
async def list_medications(
    active_only: bool = False,
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("automation.view")),
    db: AsyncSession = Depends(get_db)
):
    limit = clamp_limit(limit)
    stmt = select(MedicationSchedule)
    if active_only:
        stmt = stmt.where(MedicationSchedule.is_active == True)
        
    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = getattr(MedicationSchedule, sort_by, MedicationSchedule.created_at)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)

    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    result = await db.execute(stmt)
    meds = result.scalars().all()
    
    items = [
        {
            "id": str(m.id),
            "user_id": str(m.user_id),
            "medication_name": m.medication_name,
            "is_active": m.is_active,
            "times_of_day": m.times_of_day,
            "created_at": m.created_at.isoformat() if m.created_at else None
        } for m in meds
    ]
    
    return build_pagination_response(items, total, page, limit)

@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    sort_by: str = Query("started_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("automation.view")),
    db: AsyncSession = Depends(get_db)
):
    limit = clamp_limit(limit)
    stmt = select(JobExecution)
    if status:
        stmt = stmt.where(JobExecution.status == status)
        
    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = getattr(JobExecution, sort_by, JobExecution.started_at)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)

    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    items = [
        {
            "id": str(j.id),
            "job_name": j.job_name,
            "status": j.status.value if hasattr(j.status, 'value') else j.status,
            "duration_seconds": j.duration_seconds,
            "failure_category": j.failure_category,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None
        } for j in jobs
    ]
    
    return build_pagination_response(items, total, page, limit)
