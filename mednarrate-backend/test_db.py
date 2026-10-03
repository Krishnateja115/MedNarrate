import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        # Get all Hindi translations and their report IDs
        res = await session.execute(text("SELECT a.report_id, t.ui_labels FROM analysis_translations t JOIN report_analyses a ON t.report_analysis_id = a.id WHERE t.language = 'hi'"))
        for row in res:
            labels = row[1]
            print(f"Report: {row[0]}")
            print(f"Has label_not_provided: {'label_not_provided' in labels}")
            print(f"Has label_cat_cbc: {'label_cat_cbc' in labels}")
            print("---")

asyncio.run(main())
