import pytest
import asyncio
import time
from datetime import date
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.report import Report, ReportType, FileType, ProcessingStatus

@pytest.mark.asyncio
async def test_status_endpoint_responsive_during_background_processing(
    client: AsyncClient,
    token_headers: dict,
    db_session: AsyncSession
):
    """
    Verifies that GET /api/v1/reports/{id}/status remains responsive (< 200ms)
    while background report analysis is actively running on a worker thread.
    """
    # 1. Fetch created user from token setup
    stmt = select(User).where(User.email == "test_part3@example.com")
    res = await db_session.execute(stmt)
    user = res.scalars().first()

    # 2. Create a valid test report in DB with all required fields
    report = Report(
        user_id=user.id,
        title="Test Lab Report",
        file_name="test_event_loop_report.pdf",
        report_date=date.today(),
        file_path="uploads/test_event_loop_report.pdf",
        report_type=ReportType.blood,
        file_type=FileType.pdf,
        extracted_text="Patient Test Result: Hemoglobin 14.2 g/dL",
        processing_status=ProcessingStatus.uploaded
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)

    report_id = str(report.id)

    # 3. Mock extract_text_from_file to introduce a 0.5s synchronous blocking delay.
    # Because extract_text_from_file is executed via asyncio.to_thread,
    # the 0.5s sleep occurs on an OS thread pool, leaving the asyncio event loop free.
    def blocking_heavy_work(*args, **kwargs):
        time.sleep(0.5)
        return "Patient Test Result: Hemoglobin 14.2 g/dL"

    with patch("app.services.analysis_pipeline.extract_text_from_file", side_effect=blocking_heavy_work):
        # 4. Trigger processing
        process_resp = await client.post(
            f"/api/v1/reports/{report_id}/process",
            headers=token_headers
        )
        assert process_resp.status_code == 202
        assert process_resp.json()["processing_status"] == "processing"

        # 5. Concurrently send multiple status GET requests while processing is underway
        async def fetch_status():
            start = time.perf_counter()
            resp = await client.get(
                f"/api/v1/reports/{report_id}/status",
                headers=token_headers
            )
            elapsed = time.perf_counter() - start
            return resp, elapsed

        # Send 3 concurrent status requests
        results = await asyncio.gather(
            fetch_status(),
            fetch_status(),
            fetch_status()
        )

        # 6. Verify all status requests responded promptly and returned valid status
        for resp, elapsed in results:
            assert resp.status_code == 200
            assert resp.json()["processing_status"] in ["processing", "completed"]
            # Assert each status request responded in under 200ms (0.2s)
            assert elapsed < 0.200, f"Status endpoint blocked: took {elapsed:.4f}s (expected < 0.200s)"

    # Allow background task to clean up
    await asyncio.sleep(0.6)
