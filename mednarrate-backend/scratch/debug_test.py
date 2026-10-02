import asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient
from app.core.security import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

async def run():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Just send the payload with a random token
        token = create_access_token("some-id")
        resp = await client.post(
            "/api/v1/admin/break-glass/request",
            json={
                "resource_type": "medical_report",
                "resource_id": "rep_123",
                "reason": "Emergency review",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        print("Status:", resp.status_code)
        print("Response:", resp.text)

asyncio.run(run())
