from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, time, timedelta

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.user import User
from app.models.report import Report, ProcessingStatus
from app.models.incidents import Incident, IncidentStatus
from app.models.job_execution import JobExecution, JobStatus
from sqlalchemy import desc

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(
    admin_ctx: AdminContext = Depends(require_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    # Total Users
    total_users_stmt = select(func.count(User.id))
    total_users = (await db.execute(total_users_stmt)).scalar() or 0
    
    # Active Users
    active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_users = (await db.execute(active_users_stmt)).scalar() or 0

    # Reports Today
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(tzinfo=timezone.utc)
    reports_today_stmt = select(func.count(Report.id)).where(Report.uploaded_at >= today_start)
    reports_today = (await db.execute(reports_today_stmt)).scalar() or 0

    # Reports Processing & Failed
    reports_processing_stmt = select(func.count(Report.id)).where(Report.processing_status == ProcessingStatus.processing)
    reports_processing = (await db.execute(reports_processing_stmt)).scalar() or 0
    
    reports_failed_stmt = select(func.count(Report.id)).where(Report.processing_status == ProcessingStatus.failed)
    reports_failed = (await db.execute(reports_failed_stmt)).scalar() or 0

    reports_completed_stmt = select(func.count(Report.id)).where(Report.processing_status == ProcessingStatus.completed)
    reports_completed = (await db.execute(reports_completed_stmt)).scalar() or 0
    
    total_processed = reports_failed + reports_completed
    analysis_success_rate = (reports_completed / total_processed * 100) if total_processed > 0 else 0.0

    # Critical Incidents
    critical_incidents_stmt = select(func.count(Incident.id)).where(
        Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating, IncidentStatus.identified]),
        Incident.severity.in_(["SEV-1", "SEV-2"])
    )
    critical_incidents = (await db.execute(critical_incidents_stmt)).scalar() or 0

    open_incidents_stmt = select(func.count(Incident.id)).where(
        Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating, IncidentStatus.identified])
    )
    open_incidents = (await db.execute(open_incidents_stmt)).scalar() or 0

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "users": {
            "total_users": total_users,
            "active_users": active_users
        },
        "reports": {
            "reports_today": reports_today,
            "reports_processing": reports_processing,
            "reports_failed": reports_failed
        },
        "analysis": {
            "analysis_success_rate": round(analysis_success_rate, 2),
            "analysis_failure_count": reports_failed
        },
        "support": {
            "open_support_tickets": None  # Not currently instrumented
        },
        "incidents": {
            "critical_incidents": critical_incidents,
            "open_incidents": open_incidents
        }
    }

@router.get("/alerts")
async def get_dashboard_alerts(
    admin_ctx: AdminContext = Depends(require_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    """Aggregate recent critical errors, failed jobs, and incidents into an operational feed."""
    
    feed = []
    
    # 1. Fetch recently failed jobs
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    failed_jobs_stmt = select(JobExecution).where(
        JobExecution.status == JobStatus.failed,
        JobExecution.started_at >= yesterday
    ).order_by(desc(JobExecution.started_at)).limit(10)
    failed_jobs = (await db.execute(failed_jobs_stmt)).scalars().all()
    
    for job in failed_jobs:
        feed.append({
            "id": f"job-{job.id}",
            "type": "job_failure",
            "title": f"Job Failed: {job.job_name}",
            "description": job.error_message or "Unknown error",
            "severity": "medium",
            "timestamp": job.started_at.isoformat()
        })
        
    # 2. Fetch open incidents
    incidents_stmt = select(Incident).where(
        Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating, IncidentStatus.identified])
    ).order_by(desc(Incident.created_at)).limit(10)
    incidents = (await db.execute(incidents_stmt)).scalars().all()
    
    for inc in incidents:
        feed.append({
            "id": f"inc-{inc.id}",
            "type": "incident",
            "title": inc.title,
            "description": f"Severity: {inc.severity} - Status: {inc.status.value}",
            "severity": "high" if inc.severity in ["SEV-1", "SEV-2"] else "medium",
            "timestamp": inc.created_at.isoformat()
        })
        
    # Sort combined feed by timestamp descending
    feed.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "status": "ok",
        "alerts": feed[:20]
    }
