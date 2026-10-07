import asyncio
import os
from app.services.llm_client import LLMClient
from app.core.config import settings

async def main():
    client = LLMClient()
    provider = client.get_provider('dev_gemini')
    print("Testing dev_gemini provider...")
    try:
        res = await provider.generate("hello", timeout=5.0)
        print("Success:", res)
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
