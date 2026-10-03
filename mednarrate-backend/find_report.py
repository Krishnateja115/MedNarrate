import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///./mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        res = await s.execute(text("SELECT id FROM reports WHERE extracted_text LIKE '%Neutrophil%' OR extracted_text LIKE '%Basophil%'"))
        rows = res.fetchall()
        print("Reports:", rows)

asyncio.run(main())
