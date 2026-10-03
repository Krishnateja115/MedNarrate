"""
Debug validation failure: call translate directly and catch the exact error.
"""
import asyncio
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./mednarrate.db")
os.environ.setdefault("JWT_SECRET", "mednarrate-dev-secret-key-super-secure-12345")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.prompts import TRANSLATION_PROMPT
from app.services.translation_validation import parse_translation, validate_translation

# A real patient_summary from the DB (report4, analysis id e49bb231)
# Shortened for testing
PATIENT_SUMMARY = """## 🩸 Your Blood Report: What It Means For You

### 1. What Your Report Says
Your report contains 18 laboratory test results. Most results are within the reference ranges provided. However, MCV (80.0 fL) was flagged as LOW, meaning this value falls below the expected lower limit.

### 2. Key Findings
Results outside reported reference ranges / flagged results:
• MCV: 80.0 — flagged as LOW (reference: 83.0 – 101.0 fL)

### 3. What These Terms Mean
- **MCV (Mean Corpuscular Volume):** A measure of the average size of your red blood cells. A LOW MCV may indicate smaller-than-normal red blood cells.

### 4. Information Not Provided
- No reference ranges were provided for: Absolute Neutrophils (2500.0 K/μL), Absolute Lymphocytes (2000.0 K/μL), Absolute Eosinophils (50.0 K/μL), Absolute Monocytes (450.0 K/μL).

### 5. What to Discuss With Your Doctor
- Discuss the MCV LOW 80.0 fL result with your doctor.
- Ask about follow-up tests if needed.

This explanation is derived directly from your uploaded document for informational purposes and does not replace advice from your doctor."""

ABNORMAL_FINDINGS = [
    {
        "test_name": "MCV",
        "value": 80.0,
        "unit": "fL",
        "ref_low": 83.0,
        "ref_high": 101.0,
        "flag": "low",
    }
]

MEDICATIONS = []

REQUIRED_LABEL_KEYS = [
    "section_report_at_a_glance", "section_important_results", "section_reported_medications",
    "section_what_to_discuss", "section_patient_report_info", "chip_lab_results",
    "chip_medications", "chip_noteworthy", "chip_report_type",
    "label_result", "label_reported_range", "label_status",
    "label_dose", "label_frequency", "label_timing",
    "label_high", "label_low", "label_normal", "label_critical", "label_not_classified",
    "label_not_provided", "label_no_lab_results", "label_no_medications",
    "label_confirm_followup", "label_review_test_parameters",
    "label_confirm_dosage_timing", "label_confirm_new_medications",
    "label_generated_by_gemini", "label_generated_by_local_fallback",
    "label_generated_by_ollama", "label_generated_offline",
    "label_patient_report_heading", "label_clinical_report_heading",
    "section_important_findings", "section_key_clinical_findings",
    "label_no_key_findings", "label_key_finding_expansion_patient",
    "label_key_finding_expansion_clinician", "label_source_latest_report",
    "label_report_extracted", "label_translate", "label_retranslate",
    "label_disclaimer_patient", "label_disclaimer_summary",
]


