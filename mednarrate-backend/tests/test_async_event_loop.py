import asyncio
import threading
from datetime import date
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.main import app
from app.models.report import FileType, ProcessingStatus, Report, ReportType
from app.models.user import User
from app.services.analysis_pipeline import run_analysis


@pytest.mark.asyncio
async def test_status_endpoint_responsive_during_background_processing(
    client: AsyncClient,
    token_headers: dict,
    db_session: AsyncSession,
    db_session_factory,
):
    """Status requests complete while synchronous extraction is held open."""
    stmt = select(User).where(User.email == "test_part3@example.com")
    res = await db_session.execute(stmt)
    user = res.scalars().first()

    report = Report(
        user_id=user.id,
        title="Test Lab Report",
        file_name="test_event_loop_report.pdf",
        report_date=date.today(),
        file_path="uploads/test_event_loop_report.pdf",
        report_type=ReportType.blood,
        file_type=FileType.pdf,
        extracted_text=None,
        processing_status=ProcessingStatus.uploaded,
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)

    report_id = str(report.id)
    extraction_started = threading.Event()
    release_extraction = threading.Event()

    def blocking_heavy_work(*args, **kwargs):
        extraction_started.set()
        if not release_extraction.wait(timeout=2.0):
            raise RuntimeError("test extraction was not released")
        raise RuntimeError("stop pipeline after concurrency assertion")

    async def get_independent_db():
        async with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = get_independent_db

    with patch(
        "app.services.analysis_pipeline.extract_text_from_file",
        side_effect=blocking_heavy_work,
    ):
        async with db_session_factory() as analysis_db:
            analysis_task = asyncio.create_task(run_analysis(report.id, analysis_db))
            started = await asyncio.to_thread(extraction_started.wait, 1.0)
            assert started, "background extraction did not start"

            async def fetch_status():
                return await client.get(
                    f"/api/v1/reports/{report_id}/status", headers=token_headers
                )

            try:
                results = await asyncio.wait_for(
                    asyncio.gather(fetch_status(), fetch_status(), fetch_status()),
                    timeout=1.0,
                )
            finally:
                release_extraction.set()
                await analysis_task

    for resp in results:
        assert resp.status_code == 200
        assert resp.json()["processing_status"] == "processing"
