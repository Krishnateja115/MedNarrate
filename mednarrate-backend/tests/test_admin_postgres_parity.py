import uuid
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment, AdminAuditLog
from app.models.report import Report, ProcessingStatus, FileType, ReportType
from app.models.incidents import Incident, IncidentStatus, IncidentSeverity
from app.models.support import SupportTicket, TicketStatus, TicketPriority, TicketCategory
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.core.security import create_access_token


@pytest.fixture
async def full_admin_user(db_session: AsyncSession):
    user = User(
        email=f"parity_admin_{uuid.uuid4()}@example.com",
        hashed_password="hashed_password",
        full_name="Parity Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.flush()

    role = AdminRole(
        name=f"Full Access {uuid.uuid4()}", description="Full access"
    )
    db_session.add(role)
    await db_session.flush()

    perms = ["dashboard.view", "system.health.view", "incidents.view", "reports.diagnostics.view"]
    from sqlalchemy import select

    for p_name in perms:
        stmt = select(AdminPermission).where(AdminPermission.name == p_name)
        perm = (await db_session.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name=p_name, description="Test perm")
            db_session.add(perm)
            await db_session.flush()
        db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))

    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))

    # 1. Failed reports
    now = datetime.utcnow()
    db_session.add(Report(
        user_id=user.id, title="Failed Report", file_name="f.pdf", file_path="/f.pdf",
        file_type=FileType.pdf, report_type=ReportType.other,
        processing_status=ProcessingStatus.failed, uploaded_at=now, report_date=now.date()
    ))
    db_session.add(Report(
        user_id=user.id, title="Completed Report", file_name="c.pdf", file_path="/c.pdf",
        file_type=FileType.pdf, report_type=ReportType.other,
        processing_status=ProcessingStatus.completed, uploaded_at=now, report_date=now.date()
    ))

    # 2. SEV-1 and SEV-2 Incidents
    db_session.add(Incident(
        title="DB Down", severity=IncidentSeverity.sev1, status=IncidentStatus.open,
        affected_service="database", created_at=now
    ))
    db_session.add(Incident(
        title="High Latency", severity=IncidentSeverity.sev2, status=IncidentStatus.investigating,
        affected_service="api", created_at=now
    ))

    # 3. P1 and P2 Support Tickets
    db_session.add(SupportTicket(
        user_id=user.id, title="Cannot login", description="Help", category=TicketCategory.login,
        priority=TicketPriority.p1, status=TicketStatus.new
    ))
    db_session.add(SupportTicket(
        user_id=user.id, title="Slow UI", description="Help", category=TicketCategory.performance,
        priority=TicketPriority.p2, status=TicketStatus.investigating
    ))

    # 4. LLM Diagnostic Error
    db_session.add(LLMDiagnosticEvent(
        provider="gemini", model_name="gemini-pro",
        status="error", error_category="timeout", latency_ms=5000.0,
        timestamp=now
    ))

    # 5. Admin Audit Security Event
    db_session.add(AdminAuditLog(
        actor_admin_id=user.id, action="FAILED_ADMIN_LOGIN", result="failure",
        reason="bad password", timestamp=now
    ))

    await db_session.commit()
    return {"user": user, "token": create_access_token(str(user.id))}


@pytest.mark.asyncio
async def test_postgres_enum_parity_dashboard_summary(client: AsyncClient, full_admin_user: dict):
    headers = {"Authorization": f"Bearer {full_admin_user['token']}"}
    response = await client.get("/api/v1/admin/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Verify accurate reporting of inserted data
    assert data["reports"]["reports_failed"] >= 1
    assert data["reports"]["reports_completed"] >= 1
    assert data["incidents"]["critical_incidents"] >= 2
    assert data["incidents"]["open_incidents"] >= 2
    assert data["support"]["p1_tickets"] >= 1
    assert data["support"]["p2_tickets"] >= 1
    assert data["support"]["open_support_tickets"] >= 2


@pytest.mark.asyncio
async def test_postgres_enum_parity_dashboard_alerts(client: AsyncClient, full_admin_user: dict):
    headers = {"Authorization": f"Bearer {full_admin_user['token']}"}
    response = await client.get("/api/v1/admin/alerts", headers=headers)
    assert response.status_code == 200
    data = response.json()

    alerts = data.get("alerts", [])
    assert len(alerts) > 0

    categories = [a["category"] for a in alerts]
    assert "incident" in categories
    assert "report" in categories
    assert "support" in categories
    assert "ai" in categories
    assert "security" in categories
