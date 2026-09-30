import asyncio
import app.core.database
from app.models.feature_flag import FeatureFlag
from sqlalchemy.future import select

async def run():
    async with app.core.database.AsyncSessionLocal() as db:
        res = await db.execute(select(FeatureFlag))
        flags = res.scalars().all()
        for f in flags:
            print(f.name)

asyncio.run(run())
