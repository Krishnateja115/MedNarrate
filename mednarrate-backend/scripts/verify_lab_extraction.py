"""
FIX 4 Verification Script — verify lab extraction filters work correctly.
Run from mednarrate-backend/: python3 scripts/verify_lab_extraction.py
"""
import glob
import fitz  # pymupdf
from app.services.lab_value_extractor import extract_lab_values

# Find any readable PDF in uploads/
pdf_paths = glob.glob("uploads/**/*.pdf", recursive=True) + glob.glob("tests/data/*.pdf")
readable_pdf = None
for p in pdf_paths:
    try:
        doc = fitz.open(p)
        if doc.page_count > 0:
            readable_pdf = p
            break
    except Exception:
        continue

assert readable_pdf, "No readable PDF found in uploads/ — locate one before proceeding."
print(f"Testing against: {readable_pdf}")

doc = fitz.open(readable_pdf)
full_text = "".join(page.get_text("text") + "\n" for page in doc)
print(f"\nExtracted text ({len(full_text)} chars):\n{full_text[:500]}\n")

# Also test against a synthetic string with the known junk patterns
synthetic = """BLOOD TEST REPORT
Patient: John Doe
Date: 2024-01-15
Hemoglobin: 13.5 g/dL (11.5 - 16.5) LOW
WBC: 8000 /uL (4000 - 11000) NORMAL
Platelets: 250 x10^3/uL (150 - 400) NORMAL
Glucose: 105 mg/dL (70 - 99) HIGH
Collection Date: 24/06/2023 08:49 PM
MD Pathology: 1/2
Report Date: 25/06/2023
PCT: 35 MPV 8.0-12.0
MCV: 85 fL (80 - 100) NORMAL
RBC: 4.5 mil/mm3 (3.5 - 5.5) NORMAL
"""

print("=== Testing against synthetic CBC text ===")
results = extract_lab_values(synthetic, "blood")
print(f"Extracted {len(results)} lab values:\n")
KNOWN_JUNK = {"collection date", "report date", "md pathology"}
junk_found = []
for r in results:
    print(r)
    if r["test_name"].strip().lower() in KNOWN_JUNK:
        junk_found.append(r["test_name"])

assert not junk_found, f"FAIL: junk entries still present: {junk_found}"
assert len(results) >= 5, f"FAIL: only {len(results)} lab values — regression! Expected >= 5 for a CBC."
print(f"\nPASS: {len(results)} real lab values extracted, zero known junk entries.")

# Also verify against the real PDF
print("\n=== Testing against real PDF ===")
real_results = extract_lab_values(full_text, "blood")
real_junk = [r["test_name"] for r in real_results if r["test_name"].strip().lower() in KNOWN_JUNK]
print(f"Real PDF: {len(real_results)} lab values, junk count: {len(real_junk)}")
if real_junk:
    print(f"FAIL: junk entries in real PDF: {real_junk}")
else:
    print(f"PASS: zero junk entries in real PDF.")
