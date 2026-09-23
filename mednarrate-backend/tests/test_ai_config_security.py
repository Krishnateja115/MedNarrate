import pytest
from httpx import AsyncClient
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment
from app.core.security import create_access_token

@pytest.fixture
async def ai_config_admin(db_session: AsyncSession):
    user = User(
        email=f"aiconfig_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="AI Config Admin",
        role=UserRole.admin
    )
    db_session.add(user)
    
    role = AdminRole(name=f"AI Config Admin_{uuid.uuid4()}")
    db_session.add(role)
    
    for perm_name in ["ai_config:manage", "ai_config:read"]:
        stmt = select(AdminPermission).where(AdminPermission.name == perm_name)
        perm = (await db_session.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name=perm_name)
            db_session.add(perm)
        
        await db_session.flush()
        db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user

@pytest.mark.asyncio
async def test_ai_config_does_not_leak_key(client: AsyncClient, ai_config_admin: User, db_session: AsyncSession):
    """Ensure GET /ai-config never returns masked_key or raw key"""
    token = create_access_token(subject=str(ai_config_admin.id))

    # First, set a key
    put_resp = await client.put(
        "/api/v1/admin/ai-config",
        json={"api_key": "sk-super-secret-key-12345"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert put_resp.status_code == 200

    # Read config back
    get_resp = await client.get("/api/v1/admin/ai-config", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 200
    
    data = get_resp.json()
    assert data["api_key_status"]["is_set"] is True
    assert "masked_key" not in data["api_key_status"]
    assert "sk-" not in str(data)
