import sys
import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

EMAIL = "test@mednarrate.com"
PASSWORD = "password123"
REPORT_ID = "159351a2adc546cdb7facda28a7810a8"

print("=" * 70)
print("PHASE 1: LOGIN")
print("=" * 70)

login_data = {
    "username": EMAIL,
    "password": PASSWORD
}
try:
    r = httpx.post(f"{BASE_URL}/auth/login", data=login_data, timeout=10)
    print(f"Login HTTP status: {r.status_code}")
    if r.status_code != 200:
        print(f"Login FAILED: {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print(f"Login SUCCESS, token length={len(token)}")
    headers = {"Authorization": f"Bearer {token}"}
except Exception as e:
    print(f"Login ERROR: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("PHASE 2: TRANSLATE TO TELUGU (te)")
print("=" * 70)
print(f"Report ID: {REPORT_ID}")
print(f"Expected findings: MCV=80 LOW, MCHC=37.5 HIGH, PDW=9 NOT_CLASSIFIED")
print()

translate_body = {"language": "te"}
try:
    r = httpx.post(
        f"{BASE_URL}/reports/{REPORT_ID}/analysis/translate",
        headers=headers,
        json=translate_body,
        timeout=120
    )
    print(f"HTTP status: {r.status_code}")
    print()

    if r.status_code == 200:
        data = r.json()
        print(f"language: {data.get('language')}")
        print(f"schema_version: {data.get('schema_version')}")
        print(f"cached: {data.get('cached')}")
        print(f"patient_summary length: {len(data.get('patient_summary',''))}")
        print(f"findings_json count: {len(data.get('findings_json',[]) or [])}")
        print(f"medications_json count: {len(data.get('medications_json',[]) or [])}")
        print(f"doctor_discussion_points count: {len(data.get('doctor_discussion_points',[]) or [])}")
        print(f"ui_labels count: {len(data.get('ui_labels',{}) or {})}")
        print()

        print("=" * 70)
        print("PATIENT SUMMARY (first 500 chars):")
        print("=" * 70)
        ps = data.get('patient_summary', '')
        print(ps[:500])
        if len(ps) > 500:
            print(f"... [truncated, total {len(ps)} chars]")
        print()

        print("=" * 70)
        print("FINDINGS JSON (first 3):")
        print("=" * 70)
        findings = data.get('findings_json', []) or []
        for i, f in enumerate(findings[:3]):
            print(f"  [{i}] {json.dumps(f, ensure_ascii=False, indent=4)[:300]}")
        print()

        print("=" * 70)
        print("DOCTOR DISCUSSION POINTS:")
        print("=" * 70)
        dpoints = data.get('doctor_discussion_points', []) or []
        for i, dp in enumerate(dpoints):
            print(f"  [{i}] {dp}")
        print()
        has_english_dp = any(
            "Discuss the" in str(dp) or
            "healthcare provider" in str(dp) or
            "your healthcare" in str(dp)
            for dp in dpoints
        )
        print(f"MIXED LANGUAGE (English detected in discussion): {has_english_dp}")
        print()

        print("=" * 70)
        print("UI LABELS - sample keys:")
        print("=" * 70)
        uilabels = data.get('ui_labels', {}) or {}
        sample_keys = [
            "section_report_at_a_glance",
            "section_what_to_discuss",
            "label_translate",
            "label_retranslate",
            "label_high",
            "label_low",
            "label_not_classified",
            "label_patient_report_heading",
        ]
        for k in sample_keys:
            v = uilabels.get(k, "<MISSING>")
            short_v = (v[:80] + "...") if len(v) > 80 else v
            print(f"  {k}: {short_v}")
        print()
        missing_labels = [k for k in [
            "section_report_at_a_glance", "section_important_results",
            "section_reported_medications", "section_what_to_discuss",
            "label_translate", "label_retranslate",
            "label_high", "label_low", "label_normal",
        ] if not uilabels.get(k, "").strip()]
        print(f"Missing required UI labels sample: {missing_labels[:10]}")
        print()

        print("=" * 70)
        print("MEDICATIONS JSON:")
        print("=" * 70)
        meds = data.get('medications_json', []) or []
        for i, m in enumerate(meds[:3]):
            print(f"  [{i}] {json.dumps(m, ensure_ascii=False)}")
        if not meds:
            print("  No medications in this report.")
        print()

        print("=" * 70)
        print("TRANSLATION API TEST: PASSED (HTTP 200)")
        print("=" * 70)
    else:
        print(f"RESPONSE BODY ({r.status_code}):")
        try:
            body = r.json()
            print(json.dumps(body, indent=2, ensure_ascii=False)[:3000])
        except Exception:
            print(r.text[:3000])
        print()
        print("=" * 70)
        print("TRANSLATION API TEST: FAILED")
        print("=" * 70)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERROR: {e}")
    print("=" * 70)
    print("TRANSLATION API TEST: ERROR")
    print("=" * 70)
