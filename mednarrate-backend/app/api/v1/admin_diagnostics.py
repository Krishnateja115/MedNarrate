from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import uuid

from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission, require_any_permission
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.job_execution import JobExecution
from app.models.push_token import PushToken
from app.services.llm_client import llm_client_instance
import os
from app.core.config import settings

router = APIRouter()

@router.get("/llm")
async def get_llm_diagnostics(
    sort_by: str = Query("timestamp"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("ai.telemetry.view")),
    db: AsyncSession = Depends(get_db)
):
    limit = clamp_limit(limit)
    stmt = select(LLMDiagnosticEvent)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    sort_col = getattr(LLMDiagnosticEvent, sort_by, LLMDiagnosticEvent.timestamp)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)
        
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    events = (await db.execute(stmt)).scalars().all()
    
    # We do not expose raw prompts or responses here
    items = [
        {
            "id": evt.id,
            "request_id": evt.request_id,
            "provider": evt.provider,
            "model_name": evt.model_name,
            "feature": evt.feature,
            "status": evt.status,
            "latency_ms": evt.latency_ms,
            "error_category": evt.error_category,
            "fallback_used": evt.fallback_used,
            "timestamp": evt.timestamp.isoformat()
        } for evt in events
    ]
    
    return build_pagination_response(items, total, page, limit)

@router.get("/reports")
async def get_report_diagnostics(
    sort_by: str = Query("uploaded_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("reports.diagnostics.view")),
    db: AsyncSession = Depends(get_db)
):
    limit = clamp_limit(limit)
    stmt = (
        select(Report, ReportAnalysis)
        .outerjoin(ReportAnalysis, Report.id == ReportAnalysis.report_id)
    )
    
    # Count (count reports)
    count_stmt = select(func.count(Report.id))
    total = (await db.execute(count_stmt)).scalar() or 0

    sort_col = getattr(Report, sort_by, Report.uploaded_at)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)
        
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()
    
    items = []
    for report, analysis in rows:
        items.append({
            "report_id": report.id,
            "processing_status": report.processing_status,
            "file_type": report.file_type,
            "report_type": report.report_type,
            "uploaded_at": report.uploaded_at.isoformat(),
            "analysis_status": "completed" if analysis and analysis.processed_at else ("failed" if analysis and analysis.error_reason else "pending"),
            "failure_category": analysis.failure_category if analysis else None,
            "error_reason": analysis.error_reason if analysis else None,
            "llm_provider": analysis.llm_provider if analysis else None,
            "llm_model": analysis.llm_model if analysis else None,
            "verification_status": analysis.verification_status if analysis else "unverified",
            "processing_time": (analysis.processed_at - report.uploaded_at).total_seconds() if analysis and analysis.processed_at else None
        })

    return build_pagination_response(items, total, page, limit)

@router.get("/reports/{report_id}")
async def get_report_diagnostic_snapshot(
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.diagnostics.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Report).where(Report.id == report_id)
    report = (await db.execute(stmt)).scalars().first()
    
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        
    stmt_an = select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
    analysis = (await db.execute(stmt_an)).scalars().first()
    
    # Deterministic job correlation
    stmt_job = select(JobExecution).where(JobExecution.request_id == str(report_id)).order_by(desc(JobExecution.started_at))
    jobs = (await db.execute(stmt_job)).scalars().all()
    
    job_state = "none"
    if jobs:
        job_state = jobs[0].status.value

    # Build deterministic snapshot
    snapshot = {
        "upload": True,
        "job_state": job_state,
        "jobs_count": len(jobs),
        "text_extraction": bool(report.extracted_text),
        "ner": bool(analysis and analysis.entities),
        "lab_extraction": bool(analysis and analysis.structured_lab_values),
        "llm_summary": bool(analysis and analysis.clinician_summary),
        "persistence": bool(analysis and analysis.processed_at),
        "user_id": str(report.user_id) if hasattr(report, 'user_id') else None
    }

    return {
        "status": "ok",
        "report_id": report.id,
        "processing_status": report.processing_status,
        "analysis_status": "completed" if analysis and analysis.processed_at else ("failed" if analysis and analysis.error_reason else "pending"),
        "stages": snapshot,
        "failure_category": analysis.failure_category if analysis else None,
        "error_reason": analysis.error_reason if analysis else None,
        "llm_provider": analysis.llm_provider if analysis else None,
        "llm_model": analysis.llm_model if analysis else None,
        "processing_time": (analysis.processed_at - report.uploaded_at).total_seconds() if analysis and analysis.processed_at else None
    }

@router.get("/system/snapshot")
async def get_system_snapshot(
    admin_ctx: AdminContext = Depends(require_permission("system.health.view")),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a deterministic real diagnostic snapshot of the system state.
    """
    # Recent jobs (last 20)
    jobs_stmt = select(JobExecution).order_by(desc(JobExecution.started_at)).limit(20)
    recent_jobs = (await db.execute(jobs_stmt)).scalars().all()
    
    jobs_data = [{
        "id": j.id,
        "job_name": j.job_name,
        "status": j.status.value,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "duration_seconds": j.duration_seconds
    } for j in recent_jobs]

    # Active push tokens count
    tokens_stmt = select(func.count(PushToken.id))
    active_tokens = (await db.execute(tokens_stmt)).scalar() or 0
    
    # LLM Provider State
    provider_name = (settings.PRIMARY_LLM_PROVIDER or "auto").lower().strip()
    try:
        provider = llm_client_instance.get_provider(provider_name)
        provider_health = await provider.health_check()
        llm_state = {
            "provider": provider_name,
            "configured": provider_health.get("configured", False),
            "reachable": provider_health.get("reachable", False),
            "request_successful": provider_health.get("request_successful", False)
        }
    except Exception as e:
        llm_state = {"error": str(e)}

    # Storage Stats (simple implementation checking upload dir)
    storage_stats = {"upload_dir_exists": False, "total_files": 0, "size_bytes": 0}
    try:
        if os.path.exists(settings.UPLOAD_DIR):
            storage_stats["upload_dir_exists"] = True
            for root, dirs, files in os.walk(settings.UPLOAD_DIR):
                storage_stats["total_files"] += len(files)
                storage_stats["size_bytes"] += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    except Exception:
        pass

    return {
        "status": "ok",
        "snapshot": {
            "recent_jobs": jobs_data,
            "llm_provider_state": llm_state,
            "active_tokens": active_tokens,
            "storage_stats": storage_stats
        }
    }
