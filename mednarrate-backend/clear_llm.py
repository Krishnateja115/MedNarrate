import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def clear():
    async with AsyncSessionLocal() as session:
        await session.execute(text('DELETE FROM llm_diagnostic_events;'))
        await session.commit()

asyncio.run(clear())
