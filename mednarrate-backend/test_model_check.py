import asyncio
import httpx
import sys

# Force UTF-8 output for Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
API_KEY = os.getenv("GEMINI_API_KEY", "")
CANDIDATES = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

async def test_model(model):
    payload = {
        "contents": [{"parts": [{"text": "Translate 'Hemoglobin is Low' to Telugu. Return JSON: {\"text\": \"answer\"}"}]}],
        "generationConfig": {"maxOutputTokens": 100, "responseMimeType": "application/json"}
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            json=payload,
            headers={"x-goog-api-key": API_KEY}
        )
        status = resp.status_code
        data = resp.json()
        if status == 200:
            c = data.get("candidates", [])
            if c:
                t = "".join(p.get("text", "") for p in c[0].get("content", {}).get("parts", []) if not p.get("thought"))
                print(f"  OK [{model}] -> (len={len(t)}) {repr(t[:80])}")
                return True
            else:
                print(f"  OK but NO CANDIDATES [{model}]")
        else:
            err = data.get("error", {})
            print(f"  {status} [{model}] - {err.get('message','')[:90]}")
    return False

async def main():
    print("Testing models (UTF-8 safe)...")
    working = []
    for m in CANDIDATES:
        try:
            ok = await test_model(m)
            if ok:
                working.append(m)
        except Exception as e:
            print(f"  EXCEPTION [{m}]: {type(e).__name__}: {e}")
    print(f"\nWorking models: {working}")
    if working:
        print(f"BEST MODEL: {working[0]}")

asyncio.run(main())
