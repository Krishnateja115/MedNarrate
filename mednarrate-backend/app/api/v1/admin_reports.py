"""
Admin Reports API.

Normal access (reports.view):
  GET /reports          — list with pagination, NO sensitive fields
  GET /reports/{id}     — metadata + analysis summary, NO raw text / medical content

Sensitive access (reports.sensitive_view + active break-glass grant):
  GET /reports/{id}/sensitive — full report including extracted_text, clinician_summary,
                                 patient_summary, abnormal_findings

Privileged mutations (reports.manage):
  POST /reports/{id}/actions/retry      — reset to uploaded for reprocessing
  POST /reports/{id}/actions/reprocess  — delete analysis and reset

All mutations are atomic: business mutation + audit event in one transaction.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import String, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission, validate_access_grant
from app.core.database import get_db
from app.models.report import ProcessingStatus, Report, ReportType
from app.models.report_analysis import ReportAnalysis
from app.models.user import User
from app.services.audit import log_admin_action

router = APIRouter()

import csv
import io
from datetime import datetime

from fastapi.responses import StreamingResponse


@router.get("/export")
async def export_reports_csv(
    domain: str = Query(..., description="The domain to export: support, users, or ai_failures"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("reports.view")),
    db: AsyncSession = Depends(get_db),
):
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Parse dates if provided
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            pass

    if domain == "support":
        from app.models.support import SupportTicket
        stmt = select(SupportTicket).order_by(desc(SupportTicket.created_at))
        if start_dt:
            stmt = stmt.where(SupportTicket.created_at >= start_dt)
        if end_dt:
            stmt = stmt.where(SupportTicket.created_at <= end_dt)
            
        tickets = (await db.execute(stmt)).scalars().all()
        writer.writerow(["Ticket ID", "Subject", "Status", "Priority", "User ID", "Created At"])
        for t in tickets:
            writer.writerow([str(t.id), t.subject, t.status.value if t.status else "", t.priority.value if t.priority else "", str(t.user_id), t.created_at.isoformat() if t.created_at else ""])
            
    elif domain == "users":
        stmt = select(User).order_by(desc(User.created_at))
        if start_dt:
            stmt = stmt.where(User.created_at >= start_dt)
        if end_dt:
            stmt = stmt.where(User.created_at <= end_dt)
            
        users = (await db.execute(stmt)).scalars().all()
        writer.writerow(["User ID", "Email", "Full Name", "Role", "Is Active", "Created At"])
        for u in users:
            writer.writerow([str(u.id), u.email, u.full_name, u.role.value if u.role else "", u.is_active, u.created_at.isoformat() if u.created_at else ""])
            
    elif domain == "ai_failures":
        from app.models.report_analysis import ReportAnalysis
        stmt = select(ReportAnalysis).where(ReportAnalysis.status == "failed").order_by(desc(ReportAnalysis.created_at))
        if start_dt:
            stmt = stmt.where(ReportAnalysis.created_at >= start_dt)
        if end_dt:
            stmt = stmt.where(ReportAnalysis.created_at <= end_dt)
            
        analyses = (await db.execute(stmt)).scalars().all()
        writer.writerow(["Analysis ID", "Report ID", "Error Message", "Error Reason", "Failure Category", "LLM Provider", "Created At"])
        for a in analyses:
            writer.writerow([str(a.id), str(a.report_id), a.error_message, a.error_reason, a.failure_category, a.llm_provider, a.created_at.isoformat() if a.created_at else ""])
    else:
        raise HTTPException(status_code=400, detail="Invalid export domain")

    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename=export_{domain}.csv"}
    )


@router.get("")
async def get_reports(
    admin_ctx: AdminContext = Depends(require_permission("reports.view")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    report_type: Optional[ReportType] = None,
    processing_status: Optional[ProcessingStatus] = None,
    user_id: Optional[uuid.UUID] = None,
):
    """List reports. Sensitive fields (extracted_text, findings) are never returned here."""
    stmt = select(Report, User.email).outerjoin(User, Report.user_id == User.id)

    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Report.title.ilike(search_term),
                Report.id.cast(String).ilike(search_term)
                if search.replace("-", "").isalnum()
                else False,
                User.email.ilike(search_term),
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
        reports.append(
            {
                "id": str(report.id),
                "user_id": str(report.user_id),
                "user_email": user_email,
                "title": report.title,
                "report_type": report.report_type.value,
                "processing_status": report.processing_status.value,
                "uploaded_at": report.uploaded_at.isoformat()
                if report.uploaded_at
                else None,
                "updated_at": report.updated_at.isoformat()
                if report.updated_at
                else None,
                # NOTE: extracted_text, clinician_summary, patient_summary intentionally omitted
            }
        )

    return {
        "status": "ok",
        "reports": reports,
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_next": (offset + limit) < total_count,
            "has_previous": offset > 0,
        },
    }


@router.get("/{report_id}")
async def get_report_detail(
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Report metadata + analysis summary. Sensitive fields are redacted.
    Use GET /reports/{id}/sensitive with an active break-glass grant for full content.
    """
    stmt = (
        select(Report, User.email)
        .outerjoin(User, Report.user_id == User.id)
        .where(Report.id == report_id)
    )
    result = (await db.execute(stmt)).first()

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    report, user_email = result

    # Fetch analysis (operational metadata only — no clinical content)
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
            "report_date": report.report_date.isoformat()
            if report.report_date
            else None,
            "file_name": report.file_name,
            "file_type": report.file_type.value,
            "report_type": report.report_type.value,
            "processing_status": report.processing_status.value,
            "uploaded_at": report.uploaded_at.isoformat()
            if report.uploaded_at
            else None,
            # Sensitive fields intentionally excluded — require break-glass
            "sensitive_content_available": bool(report.extracted_text),
        },
        "analysis": {
            "id": str(analysis.id) if analysis else None,
            "error_reason": analysis.error_reason if analysis else None,
            "failure_category": analysis.failure_category if analysis else None,
            "verification_status": analysis.verification_status
            if analysis
            else "unverified",
            "llm_provider": analysis.llm_provider if analysis else None,
            "llm_model": analysis.llm_model if analysis else None,
            "processed_at": analysis.processed_at.isoformat()
            if analysis and analysis.processed_at
            else None,
            # NOTE: clinician_summary, patient_summary, abnormal_findings excluded — require break-glass
        }
        if analysis
        else None,
    }


