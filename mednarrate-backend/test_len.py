import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
async def main():
    engine = create_async_engine('sqlite+aiosqlite:///mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        res = await session.execute(text("SELECT patient_summary, clinician_summary FROM report_analyses WHERE report_id='1ebb5ebd2a864602a93914489e999123'"))
        row = res.fetchone()
        print('Patient summary length:', len(row[0]) if row[0] else 0)
        print('Clinician summary length:', len(row[1]) if row[1] else 0)
asyncio.run(main())