async def test_language(lang, lang_name):
    from app.services.llm_client import generate_translation

    prompt = TRANSLATION_PROMPT.format(
        target_language=lang_name,
        patient_summary="The patient has elevated blood pressure.",
        clinical_summary="Patient presents with hypertension. BP 150/95.",
        clinician_summary="Patient presents with hypertension. BP 150/95.",
        summary_metrics="BP: 150/95",
        abnormal_findings_json="[]",
        medications_json="[]",
        unique_parameters_json="[]",
        labels_json="{}"
    )
    
    print(f"\n=== Testing {lang_name} ({lang}) ===")
    try:
        llm_res = await generate_translation(prompt)
        raw = llm_res.get("content", "")
        print(f"  LLM returned {len(raw)} chars from provider={llm_res.get('provider')}")
        print(f"  First 300 chars: {repr(raw[:300])}")
        
        # Try to parse
        try:
            parsed = parse_translation(raw)
        except Exception as e:
            print(f"  ❌ PARSE ERROR: {type(e).__name__}: {e}")
            return False
        
        print(f"  Parsed OK. Keys: {list(parsed.keys())}")
        summary = parsed.get("patient_summary", "")
        print(f"  patient_summary len={len(summary)}, preview={repr(summary[:150])}")
        
        # Count native script chars
        from app.services.translation_validation import SCRIPT_RANGES
        low, high = SCRIPT_RANGES.get(lang, (0, 0))
        letters = [c for c in summary if c.isalpha()]
        native = sum(low <= ord(c) <= high for c in letters)
        ratio = native / max(len(letters), 1)
        print(f"  Native script: {native}/{len(letters)} letters = {ratio:.1%}")
        
        # Try to validate
        try:
            validate_translation(parsed, lang, PATIENT_SUMMARY, ABNORMAL_FINDINGS, MEDICATIONS, REQUIRED_LABEL_KEYS)
            print(f"  ✅ VALIDATION PASSED")
            return True
        except (ValueError, TypeError, KeyError) as e:
            print(f"  ❌ VALIDATION FAILED: {type(e).__name__}: {e}")
            
            # --- Deep field analysis ---
            from app.services.translation_validation import require_script, SCRIPT_RANGES
            
            # Check patient_summary
            try:
                require_script(parsed.get("patient_summary", ""), lang)
                print(f"  patient_summary: ✅ script OK")
            except ValueError as ve:
                print(f"  patient_summary: ❌ {ve}")
            
            # Check doctor_discussion_points
            discussion = parsed.get("doctor_discussion_points", [])
            for i, pt in enumerate(discussion):
                letts = [c for c in pt if c.isalpha()]
                nat = sum(low <= ord(c) <= high for c in letts) if letts else 0
                r = nat / max(len(letts), 1)
                try:
                    require_script(pt, lang)
                    print(f"  discussion[{i}]: ✅ ({nat}/{len(letts)} = {r:.0%}) {repr(pt[:60])}")
                except ValueError as ve:
                    print(f"  discussion[{i}]: ❌ ({nat}/{len(letts)} = {r:.0%}) {repr(pt[:80])} -> {ve}")
            
            # Check findings
            findings_out = parsed.get("abnormal_findings", [])
            for i, f in enumerate(findings_out):
                expl = f.get("translated_explanation", "")
                letts = [c for c in expl if c.isalpha()]
                nat = sum(low <= ord(c) <= high for c in letts) if letts else 0
                r = nat / max(len(letts), 1)
                try:
                    require_script(expl, lang)
                    print(f"  finding[{i}].explanation: ✅ ({nat}/{len(letts)} = {r:.0%}) {repr(expl[:60])}")
                except ValueError as ve:
                    print(f"  finding[{i}].explanation: ❌ ({nat}/{len(letts)} = {r:.0%}) {repr(expl[:80])} -> {ve}")
            
            # Check UI labels
            labels = parsed.get("ui_labels", {})
            for key in REQUIRED_LABEL_KEYS:
                val = labels.get(key, "")
                letts = [c for c in val if c.isalpha()]
                nat = sum(low <= ord(c) <= high for c in letts) if letts else 0
                r = nat / max(len(letts), 1)
                try:
                    require_script(val, lang)
                    pass  # OK
                except ValueError as ve:
                    print(f"  label['{key}']: ❌ ({nat}/{len(letts)} = {r:.0%}) {repr(val[:80])} -> {ve}")
            
            return False
    except Exception as e:
        print(f"  ❌ LLM ERROR: {type(e).__name__}: {e}")
        return False


async def main():
    print("=== Translation Validation Debug ===\n")
    
    langs = [("ta", "Tamil"), ("hi", "Hindi")]
    for lang, name in langs:
        await test_language(lang, name)


asyncio.run(main())
