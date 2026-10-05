import asyncio
import httpx
from app.core.config import settings
import json

async def main():
    api_key = settings.GROQ_API_KEY
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "Hello"}],
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
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print("Error:", resp.text)

asyncio.run(main())
