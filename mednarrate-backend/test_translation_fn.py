import asyncio
import os
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.translation_planner import execute_translation_plan

async def main():
    try:
        res = await execute_translation_plan("Translate this to Hindi: Hello world, my name is MedNarrate.")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
