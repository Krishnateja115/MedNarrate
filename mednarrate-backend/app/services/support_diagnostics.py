"""
Support Diagnostics Service.

Builds a privacy-safe diagnostic snapshot for a support ticket.
Correlates: user, ticket, report, report analysis, job executions, 
LLM telemetry, notifications, incidents.

Privacy guarantees:
- No extracted_text, clinician_summary, patient_summary, abnormal_findings
- No raw AI prompt/output content
- No API keys, tokens, credentials
- Missing values are represented as None/"not_captured", never invented
"""
from typing import Any, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.support import SupportTicket
from app.models.report import Report, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.job_execution import JobExecution
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.models.notification_log import NotificationLog
from app.models.incidents import Incident, IncidentStatus


# Deterministic action recommendations based on backend state
def _recommend_actions(
    report: Optional[Report],
    analysis: Optional[ReportAnalysis],
    recent_job: Optional[JobExecution],
    recent_notification: Optional[NotificationLog],
    can_manage_reports: bool,
    can_manage_support: bool
) -> list:
    """
    Generate recommended actions based purely on deterministic backend state.
    Never claims an action is safe merely because a button exists.
    """
    recommendations = []

    if report:
        status = report.processing_status
        
        if status == ProcessingStatus.failed:
            failure_cat = analysis.failure_category if analysis else None
            
            if failure_cat in ("llm_generation_failed", "llm_timeout", "llm_error"):
                recommendations.append({
                    "action": "retry_analysis",
                    "label": "Retry AI Analysis",
                    "reason": f"AI generation failed: {failure_cat}",
                    "safe": can_manage_reports,
                    "requires_permission": "reports.manage"
                })
            elif failure_cat in ("extraction_failed", "ocr_failed", "parse_error"):
                recommendations.append({
                    "action": "reprocess_report",
                    "label": "Reprocess Report (Full)",
                    "reason": f"Extraction failure: {failure_cat}. Full reprocess may resolve.",
                    "safe": can_manage_reports,
                    "requires_permission": "reports.manage"
                })
            else:
                # Generic failure — recommend retry
                recommendations.append({
                    "action": "retry_analysis",
                    "label": "Retry Report Processing",
                    "reason": "Report is in failed state",
                    "safe": can_manage_reports,
                    "requires_permission": "reports.manage"
                })
                
        elif status == ProcessingStatus.processing:
            # Check if it's been stuck
            stuck_threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=30)
            if report.updated_at and report.updated_at < stuck_threshold:
                recommendations.append({
                    "action": "retry_analysis",
                    "label": "Retry Stuck Report",
                    "reason": "Report has been in 'processing' state for over 30 minutes",
                    "safe": can_manage_reports,
                    "requires_permission": "reports.manage"
                })
        elif status == ProcessingStatus.completed:
            # Do NOT show retry as an action for completed reports
            recommendations.append({
                "action": "none_needed",
                "label": "Report Processed Successfully",
                "reason": "Report completed successfully. No retry needed.",
                "safe": True,
                "requires_permission": None
            })

    if recent_notification and recent_notification.status == "failed":
        recommendations.append({
            "action": "retry_notification",
            "label": "Retry Notification",
            "reason": "Last notification delivery failed",
            "safe": can_manage_support,
            "requires_permission": "support.manage"
        })

    if not recommendations:
        recommendations.append({
            "action": "investigate",
            "label": "Manual Investigation Required",
            "reason": "Could not determine a safe automatic action from current system state",
            "safe": True,
            "requires_permission": None
        })

    return recommendations


