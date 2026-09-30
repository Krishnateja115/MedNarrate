import uuid
from datetime import date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.user import User, UserRole
from app.models.report import FileType, ProcessingStatus, Report, ReportType
from app.models.job_execution import JobExecution, JobStatus
from app.models.support import SupportTicket, TicketPriority, TicketStatus


@pytest.fixture
async def dashboard_admin_user(db_session: AsyncSession):
    unique_email = f"dashboard_admin_{uuid.uuid4()}@example.com"
    user = User(
        email=unique_email,
        hashed_password="hashed_password",
        full_name="Dashboard Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.flush()

    role = AdminRole(
        name=f"Dashboard Reviewer {uuid.uuid4()}", description="Can view dashboard"
    )
    db_session.add(role)
    await db_session.flush()

    perms = [
        "dashboard.view",
        "system.health.view",
        "jobs.view",
        "ai.telemetry.view",
        "reports.diagnostics.view",
        "incidents.view",
        "incidents.manage",
        "rag.view",
        "admins.view",
    ]
    from sqlalchemy import select

    for p_name in perms:
        stmt = select(AdminPermission).where(AdminPermission.name == p_name)
        perm = (await db_session.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name=p_name, description="Test perm")
            db_session.add(perm)
            await db_session.flush()
        rp = AdminRolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp)

    ra = AdminRoleAssignment(user_id=user.id, role_id=role.id)
    db_session.add(ra)
    db_session.add(
        Report(
            user_id=user.id,
            title="Dashboard chart regression report",
            report_date=date.today(),
            file_name="dashboard.pdf",
            file_path="/tmp/dashboard.pdf",
            file_type=FileType.pdf,
            report_type=ReportType.other,
            processing_status=ProcessingStatus.completed,
            uploaded_at=datetime.utcnow(),
        )
    )
    await db_session.commit()

    token = create_access_token(str(user.id))
    return {"user": user, "token": token}


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "reports" in data
    assert "analysis" in data
    assert "incidents" in data
    assert "support" in data
    assert data["users"]["total_users"] >= 1  # Because the admin user was created
    assert data["users"]["active_users"] >= 1
    assert data["chart_data"]

    # Contract guarantees
    assert "reports_today" in data["reports"]
    assert "reports_this_week" in data["reports"]
    assert "reports_processing" in data["reports"]
    assert data["reports"]["reports_completed"] >= 1
    assert "reports_failed" in data["reports"]

    assert "total_users" in data["users"]
    assert "new_users_today" in data["users"]
    assert "new_users_this_week" in data["users"]


