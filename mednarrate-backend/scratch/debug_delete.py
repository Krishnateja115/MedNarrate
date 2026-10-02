import asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient
from app.core.security import create_access_token
from app.core.database import SessionLocal
import uuid
from app.models.user import User

async def run():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create an admin user to get the token
        resp = await client.post("/api/v1/admin/users/test")
