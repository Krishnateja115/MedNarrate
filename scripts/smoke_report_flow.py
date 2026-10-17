#!/usr/bin/env python3
"""End-to-end smoke test: signup -> login -> upload a sample lab report -> process -> poll -> print summary.

Usage:  python3 scripts/smoke_report_flow.py [BASE_URL]      (default http://localhost:8000)
Needs only the Python standard library. Creates a throwaway user.
"""
import json, sys, time, uuid, urllib.request, urllib.error, urllib.parse

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/") + "/api/v1"
TIMEOUT_S = int(sys.argv[2]) if len(sys.argv) > 2 else 180
PDF_PATH = __import__('os').path.expanduser(sys.argv[3]) if len(sys.argv) > 3 else None
if PDF_PATH and not __import__('os').path.isfile(PDF_PATH):
    sys.exit(f"PDF not found: {PDF_PATH}  (try scripts/sample_reports/report3.pdf)")   # optional: upload your own PDF instead of the sample

REPORT_LINES = [
    "Laboratory Report",
    "Patient Name: Test Patient    Age: 42    Sex: M",
    "Date: 2026-10-01",
    "Complete Blood Count",
    "Hemoglobin 10.2 g/dL (Ref 13.0 - 17.0) LOW",
    "WBC 11800 /uL (Ref 4000 - 11000) HIGH",
    "Platelets 245000 /uL (Ref 150000 - 410000)",
    "Lipid Profile",
    "Total Cholesterol 238 mg/dL (Ref < 200) HIGH",
    "LDL Cholesterol 160 mg/dL (Ref < 100) HIGH",
    "HDL Cholesterol 38 mg/dL (Ref > 40) LOW",
    "Fasting Glucose 108 mg/dL (Ref 70 - 99) HIGH",
]


def make_pdf(lines):
    """Minimal single-page text PDF (no third-party libs)."""
    def esc(s): return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = "BT /F1 12 Tf 50 780 Td 16 TL\n" + "\n".join(f"({esc(l)}) Tj T*" for l in lines) + "\nET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    x = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for o in offs: out += f"{o:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode()
    return out


def call(method, path, *, token=None, json_body=None, form=None, files=None):
    headers, data = {}, None
    if token: headers["Authorization"] = f"Bearer {token}"
    if json_body is not None:
        data = json.dumps(json_body).encode(); headers["Content-Type"] = "application/json"
    elif files is not None:
        b = uuid.uuid4().hex
        parts = b""
        for k, v in (form or {}).items():
            parts += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, (fn, content, ct) in files.items():
            parts += f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\nContent-Type: {ct}\r\n\r\n'.encode() + content + b"\r\n"
        data = parts + f"--{b}--\r\n".encode(); headers["Content-Type"] = f"multipart/form-data; boundary={b}"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode(); headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read(); return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try: return e.code, json.loads(body)
        except Exception: return e.code, body


def step(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" - {detail}" if detail else ""))
    if not ok: sys.exit(1)


email, pw = f"smoke_{uuid.uuid4().hex[:8]}@example.com", "Sm0ke-Test-Passw0rd!"
s, r = call("POST", "/auth/signup", json_body={"email": email, "password": pw, "full_name": "Smoke Tester"})
step("signup", s == 201, f"{s} {r if s != 201 else ''}")
s, r = call("POST", "/auth/login", form={"username": email, "password": pw})
step("login", s == 200 and "access_token" in (r or {}), f"{s}")
tok = r["access_token"]
s, r = call("POST", "/reports/upload", token=tok,
            form={"title": "Smoke CBC + Lipid", "report_date": "2026-10-01", "report_type": "blood"},
            files={"file": ("smoke_report.pdf", open(PDF_PATH, "rb").read() if PDF_PATH else make_pdf(REPORT_LINES), "application/pdf")})
step("upload", s == 201, f"{s} {r if s != 201 else ''}")
rid = r["id"]
s, r = call("POST", f"/reports/{rid}/process", token=tok)
step("start processing", s == 202, f"{s} {r if s != 202 else ''}")
t0, status = time.time(), "processing"
while time.time() - t0 < TIMEOUT_S:
    s, r = call("GET", f"/reports/{rid}/status", token=tok)
    status = (r or {}).get("processing_status") if isinstance(r, dict) else None
    if status in ("completed", "failed"): break
    time.sleep(3)
step("analysis finished", status == "completed", f"status={status} after {int(time.time()-t0)}s {r if status != 'completed' else ''}")
s, a = call("GET", f"/reports/{rid}/analysis", token=tok)
step("fetch analysis", s == 200, f"{s}")
labs = a.get("structured_lab_values") or []
print(f"\nLab values extracted: {len(labs)}")
for l in labs[:12]:
    print(f"  - {l.get('test_name')}: {l.get('value')} {l.get('unit')} [{l.get('flag')}] (ref {l.get('ref_low')}-{l.get('ref_high')})")
print("\nPATIENT SUMMARY:\n", (a.get("patient_summary") or "")[:3000])
print("\nCLINICIAN SUMMARY:\n", (a.get("clinician_summary") or "")[:3000])
step("summary present", bool(a.get("patient_summary") or a.get("clinician_summary")))
print("\nALL CHECKS PASSED")
