import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://127.0.0.1:8000/api/v1/reports/1ebb5ebd-2a86-4602-a939-14489e999123/analysis/translate', json={'language': 'hi'})
        print(r.status_code)
        print(r.json())

if __name__ == "__main__":
    asyncio.run(run())
