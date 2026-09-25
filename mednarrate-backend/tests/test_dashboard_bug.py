import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.api.v1.admin_dashboard import get_dashboard_summary

async def run():
    async with AsyncSessionLocal() as session:
        # Mock admin_ctx
        class MockCtx:
            user_id = 1
        
        result = await get_dashboard_summary(days=30, admin_ctx=MockCtx(), db=session)
        import json
        print(json.dumps(result, default=str, indent=2))

if __name__ == "__main__":
    asyncio.run(run())
