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
from app.services.llm_client import llm_client_instance


@pytest.fixture
async def health_admin(db_session: AsyncSession):
    user = User(
        email=f"health_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Health Admin",
        role=UserRole.admin,
    )
    db_session.add(user)

    role = AdminRole(name=f"Health Admin_{uuid.uuid4()}")
    db_session.add(role)

    stmt = select(AdminPermission).where(AdminPermission.name == "system.health.view")
    perm = (await db_session.execute(stmt)).scalars().first()
    if not perm:
        perm = AdminPermission(name="system.health.view")
        db_session.add(perm)

    await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_health_check_returns_all_services(
    client: AsyncClient, health_admin: User
):
    """Ensure the health endpoint checks all required core services and does not leak info"""
    token = create_access_token(subject=str(health_admin.id))

    # Overwrite LLM health check behavior for testing to simulate successful test request
    original_get_provider = llm_client_instance.get_provider

    class MockProvider:
        async def health_check(self, config: dict | None = None):
            return {"reachable": True, "configured": True, "request_successful": True}

    def mock_get_provider(*args, **kwargs):
        return MockProvider()

    llm_client_instance.get_provider = mock_get_provider

    try:
        resp = await client.get(
            "/api/v1/admin/system/health", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200

        data = resp.json()
        assert "status" in data
        assert "services" in data

        services = data["services"]
        assert "api" in services
        assert "database" in services
        assert "llm_provider" in services
        assert "storage" in services
        assert "scheduler" in services
        assert "rag" in services
        assert "report_worker" in services
        for name in ("api", "database", "llm_provider", "storage", "rag"):
            assert isinstance(services[name]["latency_ms"], (int, float))
            assert services[name]["latency_ms"] >= 0
        assert services["scheduler"]["latency_ms"] is None

        refreshed = await client.get(
            "/api/v1/admin/system/health", headers={"Authorization": f"Bearer {token}"}
        )
        assert refreshed.status_code == 200
        assert refreshed.json()["timestamp"] != data["timestamp"]
        assert refreshed.json()["services"]["api"]["latency_ms"] >= 0

        # Ensure no sensitive details are exposed
        for service_name, details in services.items():
            if "details" in details:
                assert "api_key" not in details["details"]
                assert "password" not in details["details"]
    finally:
        llm_client_instance.get_provider = original_get_provider

@pytest.mark.asyncio
async def test_root_health_check_reports_unmigrated_db(
    client: AsyncClient, db_session_factory, monkeypatch: pytest.MonkeyPatch
):
    """A reachable database without Alembic history is not healthy."""
    from app.core import database

    monkeypatch.setattr(database, "AsyncSessionLocal", db_session_factory)
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["db"] == "down"
    assert data["schema_revision"] is None
