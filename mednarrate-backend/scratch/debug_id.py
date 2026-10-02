import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.database import Base

async def test():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        user = User(email="test@test.com", hashed_password="1", full_name="A", role="patient")
        db.add(user)
        print("Type before commit:", type(user.id))
        await db.commit()
        print("Type after commit:", type(user.id))

asyncio.run(test())
