import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
async def main():
    engine = create_async_engine('sqlite+aiosqlite:///mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        res = await session.execute(text("SELECT id FROM reports WHERE id='1ebb5ebd-2a86-4602-a939-14489e999123'"))
        print('Report:', res.fetchall())
        res2 = await session.execute(text("SELECT id FROM report_analyses WHERE report_id='1ebb5ebd-2a86-4602-a939-14489e999123'"))
        print('Analysis:', res2.fetchall())
asyncio.run(main())