@router.get("/{report_id}/sensitive")
async def get_report_sensitive_content(
    report_id: uuid.UUID,
    request: Request,
    admin_ctx: AdminContext = Depends(require_permission("reports.sensitive_view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns sensitive report content: extracted_text, clinician_summary, patient_summary,
    abnormal_findings, lab values. Requires:
      1. reports.sensitive_view permission
      2. Active, unexpired, scope-matching break-glass grant

    Every access is audited with sensitive_access_flag=True.
    """
    # Enforce break-glass grant — validate_access_grant raises 403 if not met
    grant = await validate_access_grant(
        admin_ctx=admin_ctx,
        resource_type="medical_report",
        resource_id=str(report_id),
        db=db,
    )

    stmt = (
        select(Report, User.email)
        .outerjoin(User, Report.user_id == User.id)
        .where(Report.id == report_id)
    )
    result = (await db.execute(stmt)).first()

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")

    report, user_email = result

    analysis_stmt = select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
    analysis = (await db.execute(analysis_stmt)).scalars().first()

    # Audit sensitive access atomically with the read
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="SENSITIVE_REPORT_ACCESS",
        resource_type="medical_report",
        resource_id=str(report_id),
        permission_used="reports.sensitive_view",
        result="success",
        reason=f"Break-glass grant {grant.id}",
        request=request,
        # NEVER include extracted_text or clinical content in audit metadata
        metadata={"grant_id": str(grant.id), "report_title": report.title},
        sensitive_access_flag=True,
    )
    await db.commit()

    return {
        "status": "ok",
        "grant_id": str(grant.id),
        "grant_expires_at": grant.expires_at.isoformat(),
        "report": {
            "id": str(report.id),
            "user_id": str(report.user_id),
            "user_email": user_email,
            "title": report.title,
            "hospital": report.hospital,
            "report_date": report.report_date.isoformat()
            if report.report_date
            else None,
            "file_name": report.file_name,
            "file_type": report.file_type.value,
            "report_type": report.report_type.value,
            "processing_status": report.processing_status.value,
            "uploaded_at": report.uploaded_at.isoformat()
            if report.uploaded_at
            else None,
            # Sensitive fields — only returned with active break-glass grant
            "extracted_text": report.extracted_text,
        },
        "analysis": {
            "id": str(analysis.id) if analysis else None,
            "clinician_summary": analysis.clinician_summary if analysis else None,
            "patient_summary": analysis.patient_summary if analysis else None,
            "structured_lab_values": analysis.structured_lab_values if analysis else [],
            "abnormal_findings": analysis.abnormal_findings if analysis else [],
            "entities": analysis.entities if analysis else [],
            "error_reason": analysis.error_reason if analysis else None,
            "failure_category": analysis.failure_category if analysis else None,
            "llm_provider": analysis.llm_provider if analysis else None,
            "llm_model": analysis.llm_model if analysis else None,
        }
        if analysis
        else None,
    }


@router.post("/{report_id}/actions/retry")
async def retry_report(
    request: Request,
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset a failed/stuck report back to 'uploaded' for reprocessing.
    Business mutation and audit are in the same transaction.
    """
    report = (
        (await db.execute(select(Report).where(Report.id == report_id)))
        .scalars()
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.processing_status == ProcessingStatus.completed:
        raise HTTPException(status_code=400, detail="Cannot retry a completed report")

    previous_status = report.processing_status.value
    report.processing_status = ProcessingStatus.uploaded

    # Audit within same transaction as status change
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="REPORT_RETRY",
        resource_type="report",
        resource_id=str(report.id),
        permission_used="reports.manage",
        result="success",
        request=request,
        metadata={"previous_status": previous_status, "new_status": "uploaded"},
    )

    # Single commit: status change + audit
    await db.commit()

    return {
        "status": "ok",
        "message": "Report retry initiated",
        "new_status": "uploaded",
    }


@router.post("/{report_id}/actions/reprocess")
async def reprocess_report(
    request: Request,
    report_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("reports.manage")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete existing analysis and reset report to 'uploaded' for full reprocessing.
    Business mutations and audit are in the same transaction.
    """
    report = (
        (await db.execute(select(Report).where(Report.id == report_id)))
        .scalars()
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Delete existing analysis if it exists
    analysis = (
        (
            await db.execute(
                select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
            )
        )
        .scalars()
        .first()
    )
    had_analysis = bool(analysis)
    if analysis:
        await db.delete(analysis)

    report.processing_status = ProcessingStatus.uploaded

    # Audit within same transaction
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="REPORT_REPROCESS",
        resource_type="report",
        resource_id=str(report.id),
        permission_used="reports.manage",
        result="success",
        request=request,
        metadata={"analysis_deleted": had_analysis, "new_status": "uploaded"},
    )

    # Single commit: all mutations + audit
    await db.commit()

    return {
        "status": "ok",
        "message": "Report reprocessing initiated",
        "analysis_deleted": had_analysis,
    }
