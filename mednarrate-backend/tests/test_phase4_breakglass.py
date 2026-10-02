import pytest
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.admin import SensitiveAccessGrant
from app.models.medical_profile import MedicalProfile
from app.core.security import create_access_token

@pytest.fixture
async def target_user_with_profile(db_session, target_user):
    from datetime import date
    prof = MedicalProfile(
        id=uuid.uuid4(),
        user_id=target_user.id,
        blood_group="O+",
    )
    db_session.add(prof)
    await db_session.commit()
    return target_user

async def create_grant(db_session, admin_id, resource_type, resource_id, status, expires_delta=timedelta(hours=1)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    g = SensitiveAccessGrant(
        id=uuid.uuid4(),
        admin_id=admin_id,
        resource_type=resource_type,
        resource_id=resource_id,
        reason="test",
        requested_duration_hours=1,
        created_at=now,
        expires_at=now + expires_delta,
        status=status,
    )
    db_session.add(g)
    await db_session.commit()
    return g

@pytest.mark.asyncio
async def test_breakglass_unknown_resource_type(client: AsyncClient, admin_token_and_user):
    headers, admin = admin_token_and_user
    resp = await client.request(
        "POST",
        "/api/v1/admin/break-glass/request",
        headers=headers,
        json={
            "resource_type": "unknown_type",
            "resource_id": "123",
            "reason": "Need access for unknown",
            "expires_in_hours": 1
        }
    )
    assert resp.status_code == 400
    assert "Invalid resource type" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_superadmin_denied_without_grant(client: AsyncClient, admin_token_and_user, target_user_with_profile):
    headers, admin = admin_token_and_user
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403
    assert "No active sensitive access grant" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_breakglass_states(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user_with_profile):
    headers, admin = admin_token_and_user
    
    # 1. requested grant -> 403
    g = await create_grant(db_session, admin.id, "medical_profile", str(target_user_with_profile.id), "requested")
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403
    
    # 2. revoked grant with future expires_at -> 403
    g.status = "revoked"
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403
    
    # 3. expired grant (status active but time past) -> 403
    g.status = "active"
    g.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403
    
    # 4. wrong admin -> 403
    g.status = "active"
    g.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    g.admin_id = target_user_with_profile.id # some other user to fail the admin_id check
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403
    
    # 5. wrong resource type -> 403
    g.admin_id = admin.id
    g.resource_type = "doctor_profile"
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403
    
    # 6. wrong resource ID -> 403
    g.resource_type = "medical_profile"
    g.resource_id = str(uuid.uuid4())
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 403

    # 7. active exact grant -> success
    g.resource_id = str(target_user_with_profile.id)
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 200
    
    # 8. authorized wildcard -> success
    g.resource_id = "*"
    await db_session.commit()
    resp = await client.request("GET", f"/api/v1/admin/users/{target_user_with_profile.id}/medical_profile", headers=headers)
    assert resp.status_code == 200
