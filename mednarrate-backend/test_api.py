import os
import sys
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API key found in .env")
        return
        
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    print(f"Testing model: {model_name}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    payload = {
        "contents": [{"parts": [{"text": "Hello, how are you?"}]}],
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers={"x-goog-api-key": api_key.strip()})
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
        else:
            print("Success!")

if __name__ == "__main__":
    asyncio.run(main())
