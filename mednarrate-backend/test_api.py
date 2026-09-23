import asyncio
import logging
import httpx
import os

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)

os.environ["DATABASE_URL"] = "postgresql+asyncpg://fake:fake@localhost:5432/fake"
os.environ["JWT_SECRET"] = "test-secret-for-boot-check"
os.environ["CORS_ORIGINS"] = '["https://app.mednarrate.com"]'
os.environ["PRIMARY_LLM_PROVIDER"] = "gemini"
os.environ["GEMINI_MODEL"] = "gemini-3.8-flash"
os.environ["GEMINI_API_KEY"] = "dummy"
os.environ["ENVIRONMENT"] = "development"

from app.core.config import settings
from app.services.llm_client import DevGeminiProvider

async def test_llm():
    provider = DevGeminiProvider()
    print("Testing generate with model:", provider.model_name)
    try:
        res = await provider.generate("Say hello world in 2 words")
        print("Generate response:", res)
    except Exception as e:
        print("Error during generate:", e)

if __name__ == "__main__":
    asyncio.run(test_llm())
