import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        # The model is LLMDiagnosticEvent. Let's check __tablename__ in llm_telemetry.py
        pass

asyncio.run(check())
