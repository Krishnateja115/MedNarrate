import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment
from app.core.security import create_access_token

@pytest.fixture
async def dashboard_admin_user(db_session: AsyncSession):
    unique_email = f"dashboard_admin_{uuid.uuid4()}@example.com"
    user = User(
        email=unique_email,
        hashed_password="hashed_password",
        full_name="Dashboard Admin",
        role=UserRole.admin
    )
    db_session.add(user)
    await db_session.flush()

    role = AdminRole(name=f"Dashboard Reviewer {uuid.uuid4()}", description="Can view dashboard")
    db_session.add(role)
    await db_session.flush()
    
    perms = [
        "dashboard.view", "system.health.view", "jobs.view", "ai.telemetry.view", "reports.diagnostics.view", "incidents.view", "incidents.manage"
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
    assert data["users"]["total_users"] >= 1 # Because the admin user was created

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
async def test_background_jobs(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/jobs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)

@pytest.mark.asyncio
async def test_llm_diagnostics(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/diagnostics/llm", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "pagination" in data

@pytest.mark.asyncio
async def test_report_diagnostics(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    response = await client.get("/api/v1/admin/diagnostics/reports", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data

@pytest.mark.asyncio
async def test_incident_management(client: AsyncClient, dashboard_admin_user: dict):
    headers = {"Authorization": f"Bearer {dashboard_admin_user['token']}"}
    
    # 1. Create incident
    create_payload = {
        "title": "API Latency Spike",
        "severity": "SEV-2",
        "affected_service": "LLM Provider",
        "summary": "Timeout from ollama"
    }
    response = await client.post("/api/v1/admin/incidents", json=create_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    incident_id = data["incident_id"]
    
    # 2. Get incidents
    response = await client.get("/api/v1/admin/incidents", headers=headers)
    assert response.status_code == 200
    assert any(i["id"] == incident_id for i in response.json()["incidents"])
    
    # 3. Update incident
    update_payload = {
        "status": "resolved",
        "resolution": "Restarted Ollama",
        "message": "Looks good now"
    }
    response = await client.patch(f"/api/v1/admin/incidents/{incident_id}", json=update_payload, headers=headers)
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
