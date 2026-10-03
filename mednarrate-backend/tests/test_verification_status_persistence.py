"""verification_status must be persisted by the pipeline and fail closed."""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.future import select

from app.models.feature_flag import FeatureFlag
from app.models.report import ProcessingStatus, Report
from app.models.report_analysis import ReportAnalysis
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _run(db, verifier_result, flag_enabled=True):
    from app.services.analysis_pipeline import run_analysis

    if flag_enabled:
        db.add(FeatureFlag(name="experimental_medical_verifier", enabled=True,
                           rollout_percentage=100, target_environment="all"))
    user = User(email=f"v{id(verifier_result)}@example.com", hashed_password="pw", full_name="U")
    db.add(user)
    await db.commit()
    report = Report(user_id=user.id, title="T", report_date=date(2024, 1, 1), file_name="t.pdf",
                    file_path="d/t.pdf", file_type="pdf", report_type="blood")
    db.add(report)
    await db.commit()
    rid = report.id

    ner = MagicMock()
    ner.return_value = [{"entity": "B-Test", "score": 0.99, "word": "Glucose"}]
    with patch("app.services.analysis_pipeline.get_ner_pipeline", return_value=ner), \
         patch("app.services.analysis_pipeline.extract_text_from_file", return_value="Glucose 120 mg/dL (70-99)"), \
         patch("app.services.analysis_pipeline.generate_with_timeout_metadata",
               return_value={"content": "Summary", "provider": "gemini", "model": "m"}), \
         patch("app.services.llm_orchestrator.verify_medical_facts", return_value=verifier_result) as v:
        await run_analysis(rid, db)
    analysis = (await db.execute(select(ReportAnalysis).where(ReportAnalysis.report_id == rid))).scalars().first()
    rep = (await db.execute(select(Report).where(Report.id == rid))).scalars().first()
    return analysis, rep, v


async def test_verified_is_persisted(db_session):
    a, rep, _ = await _run(db_session, {"is_valid": True, "correction": None, "verification_status": "verified"})
    assert rep.processing_status == ProcessingStatus.completed
    assert a.verification_status == "verified"


async def test_invalid_is_persisted_and_flagged(db_session):
    a, _, _ = await _run(db_session, {"is_valid": False, "correction": "[INVALID] bad", "verification_status": "invalid"})
    assert a.verification_status == "invalid"
    assert "flagged" in a.patient_summary.lower()
    assert "[WARNING from Medical Verifier]" in a.clinician_summary


@pytest.mark.parametrize("status", ["verifier_unavailable", "malformed_response"])
async def test_unavailable_or_malformed_is_not_verified(db_session, status):
    a, _, _ = await _run(db_session, {"is_valid": None, "correction": None, "verification_status": status})
    assert a.verification_status == status
    assert a.verification_status != "verified"


async def test_verifier_disabled_stays_unverified(db_session):
    a, _, v = await _run(db_session, {"is_valid": True, "correction": None, "verification_status": "verified"},
                         flag_enabled=False)
    assert not v.called
    assert a.verification_status == "unverified"
