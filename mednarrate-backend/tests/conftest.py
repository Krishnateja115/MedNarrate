import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Register all models with Base.metadata
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminRoleAssignment
from app.core.security import hash_password

from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(request, db_session):
    async def override_get_db():
        yield db_session

    from app.core.admin_auth import require_active_step_up, get_admin_context
    from fastapi import Depends

    app.dependency_overrides[get_db] = override_get_db
    
    if "phase4" not in request.node.fspath.strpath and "breakglass" not in request.node.fspath.strpath:
        async def mock_require_active_step_up(admin_ctx = Depends(get_admin_context)):
            return admin_ctx
        app.dependency_overrides[require_active_step_up] = mock_require_active_step_up

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def token_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_part3@example.com",
            "password": "StrongP@ssword1",
            "full_name": "Part3 User",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_part3@example.com", "password": "StrongP@ssword1"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

import uuid
from datetime import date
from app.core.security import hash_password
from app.models.report import Report
from app.models.admin import AdminRole, AdminRoleAssignment

@pytest.fixture
async def target_user(db_session: AsyncSession):
    rand = uuid.uuid4().hex[:6]
    u = User(
        email=f"target_{rand}@example.com",
        hashed_password=hash_password("StrongP@ssword1"),
        full_name="Target User",
        role=UserRole.patient
    )
    db_session.add(u)
    await db_session.commit()
    
    r = Report(
        user_id=u.id,
        file_path=f"{u.id}/report.pdf",
        title="Target Report",
        hospital="Test Hospital",
        report_date=date(2023, 1, 1),
        file_name="report.pdf",
        file_type="pdf",
        report_type="blood",
        processing_status="completed"
    )
    db_session.add(r)
    await db_session.commit()
    return u

@pytest.fixture
async def bystander_user(db_session: AsyncSession):
    rand = uuid.uuid4().hex[:6]
    u = User(
        email=f"bystander_{rand}@example.com",
        hashed_password=hash_password("StrongP@ssword1"),
        full_name="Bystander User",
        role=UserRole.patient
    )
    db_session.add(u)
    await db_session.commit()
    
    r = Report(
        user_id=u.id,
        file_path=f"{u.id}/report.pdf",
        title="Bystander Report",
        hospital="Test Hospital",
        report_date=date(2023, 1, 1),
        file_name="report.pdf",
        file_type="pdf",
        report_type="blood",
        processing_status="completed"
    )
    db_session.add(r)
    await db_session.commit()
    return u

@pytest.fixture
async def admin_token_and_user(client: AsyncClient, db_session: AsyncSession):
    from sqlalchemy import select
    rand = uuid.uuid4().hex[:6]
    role = (await db_session.execute(select(AdminRole).where(AdminRole.name == "Super Admin"))).scalars().first()
    if not role:
        try:
            role = AdminRole(name="Super Admin", description="SA")
            db_session.add(role)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            role = (await db_session.execute(select(AdminRole).where(AdminRole.name == "Super Admin"))).scalars().first()
    
    user = User(
        email=f"admin4_{rand}@example.com",
        hashed_password=hash_password("StrongP@ssword1"),
        full_name="Admin4",
        role=UserRole.admin,
        mfa_enabled=True,
        mfa_secret=b"ENCRYPTED_SECRET"
    )
    db_session.add(user)
    await db_session.commit()
    
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id, assigned_by_id=user.id))
    await db_session.commit()
    
    user2 = User(email=f"admin5_{rand}@example.com", hashed_password=hash_password("P@ss1"), role=UserRole.admin, full_name="Admin5")
    db_session.add(user2)
    await db_session.commit()
    db_session.add(AdminRoleAssignment(user_id=user2.id, role_id=role.id, assigned_by_id=user.id))
    await db_session.commit()
    
    from app.core.security import create_access_token
    token = create_access_token(str(user.id), user.session_version)
    return {"Authorization": f"Bearer {token}"}, user
