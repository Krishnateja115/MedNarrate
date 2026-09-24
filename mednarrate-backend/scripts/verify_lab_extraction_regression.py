"""
Regression test: extract_lab_values() must correctly parse a real multi-line-per-row
PDF table layout (the common case), not just single-line 'Name: Value Unit (range)' text.
"""

import glob
import os
import sys

import fitz

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from app.services.lab_value_extractor import extract_lab_values

SAMPLE_PATTERNS = ["tests/data/report3.pdf"]
pdf_paths = []
for pattern in SAMPLE_PATTERNS:
    pdf_paths.extend(glob.glob(pattern, recursive=True))

for pdf_path in pdf_paths:
    try:
        doc = fitz.open(pdf_path)
        full_text = "".join(page.get_text("text") + "\n" for page in doc)
    except Exception:
        continue

    if "haemoglobin" not in full_text.lower() and "hemoglobin" not in full_text.lower():
        continue  # Not the right demo report

    print(f"Testing against: {pdf_path}")
    results = extract_lab_values(full_text, report_type="blood")
    print(f"\nExtracted {len(results)} lab values:\n")
    for r in results:
        print(r)

    # Known real lab tests that MUST be present for this specific CBC report.
    expected_present = {
        "haemoglobin",
        "hemoglobin",
        "total leucocyte count",
        "neutrophils",
        "lymphocytes",
        "eosinophils",
        "monocytes",
        "basophils",
        "rbc count",
        "mcv",
        "mch",
        "mchc",
        "hct",
        "rdw-cv",
        "rdw-sd",
        "platelet count",
        "platelets",
        "mpv",
    }
    found_names = {r["original_name"].strip().lower() for r in results}
    matched = {
        name
        for name in expected_present
        if any(name in fn or fn in name for fn in found_names)
    }
    missing = expected_present - matched

    # Known junk that must NOT reappear.
    junk_names = {"pn", "re", "collection date", "report date", "md pathology"}
    junk_found = found_names & junk_names

    print(f"\nMatched {len(matched)}/{len(expected_present)} expected real lab tests.")
    if missing:
        print(f"MISSING expected tests: {missing}")
    if junk_found:
        print(f"JUNK entries present: {junk_found}")

    assert (
        len(results) >= 18
    ), f"FAIL: only {len(results)} lab values extracted — expected ~20+."
    assert (
        len(missing) <= 2
    ), f"FAIL: too many expected real lab tests missing: {missing}"
    assert not junk_found, f"FAIL: junk entries reintroduced: {junk_found}"

    print("\nPASS: real multi-line lab table correctly extracted with no junk.")
    sys.exit(0)

print("FAIL: No valid sample report found.")
sys.exit(1)
