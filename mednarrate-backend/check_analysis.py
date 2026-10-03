import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.report_analysis import ReportAnalysis

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        stmt = select(ReportAnalysis).limit(1)
        res = await session.execute(stmt)
        analyses = res.scalars().all()
        for a in analyses:
            print(f"ID: {a.id}")
            print(f"Structured: {a.structured_lab_values}")
            print("="*40)

asyncio.run(main())
