from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission, require_any_permission
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis

router = APIRouter()

@router.get("/llm")
async def get_llm_diagnostics(
    admin_ctx: AdminContext = Depends(require_permission("ai.telemetry.view")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    stmt = select(LLMDiagnosticEvent).order_by(desc(LLMDiagnosticEvent.timestamp)).offset(offset).limit(limit)
    events = (await db.execute(stmt)).scalars().all()
    
    # We do not expose raw prompts or responses here
    return {
        "status": "ok",
        "events": [
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
        ],
        "pagination": {
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/reports")
async def get_report_diagnostics(
    admin_ctx: AdminContext = Depends(require_permission("reports.diagnostics.view")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    stmt = (
        select(Report, ReportAnalysis)
        .outerjoin(ReportAnalysis, Report.id == ReportAnalysis.report_id)
        .order_by(desc(Report.uploaded_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    diagnostics = []
    for report, analysis in rows:
        diagnostics.append({
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

    return {
        "status": "ok",
        "reports": diagnostics,
        "pagination": {
            "limit": limit,
            "offset": offset
        }
    }

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
    
    # Infer stages safely
    stages = {
        "upload": True,
        "text_extraction": bool(report.extracted_text),
        "ner": bool(analysis and analysis.entities),
        "lab_extraction": bool(analysis and analysis.structured_lab_values),
        "rag": True, # Hard to infer purely from DB without inspecting chunks, assumed True if NLP ran
        "llm": bool(analysis and analysis.clinician_summary),
        "validation": bool(analysis and analysis.verification_status != "unverified"),
        "persistence": bool(analysis and analysis.processed_at)
    }

    return {
        "status": "ok",
        "report_id": report.id,
        "processing_status": report.processing_status,
        "analysis_status": "completed" if analysis and analysis.processed_at else ("failed" if analysis and analysis.error_reason else "pending"),
        "stages": stages,
        "failure_category": analysis.failure_category if analysis else None,
        "error_reason": analysis.error_reason if analysis else None,
        "llm_provider": analysis.llm_provider if analysis else None,
        "llm_model": analysis.llm_model if analysis else None,
        "processing_time": (analysis.processed_at - report.uploaded_at).total_seconds() if analysis and analysis.processed_at else None
    }
