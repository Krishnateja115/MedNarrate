import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"x-goog-api-key": api_key.strip()})
        if resp.status_code == 200:
            data = resp.json()
            for model in data.get("models", []):
                print(f"{model['name']} - {model.get('supportedGenerationMethods', [])}")
        else:
            print(resp.text)

if __name__ == "__main__":
    asyncio.run(main())
