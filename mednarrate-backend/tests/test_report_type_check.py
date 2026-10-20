"""MRAD dataset section and the experimental document-type check."""
import json
import os
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.ml import report_type_check as rtc
from app.ml.model_report import build_report, dataset_info
from app.models.feature_flag import FeatureFlag
from app.models.report import FileType, ProcessingStatus, Report, ReportType
from app.models.report_analysis import ReportAnalysis
from app.models.user import User

pytestmark = pytest.mark.asyncio

CBC_TEXT = (Path(__file__).parent / "fixtures" / "cbc_column_layout.txt").read_text()
LABS = [{"test_name": f"T{i}", "value": i} for i in range(4)]


# ----------------------------------------------------------- dataset section
def test_dataset_info_describes_mrad_without_leaking_a_local_path():
    info = dataset_info()
    assert info is not None
    assert info["name"].startswith("MRAD")
    assert info["classes"] == ["Blood", "Health", "TCGA"]
    assert info["records_usable"] > 100_000
    assert info["train_records"] + info["validation_records"] + info["test_records"] == info["records_usable"]
    assert sum(info["test_support_by_class"].values()) == info["test_records"]
    blob = json.dumps(info)
    assert "C:\\" not in blob and "Users" not in blob and ".csv" not in blob


def test_dataset_info_is_none_without_training_files(tmp_path):
    assert dataset_info(str(tmp_path / "no.json"), str(tmp_path / "no2.json")) is None
    report = build_report(path=str(tmp_path / "store.json"), classifier_path=str(tmp_path / "m.json"))
    assert report["dataset"] is None  # the page then just hides the section


async def test_user_endpoint_includes_the_dataset(client: AsyncClient, token_headers):
    body = (await client.get("/api/v1/ml/model-performance", headers=token_headers)).json()
    assert body["dataset"]["records_usable"] > 0
    assert "scope" in body["dataset"]


# ------------------------------------------------------------ the classifier
def test_a_real_blood_count_report_is_recognised():
    found = rtc.classify_report_text(CBC_TEXT)
    assert found is not None and found["label"] == "Blood"
    assert 0.55 <= found["confidence"] <= 1


def test_too_short_or_missing_text_gives_no_hint():
    assert rtc.classify_report_text(None) is None
    assert rtc.classify_report_text("  ") is None
    assert rtc.classify_report_text("Hb 12") is None


def test_classifier_failure_gives_no_hint_instead_of_raising(monkeypatch):
    def boom():
        raise FileNotFoundError("model files missing")

    monkeypatch.setattr(rtc, "_get_classifier", boom)
    assert rtc.classify_report_text(CBC_TEXT) is None


def test_unsure_predictions_are_hidden(monkeypatch):
    class Unsure:
        def predict(self, text):
            return {"predicted_category": "Blood", "confidence": 0.5,
                    "class_probabilities": {"Blood": 0.5, "Health": 0.0, "TCGA": 0.5}}

    monkeypatch.setattr(rtc, "_get_classifier", lambda: Unsure())
    assert rtc.classify_report_text(CBC_TEXT) is None

    class Close:
        def predict(self, text):
            return {"predicted_category": "Blood", "confidence": 0.6,
                    "class_probabilities": {"Blood": 0.6, "Health": 0.0, "TCGA": 0.55}}

    monkeypatch.setattr(rtc, "_get_classifier", lambda: Close())
    assert rtc.classify_report_text(CBC_TEXT) is None


