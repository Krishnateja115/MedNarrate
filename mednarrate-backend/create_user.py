import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        user = User(
            email="test@mednarrate.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print("Created user: test@mednarrate.com / password123")


if __name__ == "__main__":
    asyncio.run(main())
