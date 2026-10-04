import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.services.llm_client import get_resolved_ai_config

async def main():
    config = await get_resolved_ai_config()
    print("Resolved Config:")
    for k, v in config.items():
        if "key" in k and v:
            print(f"  {k}: <length {len(v)}>")
        else:
            print(f"  {k}: {v}")
            
    print("\nSettings from core config:")
    print(f"  GEMINI_MODEL: {getattr(settings, 'GEMINI_MODEL', None)}")
    key = getattr(settings, 'GEMINI_API_KEY', None)
    print(f"  GEMINI_API_KEY: <length {len(key) if key else 0}>")

if __name__ == "__main__":
    asyncio.run(main())
