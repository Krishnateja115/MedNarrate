import asyncio
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///./mednarrate.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        stmt = select(Report).where(Report.title == "report3")
        res = await db.execute(stmt)
        report = res.scalars().first()
        if not report:
            print("report3 not found")
            return
        
        print("report3 ID:", report.id)
        stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
        res_analysis = await db.execute(stmt_analysis)
        analysis = res_analysis.scalars().first()
        if not analysis:
            print("No analysis found")
            return
        
        print("structured_lab_values:", type(analysis.structured_lab_values))
        if isinstance(analysis.structured_lab_values, str):
            print("IT IS A STRING! First 100 chars:", analysis.structured_lab_values[:100])
        else:
            print("Length:", len(analysis.structured_lab_values))
            if analysis.structured_lab_values:
                print("First element type:", type(analysis.structured_lab_values[0]))
                
if __name__ == "__main__":
    asyncio.run(main())
