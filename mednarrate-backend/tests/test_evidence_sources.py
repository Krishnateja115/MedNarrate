from uuid import UUID

from sqlalchemy import select

from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.services.evidence_sources import build_lab_evidence_sources

from tests.pdf_fixtures import VALID_PDF


def test_lab_source_excerpt_requires_name_and_measured_value() -> None:
    text = "Hemoglobin 13.2 g/dL 12-16\nCreatinine 1.4 mg/dL 0.6-1.2"
    labs = [
        {"test_name": "Hemoglobin", "value": 13.2},
        {"test_name": "Creatinine", "value": 1.4},
    ]
    evidence = build_lab_evidence_sources(text, labs)
    assert evidence[0]["sources"] == ["Hemoglobin 13.2 g/dL 12-16"]
    assert evidence[1]["sources"] == ["Creatinine 1.4 mg/dL 0.6-1.2"]


def test_lab_source_excerpt_does_not_fabricate_missing_match() -> None:
    text = "Hemoglobin 13.2 g/dL 12-16\nCreatinine 0.8 mg/dL"
    labs = [{"test_name": "Creatinine", "value": 1.4}]
    assert build_lab_evidence_sources(text, labs) == []


async def test_old_analysis_gets_literal_source_excerpt_on_read(
    client, token_headers, db_session
) -> None:
    upload = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        files={"file": ("blood.pdf", VALID_PDF, "application/pdf")},
        data={"title": "Blood", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]
    report = (
        await db_session.execute(select(Report).where(Report.id == UUID(report_id)))
    ).scalar_one()
    report.extracted_text = "Hemoglobin 13.2 g/dL 12-16"
    db_session.add(
        ReportAnalysis(
            report_id=report.id,
            structured_lab_values=[
                {
                    "test_name": "Hemoglobin",
                    "original_name": "Hemoglobin",
                    "value": 13.2,
                    "unit": "g/dL",
                    "original_unit": "g/dL",
                    "flag": "normal",
                }
            ],
            evidence_sources=[],
        )
    )
    await db_session.commit()
    response = await client.get(
        f"/api/v1/reports/{report_id}/analysis", headers=token_headers
    )
    assert response.status_code == 200
    assert response.json()["evidence_sources"][0]["sources"] == [
        "Hemoglobin 13.2 g/dL 12-16"
    ]
