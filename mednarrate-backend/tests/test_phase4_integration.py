import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminRoleAssignment, SensitiveAccessGrant, AdminAuditLog
from app.models.report import Report
from app.core.security import hash_password, create_step_up_token
from datetime import datetime, timezone, timedelta, date
from app.core.admin_auth import require_active_step_up
from app.main import app
import uuid

# Unmock require_active_step_up for Phase 4 tests
app.dependency_overrides.pop(require_active_step_up, None)

@pytest.mark.asyncio
async def test_hard_delete_cleans_everything(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user, bystander_user):
    headers, admin = admin_token_and_user

    # Create step up token
    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up

    # Run hard delete
    resp = await client.request("DELETE", f"/api/v1/admin/users/{target_user.id}", headers=headers, json={"reason": "test", "confirmation": f"DELETE {target_user.id}"})
    assert resp.status_code == 200

    # Assert target is gone
    target_check = await db_session.execute(select(User).where(User.id == target_user.id))
    assert target_check.scalars().first() is None

    target_report_check = await db_session.execute(select(Report).where(Report.user_id == target_user.id))
    assert len(target_report_check.scalars().all()) == 0

    # Assert bystander remains
    bystander_check = await db_session.execute(select(User).where(User.id == bystander_user.id))
    assert bystander_check.scalars().first() is not None

    bystander_report_check = await db_session.execute(select(Report).where(Report.user_id == bystander_user.id))
    assert len(bystander_report_check.scalars().all()) == 1

@pytest.mark.asyncio
async def test_step_up_requires_privileged_type(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user):
    headers, admin = admin_token_and_user

    import jwt
    from app.core.config import settings

    # Create an invalid type token
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {
        "exp": expire,
        "sub": str(admin.id),
        "type": "access", # INVALID
        "session_version": admin.session_version,
        "jti": str(uuid.uuid4())
    }
    bad_step_up = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    headers["x-step-up-token"] = bad_step_up

    resp = await client.request("DELETE", f"/api/v1/admin/users/{target_user.id}", headers=headers, json={"reason": "test", "confirmation": f"DELETE {target_user.id}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token type"

@pytest.mark.asyncio
async def test_step_up_stale_session_version(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user):
    headers, admin = admin_token_and_user

    # Create step up token with OLD session version
    step_up = create_step_up_token(str(admin.id), admin.session_version - 1)
    headers["x-step-up-token"] = step_up

    resp = await client.request("DELETE", f"/api/v1/admin/users/{target_user.id}", headers=headers, json={"reason": "test", "confirmation": f"DELETE {target_user.id}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Step-up token session version is invalid"

@pytest.mark.asyncio
async def test_super_admin_cannot_delete_self(client: AsyncClient, db_session: AsyncSession, admin_token_and_user):
    headers, admin = admin_token_and_user
    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up

    resp = await client.request("DELETE", f"/api/v1/admin/users/{admin.id}", headers=headers, json={"reason": "test", "confirmation": f"DELETE {admin.id}"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot delete yourself"
