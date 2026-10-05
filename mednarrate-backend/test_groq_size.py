import asyncio
import httpx
from app.core.config import settings

async def test_size(prompt_len):
    api_key = settings.GROQ_API_KEY
    payload = {
        "model": settings.GROQ_GPT_TRANSLATION_MODEL,
        "messages": [{"role": "user", "content": "A" * prompt_len}],
        "temperature": 0.2,
        "max_tokens": 4096
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        print(f"Len {prompt_len} -> Status: {resp.status_code}")
        if resp.status_code != 200:
            print("Error:", resp.text)

async def main():
    await test_size(1000)
    await test_size(5000)
    await test_size(10000)
    await test_size(12000)
    await test_size(15000)

asyncio.run(main())
