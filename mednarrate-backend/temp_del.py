import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///./mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        stmt = select(Report).where(Report.title=='report3')
        res = await db.execute(stmt)
        r = res.scalars().first()
        if r:
            await db.execute(delete(ReportAnalysis).where(ReportAnalysis.report_id==r.id))
            await db.commit()
            print('DELETED')
        else:
            print('REPORT NOT FOUND')

if __name__ == '__main__':
    asyncio.run(main())
