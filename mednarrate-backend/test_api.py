import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # FastAPI OAuth2PasswordRequestForm expects form data, username and password
        resp = await client.post("http://127.0.0.1:8000/api/v1/auth/login", data={"username": "test@mednarrate.com", "password": "password123"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return
        token = resp.json()["access_token"]
        
        # Now request translation
        resp = await client.post(
            "http://127.0.0.1:8000/api/v1/reports/b3ff5701-ec48-4f1a-8ee9-5f937f249f89/analysis/translate",
            json={"language": "ta"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=120.0
        )
        print("Status:", resp.status_code)
        print("Body:", resp.text)

asyncio.run(main())
