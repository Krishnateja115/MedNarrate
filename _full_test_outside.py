"""Full 7-language translate E2E after gemini-2.0-flash switch.

Run from PARENT dir (so mednarrate-backend uvicorn file watcher doesn't reload).
"""
import asyncio, json, os, sys, time as _t, uuid as _uuid, httpx
from datetime import date as _date

BACKEND_DIR = r"c:\Users\manas\Downloads\MedNarrate-main\mednarrate-backend"
os.chdir(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

BASE = "http://127.0.0.1:8000/api/v1"


async def make_user_report_and_analysis(suffix: str, extra_values=None, abnormal_extra=None):
    from app.core.database import AsyncSessionLocal
    from app.models.report import Report, FileType, ReportType, ProcessingStatus
    from app.models.report_analysis import ReportAnalysis
    from app.models.user import User
    from app.core.security import hash_password

    email = f"t{suffix}{_uuid.uuid4().hex[:4]}@example.com"
    password = "StrongP@ssword1"
    rid = _uuid.uuid4()
    aid = _uuid.uuid4()
    async with AsyncSessionLocal() as s:
        u = User(email=email, full_name=f"Tester {suffix}", role="patient", preferred_language="en")
        u.hashed_password = hash_password(password)
        s.add(u)
        await s.flush()
        s.add(Report(
            id=rid, user_id=u.id, title=f"Blood Report {suffix}",
            file_name="x.pdf", file_path="x.pdf", file_type=FileType.pdf,
            report_type=ReportType.blood, report_date=_date.today(),
            processing_status=ProcessingStatus.completed,
            extracted_text="CBC: HGB 12 g/dL, MCV 80 fL, MCHC 37.5 g/dL, PDW 9%, WBC 8.5 k/uL",
        ))
        sv = extra_values or [
            {"test_name": "Hemoglobin", "original_name": "HGB", "value": 12.0, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "flag": "low", "category": "LabResult"},
            {"test_name": "MCV", "original_name": "MCV", "value": 80, "unit": "fL", "ref_low": 82, "ref_high": 98, "flag": "low", "category": "LabResult"},
            {"test_name": "MCHC", "original_name": "MCHC", "value": 37.5, "unit": "g/dL", "ref_low": 32.0, "ref_high": 36.0, "flag": "high", "category": "LabResult"},
            {"test_name": "PDW", "original_name": "PDW", "value": 9, "unit": "%", "ref_low": 9.0, "ref_high": 17.0, "flag": "not_classified", "category": "LabResult"},
            {"test_name": "WBC", "original_name": "WBC", "value": 8.5, "unit": "x10^3/uL", "ref_low": 4.0, "ref_high": 11.0, "flag": "normal", "category": "LabResult"},
        ]
        af = abnormal_extra or [
            {"test_name": "Hemoglobin", "original_name": "HGB", "value": 12.0, "unit": "g/dL", "flag": "low", "explanation": "Hemoglobin is low (12.0 g/dL vs 13-17)."},
            {"test_name": "MCV", "original_name": "MCV", "value": 80, "unit": "fL", "flag": "low", "explanation": "MCV low microcytic 80 fL vs 82-98."},
            {"test_name": "MCHC", "original_name": "MCHC", "value": 37.5, "unit": "g/dL", "flag": "high", "explanation": "MCHC high at 37.5 g/dL vs 32-36."},
            {"test_name": "PDW", "original_name": "PDW", "value": 9, "unit": "%", "flag": "not_classified", "explanation": "PDW exactly on lower limit, can't classify."},
        ]
        s.add(ReportAnalysis(
            id=aid, report_id=rid,
            structured_lab_values=sv, entities=[],
            abnormal_findings=af,
            evidence_sources=[],
            model_versions={"v": 1},
            patient_summary=f"### 1. What Your Report Says\n{suffix}: CBC with 5 values, 3 out-of-range, 1 borderline.\n### 2. Key Findings\n- Hemoglobin:12.0 LOW.\n- MCV:80 LOW.\n- MCHC:37.5 HIGH.\n- PDW:9 NOT_CLASSIFIED.\n### 3. Terms\nHemoglobin=O2 protein; MCV=mean red cell volume; MCHC=Hb conc; PDW=platelet dist.\n### 4. Not Provided\nIron/B12/folate, symptoms, meds.\n### 5. What to Discuss\n- Low Hb + low MCV pattern with physician.\n- High MCHC + repeat test need.\n- Borderline PDW in platelet context.\n\nFor informational purposes; does not replace doctor.",
            clinician_summary=f"{suffix}: Microcytic/hypochromic; low Hb/MCV high MCHC borderline PDW. IDA vs artifact; iron studies + repeat CBC recommended.",
        ))
        await s.commit()
    return email, password, str(rid), str(aid)


ENGLISH_MARKER_WORDS = {"Discuss", "healthcare", "provider", "Review your", "Confirm dosage", "Confirm new", "with your doctor"}


def mixed_lang_audit(lang, ddp):
    if lang == "en" or not isinstance(ddp, list):
        return []
    bad = []
    for i, p in enumerate(ddp, 1):
        flags = [w for w in ENGLISH_MARKER_WORDS if w.lower() in p.lower()]
        if flags:
            bad.append((i, p, flags))
    return bad


async def call_translate(client, auth, rid, lang, name, expected_vals_note=None):
    t0 = _t.time()
    try:
        r = await client.post(f"{BASE}/reports/{rid}/analysis/translate", json={"language": lang}, headers=auth, timeout=420.0)
    except Exception as e:
        dt = int((_t.time() - t0) * 1000)
        print(f"\n  {name} ({lang})  TRANSPORT ERROR in {dt}ms: {type(e).__name__}: {e}")
        return None, None
    dt = int((_t.time() - t0) * 1000)
    ctype = r.headers.get("content-type", "")
    try:
        body = r.json() if "application/json" in ctype else {"text": r.text[:2000]}
    except Exception as e:
        body = {"err": str(e), "raw": r.text[:2000]}
    note = ("  " + expected_vals_note) if expected_vals_note else ""
    print(f"\n{'='*70}\n  {name} ({lang})  → HTTP {r.status_code} in {dt} ms{note}\n{'='*70}")
    if r.status_code == 200:
        d = body.get("data") or body
        print("  top keys:", sorted(list(d.keys())))
        for k in ("language", "schema_version", "cached"):
            print(f"  - {k}: {d.get(k)!r}")
        ps = d.get("patient_summary") or ""
        print(f"  - patient_summary len={len(ps)}  preview={ps[:140]!r}")
        fj = d.get("findings_json") or []
        print(f"  - findings_json type={type(fj).__name__} len={len(fj) if hasattr(fj,'__len__') else None}")
        mj = d.get("medications_json") or []
        print(f"  - medications_json type={type(mj).__name__} len={len(mj) if hasattr(mj,'__len__') else None}")
        uil = d.get("ui_labels") or {}
        print(f"  - ui_labels keys count={len(uil)}  head={list(uil.keys())[:15]}")
        ddp = d.get("doctor_discussion_points") or []
        print(f"  - doctor_discussion_points count={len(ddp)}:")
        for i, p in enumerate(ddp, 1):
            print(f"    [{i}] {p}")
        bad = mixed_lang_audit(lang, ddp)
        if bad:
            print(f"  ⚠️ MIXED LANGUAGE DETECTED: {bad!r}")
        else:
            print(f"  ✔ mixed-language audit clean")
    else:
        print("  body:", json.dumps(body, indent=2, ensure_ascii=False)[:2500])
    return r.status_code, body


async def main():
    print("== Setting up two isolated reports for multi-report isolation test ==")
    u1, p1, r1, a1 = await make_user_report_and_analysis("A")
    u2, p2, r2, a2 = await make_user_report_and_analysis("B", extra_values=[
            {"test_name": "TSH", "original_name": "TSH", "value": 5.2, "unit": "mIU/L", "ref_low": 0.4, "ref_high": 4.0, "flag": "high", "category": "LabResult"},
            {"test_name": "Free T4", "original_name": "FT4", "value": 0.6, "unit": "ng/dL", "ref_low": 0.8, "ref_high": 1.8, "flag": "low", "category": "LabResult"},
            {"test_name": "HbA1c", "original_name": "A1C", "value": 6.5, "unit": "%", "ref_low": 4.0, "ref_high": 5.6, "flag": "high", "category": "LabResult"},
    ], abnormal_extra=[
        {"test_name": "TSH", "original_name": "TSH", "value": 5.2, "unit": "mIU/L", "flag": "high", "explanation": "TSH elevated 5.2 mIU/L vs 0.4-4.0."},
        {"test_name": "Free T4", "original_name": "FT4", "value": 0.6, "unit": "ng/dL", "flag": "low", "explanation": "Free T4 low at 0.6 ng/dL vs 0.8-1.8."},
        {"test_name": "HbA1c", "original_name": "A1C", "value": 6.5, "unit": "%", "flag": "high", "explanation": "HbA1c 6.5% exceeds target 4-5.6%."},
    ])
    print(f"  Report A id={r1} user={u1}  (MCV/MCHC/PDW case)")
    print(f"  Report B id={r2} user={u2}  (TSH/FreeT4/HbA1c case)")
    async with httpx.AsyncClient(timeout=600.0) as client:
        r = await client.post(f"{BASE}/auth/login", data={"username": u1, "password": p1})
        assert r.status_code == 200, r.text
        auth1 = {"Authorization": f"Bearer {r.json()['access_token']}"}
        r = await client.post(f"{BASE}/auth/login", data={"username": u2, "password": p2})
        assert r.status_code == 200, r.text
        auth2 = {"Authorization": f"Bearer {r.json()['access_token']}"}

        ##########################################
        # Part 1: Report A — EN then te then cache
        ##########################################
        await call_translate(client, auth1, r1, "en", "REPORT-A-EN")
        await call_translate(client, auth1, r1, "te", "REPORT-A-TELUGU-1",
                             expected_vals_note="MCV=80 LOW MCHC=37.5 HIGH PDW=9 NOT_CLASSIFIED; Telugu expected; NUMERIC VALUES MUST BE PRESERVED UNCHANGED")
        await call_translate(client, auth1, r1, "te", "REPORT-A-TELUGU-CACHE-EXPECTED")

        ##########################################
        # Part 2: Report A — 5 remaining languages
        ##########################################
        for lang, name in [("hi","REPORT-A-HINDI"), ("ta","REPORT-A-TAMIL"), ("kn","REPORT-A-KANNADA"), ("ml","REPORT-A-MALAYALAM"), ("mr","REPORT-A-MARATHI")]:
            await call_translate(client, auth1, r1, lang, name)
        await call_translate(client, auth1, r1, "en", "REPORT-A-EN-RECHECK")

        ##########################################
        # Part 3: Report A — Language switching te → hi → ta → en
        ##########################################
        print("\n" + "#"*70 + "\n  REPORT-A: LANGUAGE SWITCHING te -> hi -> ta -> en\n" + "#"*70)
        await call_translate(client, auth1, r1, "hi", "SWITCH-HI")
        await call_translate(client, auth1, r1, "ta", "SWITCH-TA")
        await call_translate(client, auth1, r1, "en", "SWITCH-EN")

        ##########################################
        # Part 4: Two-report isolation
        ##########################################
        print("\n" + "#"*70 + "\n  TWO-REPORT ISOLATION  (A Telugu; B Hindi)\n" + "#"*70)
        await call_translate(client, auth1, r1, "te", "A→TELUGU",
                             expected_vals_note="Expected: MCV=80 MCHC=37.5 PDW=9 Telugu content")
        await call_translate(client, auth2, r2, "hi", "B→HINDI",
                             expected_vals_note="Expected: TSH=5.2 FT4=0.6 HbA1c=6.5 Hindi content — NO MCV/MCHC LEAKAGE!")
        print("\n  TWO-REPORT ISOLATION (A→Tamil B→Marathi)")
        await call_translate(client, auth1, r1, "ta", "A→TAMIL")
        await call_translate(client, auth2, r2, "mr", "B→MARATHI")
        await call_translate(client, auth1, r1, "ta", "A→TAMIL CACHE")
        await call_translate(client, auth2, r2, "mr", "B→MARATHI CACHE")

        ##########################################
        # Final summary
        ##########################################
        print("\n" + "="*70)
        print("  ALL PHASES COMPLETED.")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
