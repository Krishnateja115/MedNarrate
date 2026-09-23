import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, String
from pydantic import BaseModel

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.report import Report, ReportType, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.admin import AdminAuditLog
from app.models.user import User

router = APIRouter()

async def log_admin_action(
    db: AsyncSession,
    admin_ctx: AdminContext,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata_payload: dict,
    request: Request
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    audit_log = AdminAuditLog(
        actor_admin_id=admin_ctx.user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_payload=metadata_payload,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    await db.commit()

@router.get("")
async def get_reports(
    admin_ctx: AdminContext = Depends(require_permission("reports.view")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    report_type: Optional[ReportType] = None,
    processing_status: Optional[ProcessingStatus] = None,
    user_id: Optional[uuid.UUID] = None
):
    stmt = select(Report, User.email).outerjoin(User, Report.user_id == User.id)
    
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Report.title.ilike(search_term),
                Report.id.cast(String).ilike(search_term) if search.replace('-', '').isalnum() else False,
                User.email.ilike(search_term)
            )
        )
        
    if report_type:
        stmt = stmt.where(Report.report_type == report_type)
        
    if processing_status:
        stmt = stmt.where(Report.processing_status == processing_status)
        
    if user_id:
        stmt = stmt.where(Report.user_id == user_id)
        
    # Count total matching records
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    # Paginate and fetch
    stmt = stmt.order_by(desc(Report.uploaded_at)).offset(offset).limit(limit)
    results = (await db.execute(stmt)).all()
    
    reports = []
    for report, user_email in results:
        reports.append({
            "id": str(report.id),
            "user_id": str(report.user_id),
            "user_email": user_email,
            "title": report.title,
            "report_type": report.report_type.value,
            "processing_status": report.processing_status.value,
            "uploaded_at": report.uploaded_at.isoformat() if report.uploaded_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None
        })
    
    return {
        "status": "ok",
        "reports": reports,
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/{report_id}")
async def get_report_detail(
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.view")),
    db: AsyncSession = Depends(get_db)
):
    # Fetch report and user
    stmt = select(Report, User.email).outerjoin(User, Report.user_id == User.id).where(Report.id == report_id)
    result = (await db.execute(stmt)).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report, user_email = result
    
    # Fetch analysis
    analysis_stmt = select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
    analysis = (await db.execute(analysis_stmt)).scalars().first()
    
    return {
        "status": "ok",
        "report": {
            "id": str(report.id),
            "user_id": str(report.user_id),
            "user_email": user_email,
            "title": report.title,
            "hospital": report.hospital,
            "report_date": report.report_date.isoformat() if report.report_date else None,
            "file_name": report.file_name,
            "file_type": report.file_type.value,
            "report_type": report.report_type.value,
            "processing_status": report.processing_status.value,
            "uploaded_at": report.uploaded_at.isoformat() if report.uploaded_at else None,
        },
        "analysis": {
            "id": str(analysis.id) if analysis else None,
            "error_reason": analysis.error_reason if analysis else None,
            "failure_category": analysis.failure_category if analysis else None,
            "verification_status": analysis.verification_status if analysis else "unverified",
            "llm_provider": analysis.llm_provider if analysis else None,
            "llm_model": analysis.llm_model if analysis else None,
            "processed_at": analysis.processed_at.isoformat() if analysis and analysis.processed_at else None
        } if analysis else None
    }

@router.post("/{report_id}/actions/retry")
async def retry_report(
    request: Request,
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db)
):
    report = (await db.execute(select(Report).where(Report.id == report_id))).scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.processing_status == ProcessingStatus.completed:
        raise HTTPException(status_code=400, detail="Cannot retry a completed report")
        
    report.processing_status = ProcessingStatus.uploaded
    
    # In a real system, we would trigger a Celery/background task here.
    # We leave the actual queuing to the existing processing systems.
    
    await log_admin_action(db, admin_ctx, "REPORT_RETRY", "report", str(report.id), {}, request)
    
    return {"status": "ok", "message": "Report retry initiated"}

@router.post("/{report_id}/actions/reprocess")
async def reprocess_report(
    request: Request,
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db)
):
    report = (await db.execute(select(Report).where(Report.id == report_id))).scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Delete existing analysis if it exists
    analysis = (await db.execute(select(ReportAnalysis).where(ReportAnalysis.report_id == report_id))).scalars().first()
    if analysis:
        await db.delete(analysis)
        
    report.processing_status = ProcessingStatus.uploaded
    
    # In a real system, we would trigger a background task here.
    
    await log_admin_action(db, admin_ctx, "REPORT_REPROCESS", "report", str(report.id), {}, request)
    
    return {"status": "ok", "message": "Report reprocessing initiated"}
