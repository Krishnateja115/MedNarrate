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
from app.models.report_analysis import ReportAnalysis
from sqlalchemy import desc, cast, Date

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(
    days: int = 30,
    admin_ctx: AdminContext = Depends(require_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    time_window_start = datetime.now(timezone.utc) - timedelta(days=days)

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

    # Reports Processing & Failed (Time Window)
    reports_processing_stmt = select(func.count(Report.id)).where(
        Report.processing_status == ProcessingStatus.processing,
        Report.uploaded_at >= time_window_start
    )
    reports_processing = (await db.execute(reports_processing_stmt)).scalar() or 0
    
    reports_failed_stmt = select(func.count(Report.id)).where(
        Report.processing_status == ProcessingStatus.failed,
        Report.uploaded_at >= time_window_start
    )
    reports_failed = (await db.execute(reports_failed_stmt)).scalar() or 0

    reports_completed_stmt = select(func.count(Report.id)).where(
        Report.processing_status == ProcessingStatus.completed,
        Report.uploaded_at >= time_window_start
    )
    reports_completed = (await db.execute(reports_completed_stmt)).scalar() or 0
    
    total_processed = reports_failed + reports_completed
    analysis_success_rate = (reports_completed / total_processed * 100) if total_processed > 0 else 0.0

    # Failure Category Breakdown
    failure_category_stmt = select(ReportAnalysis.failure_category, func.count(Report.id)).join(
        ReportAnalysis, Report.id == ReportAnalysis.report_id
    ).where(
        Report.processing_status == ProcessingStatus.failed,
        Report.uploaded_at >= time_window_start,
        ReportAnalysis.failure_category.isnot(None)
    ).group_by(ReportAnalysis.failure_category)
    
    failure_cat_rows = await db.execute(failure_category_stmt)
    failure_categories = {row[0]: row[1] for row in failure_cat_rows.all()}

    # Chart Data (Daily Success vs Failure)
    chart_stmt = select(
        cast(Report.uploaded_at, Date).label("day"),
        Report.processing_status,
        func.count(Report.id)
    ).where(
        Report.uploaded_at >= time_window_start,
        Report.processing_status.in_([ProcessingStatus.completed, ProcessingStatus.failed])
    ).group_by(
        cast(Report.uploaded_at, Date),
        Report.processing_status
    ).order_by(cast(Report.uploaded_at, Date))
    
    chart_rows = await db.execute(chart_stmt)
    day_map = {}
    for row in chart_rows.all():
        day_str = str(row[0])
        status = row[1].value if hasattr(row[1], 'value') else row[1]
        count = row[2]
        if day_str not in day_map:
            day_map[day_str] = {"date": day_str, "completed": 0, "failed": 0, "volume": 0}
        if "complete" in status:
            day_map[day_str]["completed"] += count
        elif "fail" in status:
            day_map[day_str]["failed"] += count
        day_map[day_str]["volume"] += count
    
    for day in day_map.values():
        total = day["completed"] + day["failed"]
        day["success_rate"] = (day["completed"] / total * 100) if total > 0 else 0.0

    chart_data = sorted(day_map.values(), key=lambda x: x["date"])

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
            "analysis_failure_count": reports_failed,
            "failure_categories": failure_categories
        },
        "chart_data": chart_data,
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
