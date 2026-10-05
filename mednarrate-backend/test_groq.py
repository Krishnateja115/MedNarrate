import asyncio
import httpx
from app.core.config import settings

async def main():
    api_key = settings.GROQ_API_KEY
    if not api_key:
        print("NO KEY")
        return

    payload = {
        "model": settings.GROQ_GPT_TRANSLATION_MODEL,
        "messages": [{"role": "user", "content": "Translate 'Hello' to Hindi"}],
        "temperature": 0.2,
        "max_tokens": 4096
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        print("Status:", resp.status_code)
        if resp.status_code != 200:
            print(resp.text)
        else:
            print(resp.json())

asyncio.run(main())