async def build_diagnostic_snapshot(
    ticket: SupportTicket,
    db: AsyncSession,
    admin_can_manage_reports: bool = False,
    admin_can_manage_support: bool = False
) -> Dict[str, Any]:
    """
    Build a complete, privacy-safe diagnostic snapshot for a support ticket.
    
    Returns operational metadata only. Never includes:
    - extracted_text or raw report content
    - clinician/patient summaries
    - raw AI prompts or outputs
    - credentials or tokens
    """
    snapshot: Dict[str, Any] = {
        "ticket_id": ticket.id,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "related_report": None,
        "analysis_status": None,
        "pipeline_stage": None,
        "failure_category": None,
        "failure_reason": None,
        "llm_telemetry": None,
        "recent_job": None,
        "recent_notification": None,
        "related_incident": None,
        "recommended_actions": []
    }

    report: Optional[Report] = None
    analysis: Optional[ReportAnalysis] = None
    recent_job: Optional[JobExecution] = None
    recent_notification: Optional[NotificationLog] = None

    # --- Related Report ---
    if ticket.related_report_id:
        import uuid
        report_res = await db.execute(
            select(Report).where(Report.id == uuid.UUID(ticket.related_report_id))
        )
        report = report_res.scalars().first()
        
        if report:
            snapshot["related_report"] = {
                "id": str(report.id),
                "title": report.title,
                "report_type": report.report_type.value,
                "processing_status": report.processing_status.value,
                "uploaded_at": report.uploaded_at.isoformat() if report.uploaded_at else None,
                "updated_at": report.updated_at.isoformat() if report.updated_at else None,
                # Sensitive content intentionally omitted
            }
            
            # --- Analysis ---
            analysis_res = await db.execute(
                select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
            )
            analysis = analysis_res.scalars().first()
            
            if analysis:
                snapshot["analysis_status"] = analysis.verification_status or "unverified"
                snapshot["failure_category"] = analysis.failure_category or "not_captured"
                snapshot["failure_reason"] = analysis.error_reason or "not_captured"
                snapshot["pipeline_stage"] = (
                    "completed" if report.processing_status == ProcessingStatus.completed
                    else report.processing_status.value
                )
                snapshot["llm_telemetry"] = {
                    "provider": analysis.llm_provider or "not_captured",
                    "model": analysis.llm_model or "not_captured",
                    "processed_at": analysis.processed_at.isoformat() if analysis.processed_at else "not_captured",
                }
            else:
                snapshot["analysis_status"] = "no_analysis_record"
                snapshot["pipeline_stage"] = report.processing_status.value
            
            # --- Recent LLM Diagnostic Event ---
            llm_event_res = await db.execute(
                select(LLMDiagnosticEvent)
                .where(LLMDiagnosticEvent.request_id == str(report.id))
                .order_by(desc(LLMDiagnosticEvent.timestamp))
                .limit(1)
            )
            llm_event = llm_event_res.scalars().first()
            if llm_event:
                snapshot["llm_telemetry"] = {
                    **(snapshot["llm_telemetry"] or {}),
                    "status": llm_event.status,
                    "latency_ms": llm_event.latency_ms,
                    "fallback_used": getattr(llm_event, "fallback_used", "not_captured"),
                    # Never include prompt or output content
                }
            
            # --- Recent Job ---
            job_res = await db.execute(
                select(JobExecution)
                .where(JobExecution.request_id == str(report.id))
                .order_by(desc(JobExecution.started_at))
                .limit(1)
            )
            recent_job = job_res.scalars().first()
            if recent_job:
                snapshot["recent_job"] = {
                    "id": str(recent_job.id),
                    "job_name": recent_job.job_name,
                    "status": recent_job.status.value,
                    "started_at": recent_job.started_at.isoformat() if recent_job.started_at else None,
                    "finished_at": recent_job.finished_at.isoformat() if recent_job.finished_at else None,
                    "duration_seconds": recent_job.duration_seconds,
                    "error_message": recent_job.error_details,
                }

    # --- Related Incident ---
    if ticket.related_incident_id:
        import uuid
        incident_res = await db.execute(
            select(Incident).where(Incident.id == uuid.UUID(ticket.related_incident_id))
        )
        incident = incident_res.scalars().first()
        if incident:
            snapshot["related_incident"] = {
                "id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity.value,
                "status": incident.status.value,
                "created_at": incident.created_at.isoformat() if incident.created_at else None,
            }

    # --- Recent Notification for Ticket User ---
    if ticket.user_id:
        import uuid
        notif_res = await db.execute(
            select(NotificationLog)
            .where(NotificationLog.user_id == uuid.UUID(ticket.user_id))
            .order_by(desc(NotificationLog.sent_at))
            .limit(1)
        )
        recent_notification = notif_res.scalars().first()
        if recent_notification:
            snapshot["recent_notification"] = {
                "id": str(recent_notification.id),
                "type": getattr(recent_notification, "notification_type", "not_captured"),
                "status": recent_notification.status,
                "sent_at": recent_notification.sent_at.isoformat() if recent_notification.sent_at else None,
                "error_message": getattr(recent_notification, "error_message", None),
            }

    # --- Recommended Actions (deterministic only) ---
    snapshot["recommended_actions"] = _recommend_actions(
        report=report,
        analysis=analysis,
        recent_job=recent_job,
        recent_notification=recent_notification,
        can_manage_reports=admin_can_manage_reports,
        can_manage_support=admin_can_manage_support
    )

    return snapshot
