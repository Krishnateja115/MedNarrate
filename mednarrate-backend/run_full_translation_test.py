import asyncio
import httpx
import json
import time

API_URL = "http://127.0.0.1:8000/api/v1"
FILE_PATH = r"C:\Users\manas\Downloads\MedNarrate-main\mednarrate-backend\tests\data\report3.pdf"

async def run_test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Upload
        with open(FILE_PATH, "rb") as f:
            files = {"file": ("report3.pdf", f, "application/pdf")}
            res = await client.post(f"{API_URL}/upload/", files=files)
        if res.status_code != 200:
            print("Upload failed:", res.status_code, res.text)
            return
        report_id = res.json()["report_id"]
        print(f"Uploaded Report ID: {report_id}")
        
        # 2. Wait for analysis
        print("Waiting for analysis...")
        while True:
            res = await client.get(f"{API_URL}/analysis/{report_id}")
            if res.status_code != 200:
                print("Analysis check failed:", res.status_code, res.text)
                return
            status = res.json()["status"]
            if status == "completed":
                break
            elif status == "failed":
                print("Analysis failed!")
                return
            await asyncio.sleep(2)
        
        baseline = res.json()
        print("English Baseline Analyzed.")
        
        # 3. Translate to each language
        languages = ["hi", "ta", "te", "kn", "ml", "bn", "mr"]
        results = {}
        
        for lang in languages:
            start_time = time.time()
            res = await client.get(f"{API_URL}/analysis/{report_id}/translate", params={"target_language": lang})
            latency = time.time() - start_time
            results[lang] = {
                "status_code": res.status_code,
                "data": res.json() if res.status_code == 200 else res.text,
                "latency": latency
            }
            print(f"Translated to {lang} in {latency:.2f}s (Status: {res.status_code})")
            
        # 4. Check cache for second time
        for lang in ["hi"]:
            start_time = time.time()
            res = await client.get(f"{API_URL}/analysis/{report_id}/translate", params={"target_language": lang})
            latency = time.time() - start_time
            print(f"Cache check {lang}: {latency:.2f}s")
            
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump({"baseline": baseline, "translations": results}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(run_test())
