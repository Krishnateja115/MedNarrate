import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # First login to get token using form data
        login_resp = await client.post("http://localhost:8000/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "password123"
        })
        if login_resp.status_code != 200:
            print("Login failed", login_resp.text)
            return
            
        token = login_resp.json()["access_token"]
        print("Logged in, token length:", len(token))
        
        headers = {"Authorization": f"Bearer {token}"}
        
        print("Sending translation request...")
        translate_resp = await client.post(
            "http://localhost:8000/api/v1/reports/1ebb5ebd2a864602a93914489e999123/analysis/translate",
            json={"language": "hi"},
            headers=headers,
            timeout=120.0
        )
        
        print("Status:", translate_resp.status_code)
        if translate_resp.status_code == 200:
            data = translate_resp.json()
            print("Translation SUCCESS!")
            print("Summary:", data.get("patient_summary")[:100] if data.get("patient_summary") else "None")
            print("Abnormal Findings Count:", len(data.get("findings_json", [])))
            print("Medications Count:", len(data.get("medications_json", [])))
            print("UI Labels Count:", len(data.get("ui_labels", {})))
        else:
            print("Error response:", translate_resp.text)

asyncio.run(main())
