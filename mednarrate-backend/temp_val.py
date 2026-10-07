import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models.report_analysis import ReportAnalysis
from app.schemas.report import ReportAnalysisOut

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///./mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        stmt = select(ReportAnalysis)
        res = await db.execute(stmt)
        a = res.scalars().first()
        if a:
            try:
                out = ReportAnalysisOut.model_validate(a)
                print("SUCCESS")
            except Exception as e:
                print("VALIDATION ERROR:", e)
        else:
            print("No analysis found")

if __name__ == "__main__":
    asyncio.run(main())
