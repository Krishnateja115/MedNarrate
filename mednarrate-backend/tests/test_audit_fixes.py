"""Regression tests for the pre-deployment audit fixes."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.future import select

from app.core.security import hash_password
from app.models.user import User


# ---------------------------------------------------------------- signup case
@pytest.mark.asyncio
async def test_signup_is_case_insensitive_and_stores_lowercase(client: AsyncClient):
    body = {"email": "Mixed.Case@Example.com", "password": "Passw0rd!x", "full_name": "Mixed Case"}
    r = await client.post("/api/v1/auth/signup", json=body)
    assert r.status_code == 201
    assert r.json()["email"] == "mixed.case@example.com"
    r2 = await client.post(
        "/api/v1/auth/signup", json={**body, "email": "MIXED.CASE@example.com"}
    )
    assert r2.status_code == 409


# ------------------------------------------------------------ unicode names
@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["రాము", "राम कुमार", "முருகன்", "Anne-Marie O'Neil", "Dr. K. Rao"])
async def test_signup_accepts_non_latin_names(client: AsyncClient, name):
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": f"u{abs(hash(name))}@example.com", "password": "Passw0rd!x", "full_name": name},
    )
    assert r.status_code == 201, r.text


def test_emergency_name_unicode_and_rejections():
    from app.schemas.user import validate_emergency_name_str

    assert validate_emergency_name_str("సీత") == "సీత"
    assert validate_emergency_name_str("राम") == "राम"
    for bad in ["", "12345", "!!!", "Bob<script>"]:
        with pytest.raises(ValueError):
            validate_emergency_name_str(bad)


def test_text_field_unicode_ok_symbols_rejected():
    from app.schemas.user import validate_text_field_str

    assert validate_text_field_str("పెన్సిలిన్") == "పెన్సిలిన్"
    with pytest.raises(ValueError):
        validate_text_field_str("!!!")


# ---------------------------------------------------- password reset delivery
@pytest.mark.asyncio
async def test_forgot_password_sends_email_with_token_only_by_email(
    client: AsyncClient, db_session, monkeypatch
):
    sent = []

    async def fake_send(to, raw_token, ttl_minutes=60):
        sent.append((to, raw_token))
        return True

    monkeypatch.setattr(
        "app.api.v1.password_reset.send_password_reset_email", fake_send
    )
    db_session.add(
        User(email="mail_me@example.com", hashed_password=hash_password("OldPassword123"), full_name="Mail Me")
    )
    await db_session.commit()

    r = await client.post("/api/v1/auth/forgot-password", json={"email": "MAIL_ME@example.com"})
    assert r.status_code == 200
    assert len(sent) == 1 and sent[0][0] == "mail_me@example.com"
    assert sent[0][1] not in r.text  # token never in the HTTP response

    # Unknown address: identical response, no mail.
    sent.clear()
    r2 = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r2.status_code == 200 and r2.json() == r.json() and not sent


@pytest.mark.asyncio
async def test_email_service_log_provider_and_failure_handling(monkeypatch):
    from app.core.config import settings
    from app.services import email_service

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "log")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    assert await email_service.send_email("a@b.co", "s", "t") is True

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert await email_service.send_email("a@b.co", "s", "t") is False

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "sendgrid")
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", None)
    assert await email_service.send_email("a@b.co", "s", "t") is False
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    assert await email_service.send_email("a@b.co", "s", "t") is False


@pytest.mark.asyncio
async def test_email_service_sendgrid_http(monkeypatch):
    import httpx

    from app.core.config import settings
    from app.services import email_service

    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "sendgrid")
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "SG.test")
    captured = {}

    def handler(request: httpx.Request):
        captured["auth"] = request.headers["authorization"]
        captured["body"] = request.content.decode()
        return httpx.Response(202)

    real = httpx.AsyncClient
    monkeypatch.setattr(
        email_service.httpx,
        "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )
    assert await email_service.send_password_reset_email("x@y.co", "TOKEN123") is True
    assert captured["auth"] == "Bearer SG.test" and "TOKEN123" in captured["body"]


# ------------------------------------------------------------- encryption
def test_encryption_key_rotation(monkeypatch):
    from cryptography.fernet import Fernet

    from app.core import encryption
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENCRYPTION_KEY", None)
    legacy = encryption.encrypt_value("secret-1")

    new_key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", new_key)
    # Old JWT-derived ciphertext is still readable; new writes use the new key.
    assert encryption.decrypt_value(legacy) == "secret-1"
    fresh = encryption.encrypt_value("secret-2")
    # Survives JWT_SECRET rotation because it no longer depends on it.
    monkeypatch.setattr(settings, "JWT_SECRET", "a-completely-different-jwt-secret-value")
    assert encryption.decrypt_value(fresh) == "secret-2"


# ---------------------------------------------------------------- privacy
def test_deidentify_redacts_identifiers_but_keeps_clinical_facts():
    from app.services.privacy import deidentify_prompt_text as d

    text = "\n".join(
        [
            "Name : Mr. Ravi Kumar   Age: 45 Y",
            "Test Name: Hemoglobin",
            "Hemoglobin 13.5 g/dL (13.0 - 17.0)",
            "Referred by Dr Anita Rao",
            "Mobile 9876543210 / +91 98765 43210",
            "Aadhaar 1234 5678 9012",
            "UHID: AB/12345",
            "Platelets 250000 /cumm (150000 - 450000)",
            "Metformin 500 mg twice daily",
        ]
    )
    out = d(text, mode="deidentified")
    for leaked in ["Ravi", "Anita", "9876543210", "98765 43210", "1234 5678 9012", "AB/12345"]:
        assert leaked not in out
    for kept in ["Age: 45 Y", "Test Name: Hemoglobin", "13.5 g/dL", "250000", "450000", "Metformin 500 mg"]:
        assert kept in out
    assert d(text, mode="full") == text


@pytest.mark.asyncio
async def test_lab_llm_prompt_is_deidentified(monkeypatch):
    from app.services import lab_value_extractor as lve

    seen = {}

    async def fake_llm(prompt, *a, **k):
        seen["prompt"] = prompt
        return "[]"

    monkeypatch.setattr("app.services.llm_orchestrator.extract_structured_json", fake_llm)
    # Text that the local parsers cannot read -> falls through to the LLM.
    await lve.extract_lab_values("Name: Mr. Secret Person\nMobile 9876543210\nsome narrative", "blood")
    await lve.extract_medication_schedule("Name: Mr. Secret Person\nMobile 9876543210\nTab Metformin 500mg")
    assert "Secret" not in seen["prompt"] and "9876543210" not in seen["prompt"]


# ------------------------------------------------------------------ CSV
def test_csv_safe_neutralises_formulas_but_keeps_numbers():
    from app.core.csv_safety import csv_safe

    assert csv_safe("=HYPERLINK(\"http://x\")") == "'=HYPERLINK(\"http://x\")"
    assert csv_safe("@SUM(A1)") == "'@SUM(A1)"
    assert csv_safe("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert csv_safe("-5") == "-5" and csv_safe("-0.3") == "-0.3"
    assert csv_safe("Hemoglobin") == "Hemoglobin" and csv_safe(None) is None


@pytest.mark.asyncio
async def test_admin_ai_failures_csv_export_works(client: AsyncClient, db_session, admin_token_and_user):
    from app.models.report import FileType, ProcessingStatus, Report, ReportType
    from app.models.report_analysis import ReportAnalysis

    headers, admin = admin_token_and_user
    report = Report(
        user_id=admin.id,
        title="csv report",
        report_date=date(2026, 1, 1),
        file_name="x.pdf",
        file_path="x.pdf",
        file_type=FileType.pdf,
        report_type=ReportType.blood,
        processing_status=ProcessingStatus.failed,
    )
    db_session.add(report)
    await db_session.commit()
    db_session.add(ReportAnalysis(report_id=report.id, error_reason="=cmd()", failure_category="EXTRACTION_ERROR"))
    await db_session.commit()

    r = await client.get("/api/v1/admin/reports/export?domain=ai_failures", headers=headers)
    assert r.status_code == 200, r.text
    assert "EXTRACTION_ERROR" in r.text and "'=cmd()" in r.text


# ------------------------------------------------------------ analysis pipeline
async def _make_report(db):
    from app.models.report import FileType, Report, ReportType

    user = User(email="pipe@example.com", hashed_password="pw", full_name="Pipe User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    report = Report(
        user_id=user.id, title="T", report_date=date(2024, 1, 1), file_name="t.pdf",
        file_path="dummy/t.pdf", file_type=FileType.pdf, report_type=ReportType.blood,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return user, report.id


@pytest.mark.asyncio
async def test_reanalysis_replaces_medications_instead_of_duplicating(db_session):
    from unittest.mock import AsyncMock, MagicMock, patch

    from sqlalchemy import func, select

    from app.models.medication_schedule import MedicationSchedule
    from app.services.analysis_pipeline import run_analysis
    from app.services.lab_value_extractor import MedicationScheduleModel

    _, report_id = await _make_report(db_session)
    med = MedicationScheduleModel(
        medication_name="Metformin", dosage="500 mg", frequency="twice daily",
        times_of_day=[], duration_days=None, notes=None,
    )
    with patch("app.services.analysis_pipeline.get_ner_pipeline", return_value=MagicMock(return_value=[])), \
         patch("app.services.llm_orchestrator.verify_medical_facts", new_callable=AsyncMock,
               return_value={"is_valid": True, "correction": None, "verification_status": "verified"}), \
         patch("app.services.analysis_pipeline.generate_with_timeout_metadata", new_callable=AsyncMock,
               return_value={"content": "summary", "provider": "gemini", "model": "m"}), \
         patch("app.services.analysis_pipeline.extract_report_text", new_callable=AsyncMock,
               return_value="Laboratory Report\nPatient: Test User\nGlucose 120 mg/dL (70-99)"), \
         patch("app.services.analysis_pipeline.extract_medication_schedule", new_callable=AsyncMock,
               return_value=[med]):
        await run_analysis(report_id, db_session)
        await run_analysis(report_id, db_session)

    count = (await db_session.execute(
        select(func.count()).select_from(MedicationSchedule).where(MedicationSchedule.report_id == report_id)
    )).scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_pipeline_unexpected_error_marks_failed_and_hides_internals(db_session):
    from unittest.mock import AsyncMock, patch

    from sqlalchemy import select

    from app.models.report import ProcessingStatus, Report
    from app.models.report_analysis import ReportAnalysis
    from app.services.analysis_pipeline import run_analysis

    _, report_id = await _make_report(db_session)
    with patch("app.services.analysis_pipeline.extract_report_text", new_callable=AsyncMock,
               side_effect=RuntimeError("connection to db-internal-host:5432 refused /srv/secret/path")):
        await run_analysis(report_id, db_session)

    report = (await db_session.execute(select(Report).where(Report.id == report_id))).scalars().first()
    analysis = (await db_session.execute(
        select(ReportAnalysis).where(ReportAnalysis.report_id == report_id))).scalars().first()
    assert report.processing_status == ProcessingStatus.failed
    assert analysis is not None and analysis.failure_category == "PIPELINE_ERROR"
    assert "db-internal-host" not in analysis.error_reason and "/srv/secret" not in analysis.error_reason


# ------------------------------------------------------ trend / compare hardening
async def _user_headers(client, email="trend@example.com"):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "StrongP@ssword1", "full_name": "Trend User"},
    )
    r = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "StrongP@ssword1"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _seed_reports(db, email, lab_sets):
    from app.models.report import FileType, ProcessingStatus, Report, ReportType
    from app.models.report_analysis import ReportAnalysis

    user = (await db.execute(select(User).where(User.email == email))).scalars().first()
    ids = []
    for i, labs in enumerate(lab_sets, start=1):
        rep = Report(
            user_id=user.id, title=f"R{i}", report_date=date(2024, i, 1), file_name="r.pdf",
            file_path="r.pdf", file_type=FileType.pdf, report_type=ReportType.blood,
            processing_status=ProcessingStatus.completed,
        )
        db.add(rep)
        await db.commit()
        await db.refresh(rep)
        db.add(ReportAnalysis(report_id=rep.id, structured_lab_values=labs))
        await db.commit()
        ids.append(str(rep.id))
    return ids


MESSY = [
    {"test_name": "Glucose", "value": 100, "unit": "mg/dL", "flag": "normal"},
    {"test_name": "HIV", "value": "Negative", "unit": None, "flag": None},
    {"test_name": None, "value": 5, "unit": "x"},
    {"test_name": "Creatinine", "value": None, "unit": "mg/dL"},
    "garbage-entry",
]
CLEAN = [{"test_name": "Glucose", "value": 130, "unit": "mg/dL", "flag": "high", "ref_low": 70, "ref_high": 99}]


@pytest.mark.asyncio
async def test_trend_survives_messy_stored_values(client, db_session):
    headers = await _user_headers(client)
    await _seed_reports(db_session, "trend@example.com", [MESSY, CLEAN])
    r = await client.get("/api/v1/reports/trend?test_name=glucose", headers=headers)
    assert r.status_code == 200, r.text
    assert [p["value"] for p in r.json()] == [100.0, 130.0]
    r = await client.get("/api/v1/reports/trend?test_name=HIV", headers=headers)
    assert r.status_code == 200 and r.json() == []


@pytest.mark.asyncio
async def test_compare_handles_messy_values_bad_ids_and_duplicates(client, db_session, monkeypatch):
    headers = await _user_headers(client)
    ids = await _seed_reports(db_session, "trend@example.com", [MESSY, CLEAN])

    async def boom(*a, **k):
        raise RuntimeError("llm down")

    monkeypatch.setattr("app.api.v1.reports.generate", boom)
    r = await client.get(f"/api/v1/reports/compare?report_ids={','.join(ids)}", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["comparisons"][0]["parameter"].lower().startswith("glucose")
    assert "unavailable" in body["ai_summary"].lower()

    bad = await client.get("/api/v1/reports/compare?report_ids=not-a-uuid,also-bad", headers=headers)
    assert bad.status_code == 400
    dup = await client.get(f"/api/v1/reports/compare?report_ids={ids[0]},{ids[0]}", headers=headers)
    assert dup.status_code == 400  # duplicates collapse to <2 distinct reports


@pytest.mark.asyncio
async def test_compare_previous_survives_messy_values_and_llm_failure(client, db_session, monkeypatch):
    headers = await _user_headers(client)
    ids = await _seed_reports(db_session, "trend@example.com", [MESSY, CLEAN])

    async def boom(*a, **k):
        raise RuntimeError("llm down")

    monkeypatch.setattr("app.api.v1.reports.generate", boom)
    r = await client.get(f"/api/v1/reports/{ids[1]}/compare-previous", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["comparable"] is True
    assert body["compared_findings"][0]["previous_value"] == 100
    assert "unavailable" in body["narrative_summary"].lower()


# ------------------------------------------------------------------ chat
def test_intent_classifier_uses_word_boundaries():
    from app.api.v1.chat import local_classify_intent as c

    assert c("I am studying for exams") == "general"
    assert c("my glucose is 112 mg/dL") == "general"
    assert c("what does keystroke mean") == "general"
    assert c("I have severe chest pain") == "emergency"
    assert c("he is unconscious") == "emergency"
    assert c("Do I have diabetes?") == "diagnosis"


@pytest.mark.asyncio
async def test_chat_llm_failure_returns_503_without_orphan_message(client, db_session, monkeypatch):
    headers = await _user_headers(client, "chat1@example.com")
    sid = (await client.post("/api/v1/chat/sessions", json={"title": "t"}, headers=headers)).json()["id"]

    async def boom(*a, **k):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr("app.api.v1.chat.generate", boom)
    r = await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "hello there"}, headers=headers)
    assert r.status_code == 503
    assert "exploded" not in r.text
    msgs = await client.get(f"/api/v1/chat/sessions/{sid}/messages", headers=headers)
    assert msgs.json() == []


@pytest.mark.asyncio
async def test_chat_messages_default_page_is_newest_and_chronological(client, db_session):
    from datetime import datetime, timedelta

    from app.models.chat import ChatMessage, ChatRole

    headers = await _user_headers(client, "chat2@example.com")
    sid = (await client.post("/api/v1/chat/sessions", json={"title": "t"}, headers=headers)).json()["id"]
    import uuid as _uuid

    base = datetime(2024, 1, 1)
    for i in range(30):
        db_session.add(ChatMessage(
            chat_session_id=_uuid.UUID(sid), role=ChatRole.user if i % 2 == 0 else ChatRole.assistant,
            content=f"m{i:02d}", created_at=base + timedelta(minutes=i),
        ))
    await db_session.commit()

    page1 = (await client.get(f"/api/v1/chat/sessions/{sid}/messages", headers=headers)).json()
    assert [m["content"] for m in page1] == [f"m{i:02d}" for i in range(10, 30)]
    page2 = (await client.get(f"/api/v1/chat/sessions/{sid}/messages?offset=20&limit=20", headers=headers)).json()
    assert [m["content"] for m in page2] == [f"m{i:02d}" for i in range(0, 10)]


# ------------------------------------------------------------ reminders / push
@pytest.mark.asyncio
async def test_reminder_validation_and_report_ownership(client, db_session):
    headers = await _user_headers(client, "rem@example.com")
    await _user_headers(client, "rem_other@example.com")
    (other_report,) = await _seed_reports(db_session, "rem_other@example.com", [CLEAN])

    ok = {"medication_name": "Metformin", "dosage": "500 mg", "frequency": "twice daily",
          "times_of_day": ["08:00 AM", "20:00"], "duration_days": 30}
    r = await client.post("/api/v1/reminders/", json=ok, headers=headers)
    assert r.status_code == 201, r.text

    for bad in (
        {**ok, "medication_name": "x" * 500},
        {**ok, "times_of_day": ["08:00"] * 30},
        {**ok, "times_of_day": ["y" * 100]},
        {**ok, "duration_days": -3},
        {**ok, "notes": "n" * 5000},
    ):
        assert (await client.post("/api/v1/reminders/", json=bad, headers=headers)).status_code == 422

    # Cannot attach someone else's report to a reminder.
    r = await client.post("/api/v1/reminders/", json={**ok, "report_id": other_report}, headers=headers)
    assert r.status_code == 403
    rid = (await client.post("/api/v1/reminders/", json=ok, headers=headers)).json()["id"]
    r = await client.patch(f"/api/v1/reminders/{rid}", json={"report_id": other_report}, headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_push_token_unregister_accepts_post_and_delete_and_moves_between_users(client, db_session):
    from app.models.push_token import PushToken

    a = await _user_headers(client, "pa@example.com")
    b = await _user_headers(client, "pb@example.com")
    tok = {"token": "device-token-123", "platform": "android"}
    assert (await client.post("/api/v1/notifications/register-token", json=tok, headers=a)).status_code == 200
    # Same physical device, different account: token moves to B only.
    assert (await client.post("/api/v1/notifications/register-token", json=tok, headers=b)).status_code == 200
    rows = (await db_session.execute(select(PushToken))).scalars().all()
    assert len(rows) == 1
    # The shipped app uses POST to unregister.
    r = await client.post("/api/v1/notifications/unregister-token", json={"token": "device-token-123"}, headers=b)
    assert r.status_code == 200 and r.json()["message"] == "Device unregistered"
    assert (await db_session.execute(select(PushToken))).scalars().all() == []
    # DELETE stays supported.
    await client.post("/api/v1/notifications/register-token", json=tok, headers=b)
    r = await client.request("DELETE", "/api/v1/notifications/unregister-token", json={"token": "device-token-123"}, headers=b)
    assert r.status_code == 200


# ------------------------------------------------------- medication clock times
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("08:00", "08:00"), ("8:00 AM", "08:00"), ("08:00 AM", "08:00"), ("8 pm", "20:00"),
        ("12:00 AM", "00:00"), ("12:30 PM", "12:30"), ("08.30 a.m.", "08:30"),
        ("20:00:00", "20:00"), ("9:05pm", "21:05"),
        ("after breakfast", None), ("3", None), ("25:00", None), ("13:00 PM", None), ("7:75", None),
    ],
)
def test_normalize_clock_time(raw, expected):
    from app.services.lab_value_extractor import normalize_clock_time

    assert normalize_clock_time(raw) == expected


def test_medication_model_normalises_times_and_drops_free_text():
    from app.services.lab_value_extractor import MedicationScheduleModel

    m = MedicationScheduleModel(
        medication_name="X", times_of_day=["08:00 AM", "8:00", "after dinner", "9 PM"]
    )
    assert m.times_of_day == ["08:00", "21:00"]


# ------------------------------------------------- admin retry in worker mode
@pytest.mark.asyncio
@pytest.mark.parametrize("mode,expected", [("background", "uploaded"), ("worker", "processing")])
async def test_admin_retry_requeues_so_the_worker_can_pick_it_up(
    client, db_session, admin_token_and_user, monkeypatch, mode, expected
):
    from app.core.config import settings
    from app.models.report import FileType, ProcessingStatus, Report, ReportType

    monkeypatch.setattr(settings, "ANALYSIS_EXECUTION_MODE", mode)
    headers, admin = admin_token_and_user
    rep = Report(
        user_id=admin.id, title="t", report_date=date(2024, 1, 1), file_name="a.pdf", file_path="a.pdf",
        file_type=FileType.pdf, report_type=ReportType.blood, processing_status=ProcessingStatus.failed,
    )
    db_session.add(rep)
    await db_session.commit()
    r = await client.post(f"/api/v1/admin/reports/{rep.id}/actions/retry", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["new_status"] == expected
    await db_session.refresh(rep)
    assert rep.processing_status.value == expected


# --- CBC with one-cell-per-line layout (name / result / range / unit) -------

def _cbc_fixture_text() -> str:
    import pathlib

    return (pathlib.Path(__file__).parent / "fixtures" / "cbc_column_layout.txt").read_text()


def test_column_layout_cbc_extracts_ranges_units_and_flags():
    import asyncio

    from app.services.lab_value_extractor import extract_lab_values

    rows = asyncio.run(extract_lab_values(_cbc_fixture_text(), "blood"))
    by_name = {r["test_name"]: r for r in rows}

    assert len(rows) >= 20
    hb = by_name["Hemoglobin"]
    assert (hb["value"], hb["ref_low"], hb["ref_high"], hb["flag"]) == (15.0, 13.0, 17.0, "normal")
    assert "g/dL" in hb["unit"]
    assert by_name["Total Leucocyte Count"]["ref_high"] == 10000.0
    # genuinely out-of-range values are flagged from the report's own ranges
    assert by_name["MCV"]["flag"] == "low"
    assert by_name["MCHC"]["flag"] == "high"
    # section headers must not become tests
    assert not any("Indices" in n or n == "Absolute Leucocyte Count" for n in by_name)
    # values with no printed range stay unclassified rather than guessed
    assert by_name["PCT"]["flag"] == "not_classified"


def test_single_line_row_layout_is_parsed():
    import asyncio

    from app.services.lab_value_extractor import extract_lab_values

    text = (
        "TEST DESCRIPTION RESULT REF. RANGE UNIT\n"
        "Haemoglobin 15 13 - 17 g/dL\n"
        "Total Leucocyte Count 12000 4000 - 10000 /cumm\n"
        "Platelet Count 300000 150000 - 410000 /cumm\n"
    )
    rows = {r["test_name"]: r for r in asyncio.run(extract_lab_values(text, "blood"))}
    assert rows["Hemoglobin"]["flag"] == "normal"
    assert rows["Total Leucocyte Count"]["flag"] == "high"
    assert rows["Platelets"]["unit"] == "/cumm"


def test_acronyms_keep_upper_case():
    from app.services.lab_value_normalizer import normalize_parameter_name

    assert normalize_parameter_name("MCV") == "MCV"
    assert normalize_parameter_name("Rdw-Cv") == "RDW-CV"
    assert normalize_parameter_name("Absolute Neutrophils") == "Absolute Neutrophils"


def test_fallback_summary_not_treated_as_pathology_by_signature_line():
    import asyncio
    import json

    from app.services.llm_client import FallbackAIProvider
    from app.services.prompts import CLINICIAN_PROMPT

    labs = [
        {"test_name": "MCV", "value": 80.0, "unit": "fL", "ref_low": 81.0, "ref_high": 101.0, "flag": "low"},
        {"test_name": "Hemoglobin", "value": 15.0, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "flag": "normal"},
    ]
    text = "Dr. Dummy\nMD Pathology\nHaemoglobin 15 13 - 17 g/dL"
    clinician = CLINICIAN_PROMPT.format(
        report_type="blood", structured_values_json=json.dumps(labs), extracted_text=text, rag_context=""
    )
    for prompt in (clinician,):
        out = asyncio.run(FallbackAIProvider().generate(prompt))["content"]
        assert "Pathology Examination Summary" not in out
        assert "INPUT_TEXT" not in out
        assert "MCV" in out and "LOW" in out


def test_grounding_accepts_counts_derived_from_structured_values():
    from app.services.validation import verify_summary_grounding

    labs = [{"test_name": "MCV", "value": 80.0, "flag": "low", "ref_low": 81.0, "ref_high": 101.0}] + [
        {"test_name": f"T{i}", "value": 1.0, "flag": "normal"} for i in range(21)
    ]
    ok = verify_summary_grounding(
        "Your report contains 22 extracted laboratory test result(s); 1 flagged, 21 normal. MCV 80.0 fL.",
        "MCV 80.00 81 - 101 fL",
        labs,
    )
    assert ok["is_valid"], ok
    bad = verify_summary_grounding("Your hemoglobin is 9.7.", "MCV 80.00 81 - 101 fL", labs)
    assert not bad["is_valid"]


# --- LLM provider chain / circuit breaker -----------------------------------

class _HttpErr(Exception):
    def __init__(self, status, detail=""):
        super().__init__(f"HTTP {status} {detail}")
        self.status_code = status
        self.error_detail = detail


def test_error_classification_distinguishes_quota_auth_model_and_outage():
    from app.services import provider_health as ph

    assert ph.classify_error(_HttpErr(429, "You exceeded your current quota"))[0] == ph.QUOTA
    assert ph.classify_error(_HttpErr(429, "per day limit"))[1] > ph.classify_error(_HttpErr(429, "slow down"))[1]
    assert ph.classify_error(_HttpErr(401))[0] == ph.AUTH
    assert ph.classify_error(_HttpErr(403))[0] == ph.AUTH
    assert ph.classify_error(_HttpErr(404, "model gpt-x does not exist"))[0] == ph.MODEL
    assert ph.classify_error(_HttpErr(503))[0] == ph.TRANSIENT
    assert ph.classify_error(TimeoutError("timed out"))[0] == ph.TRANSIENT
    from app.services.llm_client import LLMConfigurationError
    assert ph.classify_error(LLMConfigurationError("OPENAI_API_KEY is missing"))[0] == ph.NOT_CONFIGURED


def test_circuit_breaker_skips_failed_provider_then_recovers():
    from app.services.provider_health import ProviderHealth

    h = ProviderHealth()
    assert h.is_available("openai")
    h.record_failure("openai", _HttpErr(401))
    assert not h.is_available("openai")
    assert h.is_available("mistral")
    h.record_success("openai")
    assert h.is_available("openai")
    # dev_gemini and gemini are the same provider for health purposes
    h.record_failure("dev_gemini", _HttpErr(429))
    assert not h.is_available("gemini")


def test_http_error_detail_redacts_keys():
    from app.services.provider_health import http_error_detail

    class R:
        text = ""
        def json(self):
            return {"error": {"message": "Incorrect API key provided: sk-abcdefghijklmnop1234"}}

    out = http_error_detail(R())
    assert "sk-abcdefghijklmnop1234" not in out and "[redacted]" in out


def test_chain_uses_every_keyed_provider_and_skips_unusable_ones(monkeypatch):
    from app.core.config import settings
    from app.services.llm_client import LLMClient

    for k, v in {
        "ENVIRONMENT": "production", "OPENAI_API_KEY": "k1", "MISTRAL_API_KEY": "k2",
        "ANTHROPIC_API_KEY": None, "GEMINI_API_KEY": "AIzaSyFAKEKEYFAKEKEYFAKEKEYFAKEKEY12345",
        "VERTEX_PROJECT_ID": None, "LLM_PROVIDER_CHAIN": "",
    }.items():
        monkeypatch.setattr(settings, k, v, raising=False)
    chain = LLMClient()._build_chain("gemini", "ollama", True)
    # gemini is development-only (production), anthropic has no key, vertex has no project
    assert chain == ["gemini", "ollama", "openai", "mistral"]
    assert LLMClient()._build_chain("openai", "none", False) == ["openai"]


def test_chat_falls_through_providers_and_remembers_failures(monkeypatch):
    import asyncio

    from app.core.config import settings
    from app.services import llm_client as lc
    from app.services.provider_health import provider_health

    provider_health.reset()
    calls = []

    class Fake:
        def __init__(self, name, error=None):
            self.name, self.error = name, error
        async def generate(self, prompt, **kw):
            calls.append(self.name)
            if self.error:
                raise self.error
            return {"provider": self.name, "model": "m", "content": "hello", "latency_ms": 1}

    client = lc.LLMClient()
    client.providers.update({
        "openai": Fake("openai", _HttpErr(429, "You exceeded your current quota")),
        "mistral": Fake("mistral"),
        "ollama": Fake("ollama", lc.LLMConnectionError("connection refused")),
    })
    for k, v in {"ENVIRONMENT": "development", "OPENAI_API_KEY": "k1", "MISTRAL_API_KEY": "k2",
                 "ANTHROPIC_API_KEY": None, "GEMINI_API_KEY": None, "VERTEX_PROJECT_ID": None,
                 "LLM_PROVIDER_CHAIN": "", "ENABLE_LLM_FALLBACK": True}.items():
        monkeypatch.setattr(settings, k, v, raising=False)

    async def cfg():
        return {"primary_provider": "openai", "fallback_provider": "ollama", "enable_fallback": True,
                "model_name": "m", "api_key": None, "temperature": 0.2, "max_tokens": 64}
    monkeypatch.setattr(lc, "get_resolved_ai_config", cfg)

    first = asyncio.run(client.generate_with_metadata("hi"))
    assert first["provider"] == "mistral"
    assert calls == ["openai", "ollama", "mistral"]

    calls.clear()
    second = asyncio.run(client.generate_with_metadata("hi again"))
    assert second["provider"] == "mistral"
    # the exhausted/offline providers are not hammered again during their cool-down
    assert calls == ["mistral"]
    provider_health.reset()


def test_translation_does_not_retry_a_provider_whose_quota_is_gone():
    import asyncio

    from app.exceptions import TranslationServiceError
    from app.services.provider_health import provider_health
    from app.services.translation_planner import _execute_with_fallback

    provider_health.reset()
    calls = []

    async def gen(prompt, provider):
        calls.append(provider)
        if provider == "openai":
            e = TranslationServiceError("quota")
            e.status_code, e.failure_kind = 429, "quota_or_rate_limit"
            raise e
        return {"content": '{"clinician_summary": "x", "patient_summary": "y"}'}

    chunk = {"abnormal_findings": [], "medications": [], "clinician_summary": "a", "patient_summary": "b"}
    out = asyncio.run(_execute_with_fallback(
        "prompt", ["openai", "mistral"], lambda *a, **k: None, "hi", chunk, [], "rid", gen,
    ))
    assert out["clinician_summary"] == "x"
    assert calls == ["openai", "mistral"]  # exactly one call to the exhausted provider
    provider_health.reset()


@pytest.mark.asyncio
async def test_compare_matches_tests_when_one_report_has_no_units(client, db_session, monkeypatch):
    """A blank unit or a different spelling in one report must not stop the same test being compared."""
    headers = await _user_headers(client, "units@example.com")
    older = [
        {"test_name": "MCH", "value": 30.0, "unit": "", "flag": "normal"},
        {"test_name": "rbc_count", "value": 5.0, "unit": "", "flag": "normal"},
        {"test_name": "Neutrophils", "value": 50.0, "unit": "", "flag": "normal"},
        {"test_name": "Hemoglobin", "value": 15.0, "unit": "g/dL", "flag": "normal"},
    ]
    newer = [
        {"test_name": "MCH", "value": 27.2, "unit": "pg", "flag": "low", "ref_low": 27, "ref_high": 32},
        {"test_name": "Total RBC Count", "value": 5.2, "unit": "mill/cumm", "flag": "normal"},
        {"test_name": "Neutrophils", "value": 60.0, "unit": "%", "flag": "normal"},
        {"test_name": "Hemoglobin", "value": 150.0, "unit": "g/L", "flag": "normal"},
    ]
    ids = await _seed_reports(db_session, "units@example.com", [older, newer])

    async def fake_generate(*a, **k):
        return "summary"

    monkeypatch.setattr("app.api.v1.reports.generate", fake_generate)
    r = await client.get(f"/api/v1/reports/compare?report_ids={','.join(ids)}", headers=headers)
    assert r.status_code == 200, r.text
    by = {c["parameter"]: c for c in r.json()["comparisons"]}
    assert {"MCH", "RBC", "Neutrophils"} <= set(by)
    assert by["MCH"]["unit"] == "pg"
    assert by["MCH"]["reference_range"] == "27-32"
    assert [v["value"] for v in by["MCH"]["values"]] == [30.0, 27.2]
    # g/dL and g/L are different scales and must not be trended together.
    assert "Hemoglobin" not in by
