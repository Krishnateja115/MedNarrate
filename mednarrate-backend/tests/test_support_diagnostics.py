import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.services.support_diagnostics import build_diagnostic_snapshot
from app.models.support import SupportTicket, TicketCategory, TicketPriority, TicketStatus
from app.models.report import Report, ReportType, ProcessingStatus
from app.models.report_analysis import ReportAnalysis

@pytest.fixture
async def sample_ticket_with_report(db_session: AsyncSession):
    user_id = uuid.uuid4()
    report = Report(
        user_id=user_id,
        title="Diagnostic Report",
        report_type=ReportType.blood,
        report_date=datetime.now(timezone.utc),
        processing_status=ProcessingStatus.failed,
        extracted_text="Secret Clinical Data"
    )
    db_session.add(report)
    await db_session.commit()
    
    analysis = ReportAnalysis(
        report_id=report.id,
        failure_category="extraction_failed",
        error_reason="Could not extract text",
        clinician_summary="Secret Clinician Summary"
    )
    db_session.add(analysis)

    ticket = SupportTicket(
        user_id=user_id,
        title="Processing failed",
        description="Help, my report is stuck",
        category=TicketCategory.technical_issue,
        priority=TicketPriority.high,
        status=TicketStatus.open,
        related_report_id=report.id
    )
    db_session.add(ticket)
    await db_session.commit()
    return ticket

@pytest.mark.asyncio
async def test_diagnostic_snapshot_omits_sensitive_data(db_session: AsyncSession, sample_ticket_with_report: SupportTicket):
    """Ensure no clinical data leaks into the diagnostic snapshot"""
    snapshot = await build_diagnostic_snapshot(
        ticket=sample_ticket_with_report,
        db=db_session,
        admin_can_manage_reports=True,
        admin_can_manage_support=True
    )
    
    assert snapshot["ticket_id"] == sample_ticket_with_report.id
    assert snapshot["related_report"]["id"] == str(sample_ticket_with_report.related_report_id)
    assert snapshot["related_report"]["processing_status"] == "failed"
    
    # Sensitive fields MUST NOT exist in the snapshot
    assert "extracted_text" not in snapshot["related_report"]
    assert "clinician_summary" not in snapshot.get("analysis_status", {})
    assert "patient_summary" not in snapshot.get("analysis_status", {})

@pytest.mark.asyncio
async def test_diagnostic_snapshot_determines_actions(db_session: AsyncSession, sample_ticket_with_report: SupportTicket):
    """Ensure recommended actions are deterministically based on state"""
    snapshot = await build_diagnostic_snapshot(
        ticket=sample_ticket_with_report,
        db=db_session,
        admin_can_manage_reports=True,
        admin_can_manage_support=True
    )
    
    actions = snapshot["recommended_actions"]
    assert any(a["action"] == "reprocess_report" for a in actions)
    assert any(a["reason"] == "Extraction failure: extraction_failed. Full reprocess may resolve." for a in actions)
