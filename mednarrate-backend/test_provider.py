import asyncio

from app.core.config import settings
from app.services.llm_client import DevGeminiProvider


async def main():
    print("Key in settings:", settings.GEMINI_API_KEY)
    provider = DevGeminiProvider()
    print("API Key property:", provider.api_key)
    print("Model name:", provider.model_name)
    try:
        res = await provider.generate("hello")
        print("Success:", res)
    except Exception as e:
        print("Failed:", repr(e))


asyncio.run(main())
