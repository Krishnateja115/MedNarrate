import asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient
from app.core.security import create_access_token
from app.core.database import get_db
import uuid

async def run():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        uid = uuid.uuid4()
        token = create_access_token(str(uid))
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
