import urllib.request
import json
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token

async def get_token():
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email=='admin@mednarrate.com'))).scalar()
        if user:
            return create_access_token(user.id)
    return None

token = asyncio.run(get_token())
if token:
    req = urllib.request.Request('http://localhost:8000/api/v1/admin/system/health', headers={'Cookie': f'access_token={token}'})
    try:
        with urllib.request.urlopen(req) as response:
            print(json.dumps(json.loads(response.read()), indent=2))
    except Exception as e:
        print(e)
