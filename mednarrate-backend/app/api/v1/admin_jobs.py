from fastapi import APIRouter, Depends
from typing import List

from app.core.admin_auth import AdminContext, require_permission
from app.services.scheduler import get_all_jobs
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.job_execution import JobExecution

router = APIRouter()

@router.get("")
async def get_background_jobs(
    admin_ctx: AdminContext = Depends(require_permission("jobs.view")),
    db: AsyncSession = Depends(get_db)
):
    # Fetch operational jobs scheduled in APScheduler
    jobs = get_all_jobs()
    
    # Fetch historical jobs (last 20 executions)
    history_stmt = select(JobExecution).order_by(desc(JobExecution.started_at)).limit(20)
    history_res = await db.execute(history_stmt)
    history = history_res.scalars().all()
    
    return {
        "status": "ok",
        "jobs": jobs,
        "history": [
            {
                "id": str(h.id),
                "job_name": h.job_name,
                "status": h.status.value,
                "started_at": h.started_at.isoformat(),
                "finished_at": h.finished_at.isoformat() if h.finished_at else None,
                "duration_seconds": h.duration_seconds,
                "error_message": h.error_message
            } for h in history
        ]
    }
