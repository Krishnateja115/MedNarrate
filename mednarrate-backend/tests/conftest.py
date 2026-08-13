import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.core.config import settings
import asyncio

from sqlalchemy.pool import NullPool
engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
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
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
async def token_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_part3@example.com", "password": "Password1", "full_name": "Part3 User"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_part3@example.com", "password": "Password1"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
