import asyncio, json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        res = await session.execute(text("SELECT a.structured_lab_values FROM report_analyses a WHERE a.report_id = '4b5da880-0a1a-44ad-b9c2-cb1f1d768dc1'"))
        for row in res:
            labs = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            for lab in labs:
                if "Not provided" in str(lab.get('unit')):
                    print("Found 'Not provided' in unit:", lab)
            print("Done checking labs.")

asyncio.run(main())
