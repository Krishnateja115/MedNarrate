"""
Admin Jobs API.

Provides paginated, filterable access to background job history and scheduler state.
No fabricated values — all data comes from actual JobExecution records and APScheduler.
"""
import uuid
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from app.core.admin_auth import AdminContext, require_permission
from app.services.scheduler import get_all_jobs
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.job_execution import JobExecution
from app.core.pagination import build_pagination_response, page_to_offset, clamp_limit

router = APIRouter()

# Whitelist of sortable fields to prevent injection via user-supplied sort param
ALLOWED_SORT_FIELDS = {"started_at", "finished_at", "job_name", "status", "duration_seconds"}


@router.get("")
async def get_background_jobs(
    admin_ctx: AdminContext = Depends(require_permission("jobs.view")),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    job_name: Optional[str] = None,
    sort_by: str = Query("started_at", description=f"Sort field. Allowed: {', '.join(ALLOWED_SORT_FIELDS)}"),
):
    """List paginated job execution history with filtering."""
    limit = clamp_limit(limit)

    # Validate sort field against whitelist
    if sort_by not in ALLOWED_SORT_FIELDS:
        sort_by = "started_at"

    stmt = select(JobExecution)
    if status:
        stmt = stmt.where(JobExecution.status == status)
    if job_name:
        stmt = stmt.where(JobExecution.job_name.ilike(f"%{job_name}%"))

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort (whitelisted field)
    sort_col = getattr(JobExecution, sort_by, JobExecution.started_at)
    stmt = stmt.order_by(desc(sort_col)).offset(page_to_offset(page, limit)).limit(limit)
    history_res = await db.execute(stmt)
    history = history_res.scalars().all()

    # Fetch scheduler state (live jobs)
    scheduler_jobs = get_all_jobs()

    items = [
        {
            "id": str(h.id),
            "job_name": h.job_name,
            "status": h.status.value if hasattr(h.status, "value") else h.status,
            "started_at": h.started_at.isoformat() if h.started_at else None,
            "finished_at": h.finished_at.isoformat() if h.finished_at else None,
            "duration_seconds": h.duration_seconds,
            "error_message": h.error_message,
            "resource_id": getattr(h, "resource_id", None),
        }
        for h in history
    ]

    return {
        **build_pagination_response(items, total, page, limit),
        "scheduler_jobs": scheduler_jobs,
    }


@router.get("/{job_id}")
async def get_job_detail(
    job_id: str,
    admin_ctx: AdminContext = Depends(require_permission("jobs.view")),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific job execution."""
    try:
        j_uuid = uuid.UUID(job_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    res = await db.execute(select(JobExecution).where(JobExecution.id == j_uuid))
    job = res.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": str(job.id),
        "job_name": job.job_name,
        "status": job.status.value if hasattr(job.status, "value") else job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "duration_seconds": job.duration_seconds,
        "error_message": job.error_message,
        "resource_id": getattr(job, "resource_id", None),
        # Never include internal connection strings or credentials in error details
    }
