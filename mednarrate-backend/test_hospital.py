import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        res = await session.execute(text("SELECT hospital FROM reports WHERE id = '4b5da880-0a1a-44ad-b9c2-cb1f1d768dc1'"))
        print('Hospital:', res.scalar())

asyncio.run(main())