# -------------------------------------------------------------- the endpoint
async def _report_for(db, email, *, labs=LABS, entities=None, status=ProcessingStatus.completed):
    user = (await db.execute(select(User).where(User.email == email))).scalars().first()
    report = Report(
        user_id=user.id, title="R", report_date=date(2024, 1, 1), file_name="r.pdf",
        file_path="r.pdf", file_type=FileType.pdf, report_type=ReportType.blood,
        processing_status=status,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    db.add(ReportAnalysis(report_id=report.id, structured_lab_values=labs, entities=entities or []))
    await db.commit()
    return report


async def _flag(db, enabled=True):
    db.add(FeatureFlag(name="report_type_check", enabled=enabled, rollout_percentage=100,
                       target_environment="all"))
    await db.commit()


async def test_endpoint_requires_login(client: AsyncClient):
    resp = await client.get("/api/v1/reports/00000000-0000-0000-0000-000000000000/document-type")
    assert resp.status_code == 401


async def test_flag_off_by_default_so_nothing_is_shown(client, token_headers, db_session):
    report = await _report_for(db_session, "test_part3@example.com")
    with patch("app.services.report_text_loader.extract_report_text", new=AsyncMock()) as extract:
        resp = await client.get(f"/api/v1/reports/{report.id}/document-type", headers=token_headers)
    assert resp.status_code == 200
    assert resp.json() == {"enabled": False, "available": False}
    extract.assert_not_called()  # the model is not even loaded while the flag is off


async def test_another_users_report_is_not_readable(client, token_headers, db_session, bystander_user):
    await _flag(db_session)
    other = Report(user_id=bystander_user.id, title="x", report_date=date(2024, 1, 1), file_name="x.pdf",
                   file_path="x.pdf", file_type=FileType.pdf, report_type=ReportType.blood,
                   processing_status=ProcessingStatus.completed)
    db_session.add(other)
    await db_session.commit()
    resp = await client.get(f"/api/v1/reports/{other.id}/document-type", headers=token_headers)
    assert resp.status_code in (403, 404)


async def test_flag_on_returns_the_hint_and_caches_it(client, token_headers, db_session):
    await _flag(db_session)
    report = await _report_for(db_session, "test_part3@example.com")
    extract = AsyncMock(return_value=CBC_TEXT)
    with patch("app.services.report_text_loader.extract_report_text", new=extract):
        first = (await client.get(f"/api/v1/reports/{report.id}/document-type", headers=token_headers)).json()
        second = (await client.get(f"/api/v1/reports/{report.id}/document-type", headers=token_headers)).json()
    assert first["enabled"] and first["available"] and first["experimental"]
    assert first["label"] == "Blood" and 0 < first["confidence"] <= 1
    assert second == first
    assert extract.await_count == 1  # the second visit used the stored answer


async def test_reports_that_do_not_look_medical_get_no_hint(client, token_headers, db_session):
    await _flag(db_session)
    report = await _report_for(db_session, "test_part3@example.com", labs=[], entities=[])
    with patch("app.services.report_text_loader.extract_report_text", new=AsyncMock(return_value="x" * 500)) as extract:
        body = (await client.get(f"/api/v1/reports/{report.id}/document-type", headers=token_headers)).json()
    assert body["enabled"] is True and body["available"] is False
    extract.assert_not_called()


async def test_unfinished_reports_get_no_hint(client, token_headers, db_session):
    await _flag(db_session)
    report = await _report_for(db_session, "test_part3@example.com", status=ProcessingStatus.processing)
    body = (await client.get(f"/api/v1/reports/{report.id}/document-type", headers=token_headers)).json()
    assert body["available"] is False


async def test_extraction_failure_is_not_an_error_and_is_retried_later(client, token_headers, db_session):
    await _flag(db_session)
    report = await _report_for(db_session, "test_part3@example.com")
    with patch("app.services.report_text_loader.extract_report_text",
               new=AsyncMock(side_effect=OSError("file gone"))):
        resp = await client.get(f"/api/v1/reports/{report.id}/document-type", headers=token_headers)
    assert resp.status_code == 200 and resp.json()["available"] is False
    analysis = (await db_session.execute(
        select(ReportAnalysis).where(ReportAnalysis.report_id == report.id))).scalars().first()
    assert "document_type_check" not in (analysis.model_versions or {})  # not cached


async def test_report_analysis_itself_is_untouched_by_the_check(client, token_headers, db_session):
    await _flag(db_session)
    report = await _report_for(db_session, "test_part3@example.com")
    report_id = report.id
    with patch("app.services.report_text_loader.extract_report_text", new=AsyncMock(return_value=CBC_TEXT)):
        await client.get(f"/api/v1/reports/{report_id}/document-type", headers=token_headers)
    db_session.expire_all()
    analysis = (await db_session.execute(
        select(ReportAnalysis).where(ReportAnalysis.report_id == report_id))).scalars().first()
    assert analysis.structured_lab_values == LABS
    refreshed = (await db_session.execute(select(Report).where(Report.id == report_id))).scalars().first()
    assert refreshed.processing_status == ProcessingStatus.completed
