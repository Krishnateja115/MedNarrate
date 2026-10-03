import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///./mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        res = await s.execute(text("SELECT email FROM users JOIN reports ON users.id = reports.user_id WHERE reports.id='0d8a6b9176e1473da7faee4a74fbba3a'"))
        print(res.fetchall())

asyncio.run(main())
