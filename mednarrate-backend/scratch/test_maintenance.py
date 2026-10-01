import asyncio
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.security import create_access_token
from app.core.database import AsyncSessionLocal
from sqlalchemy.future import select
from app.models.user import User, UserRole

async def get_tokens():
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.role == UserRole.patient))).scalars().first()
        admin = (await db.execute(select(User).where(User.email == "admin@mednarrate.com"))).scalars().first()
        if not user:
            user = User(email="patient@test.com", hashed_password="pw", role=UserRole.patient, is_active=True)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return create_access_token({"sub": str(user.id)}), create_access_token({"sub": str(admin.id)})

@pytest.mark.asyncio
async def test_maintenance():
    user_token, admin_token = await get_tokens()
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Enable chat maintenance
        resp = await client.post("/api/v1/admin/settings/maintenance", json={"scope": "chat", "is_enabled": True, "reason": "Testing"}, headers={"Authorization": f"Bearer {admin_token}"})
        print("Enable chat maintenance:", resp.status_code, resp.text)
        
        # Test chat
        resp = await client.post("/api/v1/chat/sessions", json={"title": "Test"}, headers={"Authorization": f"Bearer {user_token}"})
        print("Chat blocked?", resp.status_code, resp.text)
        
        # Disable
        await client.post("/api/v1/admin/settings/maintenance", json={"scope": "chat", "is_enabled": False, "reason": ""}, headers={"Authorization": f"Bearer {admin_token}"})
        
        # Test chat again
        resp = await client.post("/api/v1/chat/sessions", json={"title": "Test"}, headers={"Authorization": f"Bearer {user_token}"})
        print("Chat working?", resp.status_code, resp.text)

if __name__ == "__main__":
    asyncio.run(test_maintenance())
