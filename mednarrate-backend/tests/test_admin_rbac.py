import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment, AdminAuditLog
from sqlalchemy import select

@pytest.fixture
async def regular_user(db_session: AsyncSession):
    user = User(
        email=f"patient_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Patient User",
        role=UserRole.patient
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
async def support_admin(db_session: AsyncSession):
    user = User(
        email=f"support_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Support Admin",
        role=UserRole.admin
    )
    db_session.add(user)
    
    role = AdminRole(name=f"Support Agent_{uuid.uuid4()}")
    db_session.add(role)
    
    stmt = select(AdminPermission).where(AdminPermission.name == "knowledge_base.view")
    perm = (await db_session.execute(stmt)).scalars().first()
    if not perm:
        perm = AdminPermission(name="knowledge_base.view")
        db_session.add(perm)
    
    await db_session.flush()
    
    role_perm = AdminRolePermission(role_id=role.id, permission_id=perm.id)
    db_session.add(role_perm)
    
    assignment = AdminRoleAssignment(user_id=user.id, role_id=role.id)
    db_session.add(assignment)
    
    await db_session.commit()
    return user

@pytest.fixture
async def super_admin(db_session: AsyncSession):
    user = User(
        email=f"super_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Super Admin",
        role=UserRole.admin
    )
    db_session.add(user)

    # Get or create "Super Admin" role (unique constraint on name)
    role = (await db_session.execute(select(AdminRole).where(AdminRole.name == "Super Admin"))).scalar_one_or_none()
    if not role:
        role = AdminRole(name="Super Admin")
        db_session.add(role)

    await db_session.flush()

    assignment = AdminRoleAssignment(user_id=user.id, role_id=role.id)
    db_session.add(assignment)

    await db_session.commit()
    return user

@pytest.mark.asyncio
async def test_non_admin_cannot_access_health(client: AsyncClient, regular_user: User):
    from app.core.security import create_access_token
    token = create_access_token(subject=str(regular_user.id))
    
    resp = await client.get("/api/v1/admin/health", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not an admin"

@pytest.mark.asyncio
async def test_support_admin_can_access_health(client: AsyncClient, support_admin: User, db_session: AsyncSession):
    from app.core.security import create_access_token
    token = create_access_token(subject=str(support_admin.id))
    
    resp = await client.get("/api/v1/admin/health", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    
    # Verify audit log was created
    stmt = select(AdminAuditLog).where(AdminAuditLog.actor_admin_id == support_admin.id, AdminAuditLog.action == "ADMIN_HEALTH_CHECK")
    logs = (await db_session.execute(stmt)).scalars().all()
    assert len(logs) == 1

@pytest.mark.asyncio
async def test_support_admin_can_access_kb(client: AsyncClient, support_admin: User):
    from app.core.security import create_access_token
    token = create_access_token(subject=str(support_admin.id))
    
    resp = await client.get("/api/v1/admin/kb-stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "total_documents" in resp.json()

@pytest.mark.asyncio
async def test_support_admin_denied_privileged_operation(client: AsyncClient, support_admin: User):
    # Support agent has knowledge_base.view, but not ai.view or ai.manage
    from app.core.security import create_access_token
    token = create_access_token(subject=str(support_admin.id))
    
    resp = await client.get("/api/v1/admin/llm-status", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "Requires one of permissions" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_super_admin_bypasses_checks(client: AsyncClient, super_admin: User):
    from app.core.security import create_access_token
    token = create_access_token(subject=str(super_admin.id))
    
    # Super Admin has implicit access to everything
    resp = await client.get("/api/v1/admin/llm-status", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "selected_provider" in resp.json()
