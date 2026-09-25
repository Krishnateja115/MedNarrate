import asyncio
from app.core.database import AsyncSessionLocal
from app.api.v1.admin_health import get_system_health
from fastapi import Request

# Create a mock AdminContext
from app.models.user import User
from app.core.admin_auth import AdminContext

async def check():
    async with AsyncSessionLocal() as session:
        mock_user = User(id="00000000-0000-0000-0000-000000000000")
        ctx = AdminContext(user=mock_user, permissions=["super_admin"])
        result = await get_system_health(admin_ctx=ctx, db=session)
        print(result)

asyncio.run(check())
