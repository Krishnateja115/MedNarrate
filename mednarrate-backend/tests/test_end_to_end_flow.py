import pytest
from datetime import date
from sqlalchemy.future import select
from app.models.report import Report, ReportType, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.user import User

@pytest.mark.asyncio
async def test_end_to_end_analysis_persistence(db_session, monkeypatch):
    db = db_session
    from app.services.analysis_pipeline import run_analysis
    from app.core.config import settings
    
    # Mock LLM response for test double
    async def mock_generate(prompt, timeout=25):
        return "Patient summary: Hemoglobin is 14.2 g/dL which is normal."
    
    monkeypatch.setattr("app.services.analysis_pipeline.generate_with_timeout", mock_generate)

    # 1. Create User & Report
    user = User(email="e2e_user@example.com", hashed_password="pw", full_name="E2E User")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    sample_text = (
        "CLINICAL LABORATORY REPORT\n"
        "Specimen Date: 2026-09-10\n"
        "Hospital: Central Medical Lab\n"
        "Hemoglobin: 14.2 g/dL (Ref: 13.5 - 17.5)\n"
        "White Blood Cells: 6.5 x10^3/uL (Ref: 4.5 - 11.0)\n"
    )

    report = Report(
        user_id=user.id,
        title="End-to-End Test Report",
        hospital="Central Medical Lab",
        report_date=date(2026, 9, 10),
        file_name="e2e_test.pdf",
        file_path="dummy_path.pdf",
        file_type="pdf",
        report_type=ReportType.blood,
        extracted_text=sample_text,
        processing_status=ProcessingStatus.uploaded
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # 2. Run Pipeline
    await run_analysis(report.id, db)

    # 3. Verify Database Persistence
    stmt_rep = select(Report).where(Report.id == report.id)
    updated_report = (await db.execute(stmt_rep)).scalars().first()
    assert updated_report.processing_status == ProcessingStatus.completed

    stmt_an = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
    analysis = (await db.execute(stmt_an)).scalars().first()
    assert analysis is not None
    assert analysis.patient_summary is not None
    assert "Hemoglobin" in analysis.patient_summary or "disclaimer" in analysis.patient_summary.lower()
    assert len(analysis.structured_lab_values) >= 1
    assert any(v["test_name"].lower() == "hemoglobin" for v in analysis.structured_lab_values)
