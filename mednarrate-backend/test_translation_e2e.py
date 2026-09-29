"""
E2E Translation test using test@mednarrate.com (password123) which has existing analyzed reports.
"""
import asyncio
import sys
import httpx

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000/api/v1"
EMAIL = "test@mednarrate.com"
PASSWORD = "password123"


async def login():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": EMAIL, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if resp.status_code == 200:
            print(f"Logged in as {EMAIL}")
            return resp.json().get("access_token")
        print(f"Login failed: {resp.status_code} {resp.text[:200]}")
        return None


async def test_translation(token, report_id, lang, lang_name):
    print(f"\n  [{lang_name} ({lang})] Requesting...", flush=True)
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{BASE_URL}/reports/{report_id}/analysis/translate",
            json={"language": lang},
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get("patient_summary", "")
            ui_labels = data.get("ui_labels", {})
            cached = data.get("cached", False)
            discussion = data.get("doctor_discussion_points", [])
            has_native = any(ord(c) > 127 for c in summary)

            print(f"  [{lang_name}] ✅ OK (cached={cached}, native_script={has_native})")
            print(f"     summary_len={len(summary)}")
            print(f"     summary[:220]= {repr(summary[:220])}")
            glance = ui_labels.get("section_report_at_a_glance", "")
            print(f"     'Report at a Glance'= {repr(glance[:80])}")
            if discussion:
                print(f"     discussion[0]= {repr(discussion[0][:120])}")
            return True
        else:
            print(f"  [{lang_name}] ❌ FAILED ({resp.status_code})")
            try:
                print(f"     {resp.json().get('detail', resp.text[:400])}")
            except Exception:
                print(f"     {resp.text[:400]}")
            return False


async def main():
    print("=== MedNarrate Translation E2E Test ===\n")

    token = await login()
    if not token:
        return

    # Get completed reports
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BASE_URL}/reports", headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        reports = data if isinstance(data, list) else data.get("reports", data.get("items", []))
        completed = [r for r in reports if r.get("processing_status") == "completed"]

    print(f"Found {len(completed)} completed reports")
    if not completed:
        print("No completed reports found. Please upload and analyze a report first.")
        return

    # Pick the report with the longest summary (most content to translate)
    report_id = completed[0]["id"]
    print(f"Using: {report_id} — '{completed[0].get('title', 'unknown')}'")

    languages = [("te", "Telugu"), ("ta", "Tamil"), ("kn", "Kannada"), ("ml", "Malayalam"), ("hi", "Hindi")]
    results = {}
    for lang, name in languages:
        results[lang] = await test_translation(token, report_id, lang, name)

    print("\n\n=== FINAL RESULTS ===")
    for lang, name in languages:
        print(f"  {name:12} ({lang}): {'✅ PASS' if results.get(lang) else '❌ FAIL'}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nScore: {passed}/{total}")
    print("✅ ALL PASS" if passed == total else f"❌ {total - passed} FAILED")


asyncio.run(main())
