from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.notification_log import NotificationLog
from app.models.medication_schedule import MedicationSchedule
from app.models.job_execution import JobExecution
from app.services.audit import log_admin_action

router = APIRouter()

@router.get("/notifications")
async def list_notifications(
    status: Optional[str] = None,
    search: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("automation.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationLog).order_by(desc(NotificationLog.sent_at)).limit(50)
    
    if status:
        stmt = stmt.where(NotificationLog.status == status)
    if search:
        stmt = stmt.where(or_(
            NotificationLog.user_id.ilike(f"%{search}%"),
            NotificationLog.title.ilike(f"%{search}%")
        ))
        
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return {
        "status": "ok",
        "notifications": [
            {
                "id": n.id,
                "user_id": n.user_id,
                "title": n.title,
                "status": n.status,
                "error_message": n.error_message,
                "sent_at": n.sent_at
            } for n in logs
        ]
    }

@router.post("/notifications/{log_id}/retry")
async def retry_notification(
    log_id: str,
    admin_ctx: AdminContext = Depends(require_permission("automation.manage")),
    db: AsyncSession = Depends(get_db)
):
    log = await db.get(NotificationLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    # In a real implementation, this would enqueue a background task to actually send it again
    # For now, we update the status back to pending/retrying
    log.status = "retrying"
    
    await log_admin_action(
        db=db,
        action="NOTIFICATION_RETRY",
        actor_admin_id=admin_ctx.user.id,
        resource_type="NotificationLog",
        resource_id=log.id
    )
    await db.commit()
    return {"status": "ok", "message": "Notification queued for retry"}

@router.get("/medications")
async def list_medications(
    active_only: bool = False,
    admin_ctx: AdminContext = Depends(require_permission("automation.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).order_by(desc(MedicationSchedule.created_at)).limit(50)
    if active_only:
        stmt = stmt.where(MedicationSchedule.is_active == True)
        
    result = await db.execute(stmt)
    meds = result.scalars().all()
    
    return {
        "status": "ok",
        "schedules": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "medication_name": m.medication_name,
                "is_active": m.is_active,
                "times_of_day": m.times_of_day,
                "created_at": m.created_at
            } for m in meds
        ]
    }

@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("automation.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(JobExecution).order_by(desc(JobExecution.started_at)).limit(50)
    if status:
        stmt = stmt.where(JobExecution.status == status)
        
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    return {
        "status": "ok",
        "jobs": [
            {
                "id": j.id,
                "job_name": j.job_name,
                "status": j.status,
                "duration_seconds": j.duration_seconds,
                "failure_category": j.failure_category,
                "started_at": j.started_at,
                "finished_at": j.finished_at
            } for j in jobs
        ]
    }
