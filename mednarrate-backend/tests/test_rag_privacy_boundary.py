"""RAG must de-identify before any embedding call, independent of LLM_SEND_MODE."""
import uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.rag_chunk import RagChunk
from app.models.report import Report
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.services import rag


PII_TEXT = (
    "Patient Name: Jane Roe\nMRN: 99887766\nDOB: 01/02/1980\nPhone: 555-123-4567\n"
    "Email: jane.roe@example.com\nHemoglobin: 9.1 g/dL (12.0-15.5)\n"
)


async def _make_report(db, email="rag@example.com"):
    u = User(email=email, hashed_password=hash_password("StrongP@ssword1"),
             full_name="Jane Roe", role=UserRole.patient)
    db.add(u)
    await db.commit()
    r = Report(user_id=u.id, file_path=f"{u.id}/r.pdf", title="t", hospital="h",
               report_date=date(2023, 1, 1), file_name="r.pdf", file_type="pdf",
               report_type="blood", processing_status="completed")
    db.add(r)
    await db.commit()
    return u, r


@pytest.fixture
def spy_embedder(monkeypatch):
    seen = []

    def embed(text, task_type="retrieval_document"):
        seen.append(text)
        return [0.1] * 768

    monkeypatch.setattr(rag, "get_embedder", lambda: embed)
    return seen


@pytest.mark.parametrize("send_mode", ["deidentified", "full"])
@pytest.mark.asyncio
async def test_ingest_deidentifies_even_when_llm_send_mode_full(db_session, spy_embedder, monkeypatch, send_mode):
    monkeypatch.setattr(settings, "LLM_SEND_MODE", send_mode, raising=False)
    _, report = await _make_report(db_session)
    await rag.process_report_for_rag(report.id, PII_TEXT, db_session)

    assert spy_embedder, "embedder should have been called"
    blob = "\n".join(spy_embedder)
    for secret in ("Jane Roe", "99887766", "555-123-4567", "jane.roe@example.com", "01/02/1980"):
        assert secret not in blob
    assert "9.1" in blob  # clinical facts preserved

    rows = (await db_session.execute(select(RagChunk).where(RagChunk.report_id == report.id))).scalars().all()
    stored = "\n".join(c.chunk_text for c in rows)
    assert "Jane Roe" not in stored and "99887766" not in stored


@pytest.mark.asyncio
async def test_query_is_deidentified_before_embedding(db_session, spy_embedder, monkeypatch):
    monkeypatch.setattr(settings, "LLM_SEND_MODE", "full", raising=False)
    _, report = await _make_report(db_session, "rag2@example.com")
    await rag.process_report_for_rag(report.id, PII_TEXT, db_session)
    spy_embedder.clear()
    await rag.retrieve_chunks("Patient Name: Jane Roe hemoglobin?", report.id, db_session)
    assert spy_embedder and all("Jane Roe" not in t for t in spy_embedder)


@pytest.mark.asyncio
async def test_cross_report_retrieval_is_scoped(db_session, monkeypatch):
    monkeypatch.setattr(rag, "get_embedder", lambda: None)
    _, r1 = await _make_report(db_session, "u1@example.com")
    _, r2 = await _make_report(db_session, "u2@example.com")
    await rag.process_report_for_rag(r1.id, "Hemoglobin: 9.1 g/dL\nAlpha marker", db_session)
    await rag.process_report_for_rag(r2.id, "Glucose: 200 mg/dL\nBeta marker", db_session)
    out = await rag.retrieve_chunks("glucose beta", r1.id, db_session)
    assert "Glucose" not in out and "Beta" not in out


@pytest.mark.asyncio
async def test_embedder_failure_falls_back_without_raising(db_session, monkeypatch):
    def boom(text, task_type="retrieval_document"):
        raise RuntimeError("provider down")

    monkeypatch.setattr(rag, "get_embedder", lambda: boom)
    _, report = await _make_report(db_session, "u3@example.com")
    await rag.process_report_for_rag(report.id, PII_TEXT, db_session)
    out = await rag.retrieve_chunks("hemoglobin", report.id, db_session)
    assert "Hemoglobin" in out


def test_provider_abstraction(monkeypatch):
    from app.services import embedding_provider as ep

    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "unknown-provider", raising=False)
    assert ep.get_embedder() is None
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "gemini", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None, raising=False)
    assert ep.get_embedder() is None


@pytest.mark.asyncio
async def test_user_anonymization_removes_rag_chunks(db_session, monkeypatch):
    from app.services.user_deletion import anonymize_and_delete_user_data

    monkeypatch.setattr(rag, "get_embedder", lambda: None)
    user, report = await _make_report(db_session, "u4@example.com")
    await rag.process_report_for_rag(report.id, PII_TEXT, db_session)
    assert (await db_session.execute(select(RagChunk))).scalars().all()
    await anonymize_and_delete_user_data(user, db_session)
    await db_session.commit()
    assert (await db_session.execute(select(RagChunk))).scalars().all() == []
