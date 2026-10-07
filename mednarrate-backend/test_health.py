import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.get('http://127.0.0.1:8000/api/v1/health')
        print(r.json())

asyncio.run(run())
