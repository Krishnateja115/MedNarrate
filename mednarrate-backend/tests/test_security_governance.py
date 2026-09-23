import pytest
from httpx import AsyncClient
import uuid
from app.models.user import User, UserRole
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_admin_security_overview_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/admin/security/overview")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_audit_logs_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_public_announcements_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/admin/announcements/active/public?audience=all&language=en")
    assert response.status_code == 200
    data = response.json()
    assert "active_announcements" in data
    assert isinstance(data["active_announcements"], list)

@pytest.mark.asyncio
async def test_maintenance_mode_status_public(client: AsyncClient):
    response = await client.get("/api/v1/admin/maintenance")
    assert response.status_code == 200
    data = response.json()
    assert "is_enabled" in data
    assert "scope" in data

@pytest.mark.asyncio
async def test_superadmin_governance_flow(client: AsyncClient, db_session):
    # Provision a superadmin user directly in test DB
    superadmin = User(
        id=uuid.uuid4(),
        email="superadmin@mednarrate.test",
        hashed_password=hash_password("SuperSecret123!"),
        full_name="Super Admin",
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(superadmin)

    # Seed SuperAdmin role if not already seeded
    from app.models.admin import AdminRole, AdminRoleAssignment
    from sqlalchemy import select
    sa_role = (await db_session.execute(select(AdminRole).where(AdminRole.name == "Super Admin"))).scalar_one_or_none()
    if not sa_role:
        sa_role = AdminRole(id=uuid.uuid4(), name="Super Admin", description="Super Admin Role")
        db_session.add(sa_role)
        await db_session.flush()

    sa_assignment = AdminRoleAssignment(id=uuid.uuid4(), user_id=superadmin.id, role_id=sa_role.id)
    db_session.add(sa_assignment)

    await db_session.commit()

    # Login as superadmin to get token
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "superadmin@mednarrate.test", "password": "SuperSecret123!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Security Overview
    sec_resp = await client.get("/api/v1/admin/security/overview", headers=headers)
    assert sec_resp.status_code == 200
    sec_data = sec_resp.json()
    assert "total_admins" in sec_data
    assert "active_breakglass_grants" in sec_data

    # 2. Security Events
    evt_resp = await client.get("/api/v1/admin/security/events", headers=headers)
    assert evt_resp.status_code == 200
    assert isinstance(evt_resp.json(), list)

    # 3. Create Feature Flag
    ff_resp = await client.post(
        "/api/v1/admin/feature-flags",
        json={
            "name": "test_flag_v1",
            "description": "Test flag",
            "enabled": True,
            "rollout_percentage": 50,
            "target_environment": "all"
        },
        headers=headers
    )
    assert ff_resp.status_code == 200
    assert ff_resp.json()["flag"]["enabled"] is True

    # 4. List Feature Flags
    ff_list = await client.get("/api/v1/admin/feature-flags", headers=headers)
    assert ff_list.status_code == 200
    assert len(ff_list.json()["flags"]) >= 1

    # 5. AI Config Safe Secret Masking
    ai_resp = await client.get("/api/v1/admin/ai-config", headers=headers)
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    assert "primary_provider" in ai_data
    assert "api_key_status" in ai_data
    # Ensure plaintext API keys are NEVER exposed
    assert "api_key" not in ai_data

    # 6. Break-Glass Access Request & Authoritative Backend Expiration
    bg_resp = await client.post(
        "/api/v1/admin/break-glass/request",
        json={
            "resource_type": "patient_record",
            "resource_id": "rep_9999",
            "reason": "Clinical emergency diagnostic review by attending physician",
            "duration_minutes": 15
        },
        headers=headers
    )
    assert bg_resp.status_code == 200
    grant_id = bg_resp.json()["grant"]["id"]

    # Mark as active manually since self-approval is blocked
    from app.models.admin import SensitiveAccessGrant
    import uuid
    grant = (await db_session.execute(select(SensitiveAccessGrant).where(SensitiveAccessGrant.id == uuid.UUID(grant_id)))).scalar_one()
    grant.status = "active"
    await db_session.commit()

    # Revoke grant
    revoke_resp = await client.post(
        f"/api/v1/admin/break-glass/grants/{grant_id}/revoke", 
        json={"reason": "No longer needed"},
        headers=headers
    )
    assert revoke_resp.status_code == 200

    # 7. Audit Log Read-Only Inspection
    audit_resp = await client.get("/api/v1/admin/audit-logs", headers=headers)
    assert audit_resp.status_code == 200
    assert audit_resp.json()["total"] >= 1
