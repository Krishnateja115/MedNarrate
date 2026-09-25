import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User

async def create_admin():
    await init_db()
    async with AsyncSessionLocal() as session:
        hashed_password = hash_password("admin123")
        admin = User(
            email="admin@mednarrate.com",
            hashed_password=hashed_password,
            full_name="System Admin",
            is_active=True,
            role="admin"
        )
        session.add(admin)
        await session.commit()
        print("Admin user created: admin@mednarrate.com / admin123")

if __name__ == "__main__":
    asyncio.run(create_admin())
