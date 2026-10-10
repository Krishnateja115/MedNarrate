import asyncio
from app.services.llm_client import DevGeminiProvider

async def main():
    provider = DevGeminiProvider()
    res = await provider.generate("Translate to Hindi: 'Hello world'. Reply with JSON format {'translation': '...'}")
    print(repr(res))

if __name__ == "__main__":
    asyncio.run(main())
