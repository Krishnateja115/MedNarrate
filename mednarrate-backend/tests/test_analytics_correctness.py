import uuid
from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.api.v1.admin_analytics import _average_duration_seconds
from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.user import User, UserRole
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.models.report import FileType, ProcessingStatus, Report, ReportType
from app.models.report_analysis import ReportAnalysis


@pytest.fixture
async def analytics_admin(db_session: AsyncSession):
    user = User(
        email=f"analytics_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Analytics Admin",
        role=UserRole.admin,
    )
    db_session.add(user)

    role = AdminRole(name=f"Analytics Admin_{uuid.uuid4()}")
    db_session.add(role)

    stmt = select(AdminPermission).where(AdminPermission.name == "analytics.view")
    perm = (await db_session.execute(stmt)).scalars().first()
    if not perm:
        perm = AdminPermission(name="analytics.view")
        db_session.add(perm)

    await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_analytics_avoids_fabricated_data(
    client: AsyncClient, analytics_admin: User, db_session: AsyncSession
):
    """Ensure the analytics endpoint returns real data and handles division by zero safely."""
    uploaded_at = datetime.utcnow() - timedelta(minutes=2)
    report = Report(
        user_id=analytics_admin.id,
        title="Analytics regression report",
        report_date=date.today(),
        file_name="analytics.pdf",
        file_path="/tmp/analytics.pdf",
        file_type=FileType.pdf,
        report_type=ReportType.other,
        processing_status=ProcessingStatus.completed,
        uploaded_at=uploaded_at,
    )
    db_session.add(report)
    await db_session.flush()
    db_session.add(
        ReportAnalysis(
            report_id=report.id,
            processed_at=uploaded_at + timedelta(seconds=120),
        )
    )
    unique_error = f"test_timeout_{uuid.uuid4().hex[:8]}"
    db_session.add(
        LLMDiagnosticEvent(
            provider="test-provider",
            model_name="test-model",
            status="error",
            error_category=unique_error,
            latency_ms=250.0,
        )
    )
    await db_session.commit()

    token = create_access_token(subject=str(analytics_admin.id))

    resp = await client.get(
        "/api/v1/admin/analytics?timeframe=7d",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "ok"
    assert data["reports"]["avg_processing_time_sec"] is not None
    assert data["ai"]["failure_categories"].get(unique_error) == 1

    # Verify we aren't getting the hardcoded 85.0% or 4.2s anymore when there's no data
    if data["reports"]["total_uploads"] == 0:
        assert data["reports"]["success_rate_pct"] is None
        assert data["reports"]["failure_rate_pct"] is None
        assert data["reports"]["avg_processing_time_sec"] is None

    if data["ai"]["total_requests"] == 0:
        assert data["ai"]["success_rate_pct"] is None
        assert data["ai"]["avg_latency_ms"] is None


def test_average_processing_duration_is_database_independent():
    uploaded_at = datetime(2026, 9, 27, 9, 0, 0)
    assert (
        _average_duration_seconds(
            [
                (uploaded_at + timedelta(seconds=60), uploaded_at),
                (uploaded_at + timedelta(seconds=180), uploaded_at),
            ]
        )
        == 120.0
    )
    assert _average_duration_seconds([]) is None