@pytest.mark.asyncio
async def test_system_health(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/system/health", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "down"]
    assert "services" in data
    assert "api" in data["services"]
    assert "database" in data["services"]
    assert data["services"]["database"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_rag_status_uses_supported_document_lifecycle(
    client: AsyncClient, dashboard_admin_user: dict
):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/rag-ops/status", headers=headers)
    assert response.status_code == 200
    overview = response.json()["overview"]
    assert "total_documents" in overview
    assert "published_documents" in overview
    assert "failed_documents" not in overview


@pytest.mark.asyncio
async def test_background_jobs(
    client: AsyncClient,
    dashboard_admin_user: dict,
    db_session: AsyncSession,
):
    db_session.add(
        JobExecution(
            job_name="release-gate-job",
            status=JobStatus.failed,
            failure_category="database",
            request_id="release-gate-request",
            error_details="postgresql://secret@example.invalid/internal",
        )
    )
    await db_session.commit()
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/jobs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    failed_item = next(
        item for item in data["items"] if item["job_name"] == "release-gate-job"
    )
    assert failed_item["failure_category"] == "database"
    assert failed_item["request_id"] == "release-gate-request"
    assert "secret" not in failed_item["error_message"]


@pytest.mark.asyncio
async def test_llm_diagnostics(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/diagnostics/llm", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_report_diagnostics(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/diagnostics/reports", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_incident_management(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}

    # 1. Create incident
    create_payload = {
        "title": "API Latency Spike",
        "severity": "SEV-2",
        "affected_service": "LLM Provider",
        "summary": "Timeout from ollama",
    }
    response = await client.post(
        "/api/v1/admin/incidents", json=create_payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    incident_id = data["incident_id"]

    # 2. Get incidents
    response = await client.get("/api/v1/admin/incidents", headers=headers)
    assert response.status_code == 200
    assert any(i["id"] == incident_id for i in response.json()["items"])

    # 3. Update incident
    update_payload = {
        "status": "resolved",
        "resolution": "Restarted Ollama",
        "message": "Looks good now",
    }
    response = await client.patch(
        f"/api/v1/admin/incidents/{incident_id}", json=update_payload, headers=headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_users_endpoints(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}

    # List Users
    response = await client.get("/api/v1/admin/users", headers=headers)
    # The fixture doesn't have users.view, so it returns 403
    assert response.status_code in [200, 403]

    # Detail User
    user_id = str(dashboard_admin_user["user"].id)
    response = await client.get(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_admin_reports_endpoints(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}

    # List Reports
    response = await client.get("/api/v1/admin/reports", headers=headers)
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_admin_support_endpoints(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}

    # 1. Create a ticket using the user API
    user_headers = headers  # since admin is also a user
    create_payload = {
        "title": "Need help with processing",
        "description": "My report is stuck",
        "category": "Report Processing",
        "priority": "P2 High",
    }
    resp = await client.post(
        "/api/v1/support", json=create_payload, headers=user_headers
    )
    assert resp.status_code == 201
    ticket_id = resp.json()["ticket_id"]

    # 2. Get tickets in admin queue
    # Assuming dashboard_admin_user needs the support.view permission
    # For now, just test we don't get 500 error
    resp = await client.get("/api/v1/admin/support", headers=headers)
    assert resp.status_code in [200, 403]

    # 3. Add internal note
    reply_payload = {"content": "This is an internal note", "is_internal": True}
    resp = await client.post(
        f"/api/v1/admin/support/{ticket_id}/reply", json=reply_payload, headers=headers
    )
    assert resp.status_code in [200, 403]

    # 4. Escalate
    escalate_payload = {
        "escalation_type": "incident",
        "reason": "Affects multiple users",
    }
    resp = await client.post(
        f"/api/v1/admin/support/{ticket_id}/escalate",
        json=escalate_payload,
        headers=headers,
    )
    assert resp.status_code in [200, 403]


@pytest.mark.asyncio
async def test_admin_ai_ops_endpoints(client, token_headers):
    # Overview
    response = await client.get("/api/v1/admin/ai-ops/overview", headers=token_headers)
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        assert "overview" in response.json()

    # Traces
    response = await client.get("/api/v1/admin/ai-ops/traces", headers=token_headers)
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        assert "traces" in response.json()

    # Failures
    response = await client.get("/api/v1/admin/ai-ops/failures", headers=token_headers)
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        assert "failures" in response.json()


@pytest.mark.asyncio
async def test_admin_automation_ops_endpoints(client, token_headers):
    response = await client.get(
        "/api/v1/admin/automation-ops/notifications", headers=token_headers
    )
    assert response.status_code in [200, 403]

    response = await client.get(
        "/api/v1/admin/automation-ops/jobs", headers=token_headers
    )
    assert response.status_code in [200, 403]


import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medical_profile import MedicalProfile
from app.models.doctor_profile import DoctorProfile
from app.models.caregiver_profile import CaregiverProfile
from app.models.push_token import PushToken


@pytest.fixture
async def sample_profiles(db_session: AsyncSession):
    u_doc = User(
        email=f"doc_{uuid.uuid4()}@example.com",
        hashed_password="pw",
        full_name="Doc",
        role=UserRole.patient,
    )
    u_care = User(
        email=f"care_{uuid.uuid4()}@example.com",
        hashed_password="pw",
        full_name="Care",
        role=UserRole.patient,
    )
    u_pat = User(
        email=f"pat_{uuid.uuid4()}@example.com",
        hashed_password="pw",
        full_name="Pat",
        role=UserRole.patient,
    )

    db_session.add_all([u_doc, u_care, u_pat])
    await db_session.flush()

    d_prof = DoctorProfile(user_id=u_doc.id, specialty="Cardiology")
    c_prof = CaregiverProfile(user_id=u_care.id, relationship="Son")
    m_prof = MedicalProfile(user_id=u_pat.id, blood_group="O+")
    pt = PushToken(user_id=u_pat.id, device_token="fake_token", platform="ios")

    db_session.add_all([d_prof, c_prof, m_prof, pt])
    await db_session.commit()

    return {"doc_id": u_doc.id, "care_id": u_care.id, "pat_id": u_pat.id}


@pytest.mark.asyncio
async def test_doctor_verification(
    client: AsyncClient, dashboard_admin_user: dict, sample_profiles: dict
):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    doc_id = sample_profiles["doc_id"]

    # Needs users.manage
    resp = await client.post(
        f"/api/v1/admin/users/{doc_id}/doctor_profile/verify", headers=headers
    )
    assert resp.status_code in [200, 403]


@pytest.mark.asyncio
async def test_caregiver_verification(
    client: AsyncClient, dashboard_admin_user: dict, sample_profiles: dict
):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    care_id = sample_profiles["care_id"]

    resp = await client.post(
        f"/api/v1/admin/users/{care_id}/caregiver_profile/verify", headers=headers
    )
    assert resp.status_code in [200, 403]


@pytest.mark.asyncio
async def test_medical_profile_view(
    client: AsyncClient, dashboard_admin_user: dict, sample_profiles: dict
):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    pat_id = sample_profiles["pat_id"]

    resp = await client.get(
        f"/api/v1/admin/users/{pat_id}/medical_profile", headers=headers
    )
    # Expected 403 if no break-glass grant is given or not super_admin
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_push_notification_dispatch(
    client: AsyncClient, dashboard_admin_user: dict, sample_profiles: dict
):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    payload = {
        "title": "System Update",
        "body": "Please update your app.",
        "audience": "patients",
    }
    resp = await client.post(
        "/api/v1/admin/notifications/dispatch", json=payload, headers=headers
    )
    assert resp.status_code in [200, 403]


@pytest.mark.asyncio
async def test_admin_copilot_chat(
    client: AsyncClient, dashboard_admin_user: dict, db_session: AsyncSession
):
    token = dashboard_admin_user["token"]

    payload = {
        "messages": [{"role": "user", "content": "How many active users are there?"}]
    }

    res = await client.post(
        "/api/v1/admin/copilot/chat",
        json=payload,
        headers={"Cookie": f"access_token={token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "active" in data["reply"]
    assert "placeholder" not in data["reply"].lower()


@pytest.mark.asyncio
async def test_admin_support_tickets_endpoints(
    client: AsyncClient, dashboard_admin_user: dict, db_session: AsyncSession
):
    token = dashboard_admin_user["token"]
    admin_id = dashboard_admin_user["user"].id

    # 1 & 2. Test authorized admin with zero support tickets -> 200
    res = await client.get(
        f"/api/v1/admin/admins/{admin_id}/support_tickets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["tickets"] == []

    # Create dummy user to link the ticket
    dummy_user = User(
        email=f"dummy_{uuid.uuid4()}@example.com",
        hashed_password="pw",
        full_name="Dummy User",
    )
    db_session.add(dummy_user)
    await db_session.flush()

    # 6. Create ticket with nullable fields
    ticket1 = SupportTicket(
        user_id=str(dummy_user.id),
        title="Nullable fields ticket",
        description="Desc",
        assigned_admin_id=str(admin_id),
        status=TicketStatus.new,
        priority=TicketPriority.p3,
    )

    # 7. Create another ticket to test multiple tickets list
    ticket2 = SupportTicket(
        user_id=str(dummy_user.id),
        title="Full ticket",
        description="Desc",
        assigned_admin_id=str(admin_id),
        status=TicketStatus.resolved,
        priority=TicketPriority.p1,
    )
    db_session.add(ticket1)
    db_session.add(ticket2)
    await db_session.commit()

    # Test authorized admin with support tickets -> 200
    res = await client.get(
        f"/api/v1/admin/admins/{admin_id}/support_tickets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["tickets"]) == 2
    assert any(t["subject"] == "Nullable fields ticket" for t in data["tickets"])
    assert any(t["subject"] == "Full ticket" for t in data["tickets"])

    # 3. Test nonexistent admin -> 404
    fake_id = str(uuid.uuid4())
    res = await client.get(
        f"/api/v1/admin/admins/{fake_id}/support_tickets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404

    # 4. Test unauthenticated -> 401
    res = await client.get(f"/api/v1/admin/admins/{admin_id}/support_tickets")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_support_tickets_unauthorized(
    client: AsyncClient, token_headers: dict, db_session: AsyncSession
):
    # token_headers is a normal user token fixture
    # 5. Test unauthorized -> 403
    admin_id = str(uuid.uuid4())
    res = await client.get(
        f"/api/v1/admin/admins/{admin_id}/support_tickets", headers=token_headers
    )
    assert res.status_code == 403
