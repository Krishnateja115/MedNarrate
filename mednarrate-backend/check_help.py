import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT count(*) FROM help_articles;"))
        count = res.scalar()
        print(f"Help articles count: {count}")

asyncio.run(check())
