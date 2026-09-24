import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.analysis_translation import AnalysisTranslation
from app.models.chat import ChatSession
from app.models.medication_schedule import MedicationSchedule
from app.models.rag_chunk import RagChunk
from app.models.report_analysis import ReportAnalysis
from app.models.user import User


@pytest.mark.asyncio
async def test_report_delete_and_cascade_cleanup(
    client: AsyncClient, token_headers: dict
):
    # 1. Create/upload a report
    upload_res = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        data={
            "title": "Deletion Test Report",
            "report_date": "2026-09-13",
            "report_type": "blood",
            "hospital": "Test Clinic",
        },
        files={
            "file": (
                "test_report.pdf",
                b"%PDF-1.4 test document content",
                "application/pdf",
            )
        },
    )
    assert upload_res.status_code == 201
    report_id = upload_res.json()["id"]

    # 2. Verify report exists
    get_res = await client.get(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert get_res.status_code == 200

    # 3. Delete report
    del_res = await client.delete(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert del_res.status_code == 204

    # 4. Verify report is 404
    get_after_del = await client.get(
        f"/api/v1/reports/{report_id}", headers=token_headers
    )
    assert get_after_del.status_code == 404

    # 5. Verify deleting again returns 404 cleanly
    del_again = await client.delete(
        f"/api/v1/reports/{report_id}", headers=token_headers
    )
    assert del_again.status_code == 404


@pytest.mark.asyncio
async def test_delete_processed_report_with_child_records(
    client: AsyncClient, token_headers: dict, db_session: AsyncSession
):
    stmt_user = select(User).where(User.email == "test_part3@example.com")
    user = (await db_session.execute(stmt_user)).scalars().first()

    # 1. Upload report
    upload_res = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        data={
            "title": "Processed Report to Delete",
            "report_date": "2026-09-15",
            "report_type": "blood",
            "hospital": "City Hospital",
        },
        files={
            "file": (
                "processed.pdf",
                b"%PDF-1.4 processed test content",
                "application/pdf",
            )
        },
    )
    assert upload_res.status_code == 201
    report_id = uuid.UUID(upload_res.json()["id"])

    # 2. Manually attach ReportAnalysis, AnalysisTranslation, RagChunk, MedicationSchedule, ChatSession
    analysis = ReportAnalysis(
        report_id=report_id,
        clinician_summary="Clinician Summary Test",
        patient_summary="Patient Summary Test",
        structured_lab_values=[
            {"test_name": "Hemoglobin", "value": 13.5, "unit": "g/dL"}
        ],
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)

    translation = AnalysisTranslation(
        report_analysis_id=analysis.id, language="hi", patient_summary="मरीज़ का सारांश"
    )
    db_session.add(translation)

    rag_chunk = RagChunk(
        report_id=report_id, chunk_index=0, chunk_text="Chunk text sample"
    )
    db_session.add(rag_chunk)

    med = MedicationSchedule(
        report_id=report_id, user_id=user.id, medication_name="Aspirin", dosage="75mg"
    )
    db_session.add(med)

    chat = ChatSession(user_id=user.id, report_id=report_id, title="Chat about report")
    db_session.add(chat)
    await db_session.commit()

    # 3. Call DELETE /api/v1/reports/{id}
    del_res = await client.delete(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert del_res.status_code == 204
