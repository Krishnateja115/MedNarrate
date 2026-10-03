import asyncio, json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        res = await session.execute(text("SELECT a.report_id, t.ui_labels FROM analysis_translations t JOIN report_analyses a ON t.report_analysis_id = a.id WHERE t.language = 'hi'"))
        for row in res:
            labels = row[1]
            if isinstance(labels, str):
                labels = json.loads(labels)
            print(f"label_not_provided: {labels.get('label_not_provided')}")
            print(f"label_cat_cbc: {labels.get('label_cat_cbc')}")
            print("---")

asyncio.run(main())
