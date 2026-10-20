import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.user import User, UserRole


@pytest.fixture
async def ai_config_admin(db_session: AsyncSession):
    user = User(
        email=f"aiconfig_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="AI Config Admin",
        role=UserRole.admin,
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
async def test_ai_config_does_not_leak_key(
    client: AsyncClient, ai_config_admin: User, db_session: AsyncSession
):
    """Ensure GET /ai-config never returns masked_key or raw key"""
    token = create_access_token(subject=str(ai_config_admin.id))

    # First, set a key
    put_resp = await client.put(
        "/api/v1/admin/ai-config",
        json={"api_key": "sk-super-secret-key-12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_resp.status_code == 200

    # Read config back
    get_resp = await client.get(
        "/api/v1/admin/ai-config", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 200

    data = get_resp.json()
    assert data["api_key_status"]["is_set"] is True
    assert "masked_key" not in data["api_key_status"]
    assert "sk-" not in str(data)

@pytest.mark.asyncio
async def test_ai_config_key_is_encrypted_in_db(
    client: AsyncClient, ai_config_admin: User, db_session: AsyncSession
):
    token = create_access_token(subject=str(ai_config_admin.id))
    secret_key = "sk-super-secret-db-key-98765"

    put_resp = await client.put(
        "/api/v1/admin/ai-config",
        json={"api_key": secret_key},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_resp.status_code == 200

    from app.models.system_setting import SystemSetting
    stmt = select(SystemSetting).where(SystemSetting.key == "ai_api_key")
    res = await db_session.execute(stmt)
    setting = res.scalar_one_or_none()

    assert setting is not None
    # Verify the plaintext key is NOT stored in the DB
    assert setting.value != secret_key
    assert secret_key not in setting.value

    # Verify we can decrypt it back
    from app.core.encryption import decrypt_value
    decrypted = decrypt_value(setting.value)
    assert decrypted == secret_key


@pytest.mark.asyncio
async def test_ai_config_rejects_unknown_provider_and_bad_model(
    client: AsyncClient, ai_config_admin: User
):
    """A typo here would otherwise break every AI request for every user."""
    token = create_access_token(subject=str(ai_config_admin.id))
    headers = {"Authorization": f"Bearer {token}"}
    for payload in (
        {"primary_provider": "gemni"},
        {"fallback_provider": "ollamaa"},
        {"model_name": "bad model; drop table"},
        {"model_name": ""},
    ):
        res = await client.put("/api/v1/admin/ai-config", json=payload, headers=headers)
        assert res.status_code == 422, (payload, res.text)

    ok = await client.put(
        "/api/v1/admin/ai-config",
        json={"primary_provider": "Gemini", "model_name": "gemini-3.1-flash-lite", "fallback_provider": "fallback"},
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    cfg = (await client.get("/api/v1/admin/ai-config", headers=headers)).json()
    assert cfg["primary_provider"] == "gemini"
    assert cfg["model_name"] == "gemini-3.1-flash-lite"
    assert cfg["fallback_provider"] == "fallback"
    assert "primary_provider" in cfg["overridden"]


@pytest.mark.asyncio
async def test_ai_config_accepts_every_provider_the_admin_page_offers(
    client: AsyncClient, ai_config_admin: User
):
    """The admin dropdown lists these; the server must accept each one it shows."""
    token = create_access_token(subject=str(ai_config_admin.id))
    headers = {"Authorization": f"Bearer {token}"}
    for name in ("gemini", "groq", "groq_qwen", "openrouter", "vertex_ai", "ollama"):
        res = await client.put(
            "/api/v1/admin/ai-config",
            json={"primary_provider": name, "fallback_provider": name},
            headers=headers,
        )
        assert res.status_code == 200, (name, res.text)
