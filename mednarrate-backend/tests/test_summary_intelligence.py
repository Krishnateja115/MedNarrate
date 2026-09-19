import pytest
import asyncio
import json
from app.services.llm_client import FallbackAIProvider
from app.services.lab_value_extractor import extract_lab_values
from app.services.prompts import PATIENT_PROMPT, CLINICIAN_PROMPT, ROLE_INSTRUCTIONS

# Generic boilerplate phrases to guard against
GENERIC_BOILERPLATE_PHRASES = [
    "your medical report has been uploaded and analyzed successfully",
    "all extracted lab values are saved in your profile for health trend tracking",
    "key lab values have been extracted from your document and stored for reference",
    "review your results with your healthcare provider",
    "compare these results with your previous health trends"
]

def assert_no_generic_boilerplate_as_primary_content(text: str):
    """Ensures primary summary content is not comprised of generic boilerplate phrases."""
    text_lower = text.lower()
    for phrase in GENERIC_BOILERPLATE_PHRASES:
        assert phrase not in text_lower, f"Generic boilerplate phrase detected in summary: '{phrase}'"

def build_patient_summary_prompt(report_type: str, structured_labs: list, rag_context: str = "", extracted_text: str = "") -> str:
    role_instruction = ROLE_INSTRUCTIONS.get("patient", "")
    return PATIENT_PROMPT.format(
        report_type=report_type,
        user_role="patient",
        role_specific_instruction=role_instruction,
        structured_values_json=json.dumps(structured_labs),
        extracted_text=extracted_text,
        rag_context=rag_context,
        examples=""
    )

@pytest.mark.asyncio
async def test_individualized_summary_different_reports():
    """Verify Report A and Report B produce different, report-specific summaries containing their respective facts."""
    provider = FallbackAIProvider()

    report_a_labs = [
        {"test_name": "MCV", "original_name": "MCV", "value": 80.0, "unit": "fL", "ref_low": 81.0, "ref_high": 101.0, "flag": "low"},
        {"test_name": "Hemoglobin", "original_name": "Hemoglobin", "value": 14.2, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "flag": "normal"}
    ]

    report_b_labs = [
        {"test_name": "HbA1c", "original_name": "HbA1c", "value": 6.8, "unit": "%", "ref_low": 4.0, "ref_high": 5.6, "flag": "high"},
        {"test_name": "Fasting Glucose", "original_name": "Fasting Glucose", "value": 126.0, "unit": "mg/dL", "ref_low": 70.0, "ref_high": 99.0, "flag": "high"}
    ]

    prompt_a = build_patient_summary_prompt("Blood Test", report_a_labs)
    prompt_b = build_patient_summary_prompt("Blood Test", report_b_labs)

    res_a = await provider.generate(prompt_a)
    res_b = await provider.generate(prompt_b)

    summary_a = res_a["content"]
    summary_b = res_b["content"]

    # 1. Summaries must be strictly different
    assert summary_a != summary_b

    # 2. Report A summary must contain A facts (MCV, 80) and NOT B facts (HbA1c, 126)
    assert "MCV" in summary_a or "80" in summary_a
    assert "HbA1c" not in summary_a
    assert "126" not in summary_a

    # 3. Report B summary must contain B facts (HbA1c, 126) and NOT A facts (MCV)
    assert "HbA1c" in summary_b or "126" in summary_b
    assert "MCV" not in summary_b

    # 4. Neither should contain pure generic boilerplate
    assert_no_generic_boilerplate_as_primary_content(summary_a)
    assert_no_generic_boilerplate_as_primary_content(summary_b)

@pytest.mark.asyncio
async def test_cross_report_contamination_protection():
    """Verify Report B summary never leaks Report A patient information or laboratory values."""
    provider = FallbackAIProvider()

    report_a_labs = [{"test_name": "Cholesterol", "original_name": "Cholesterol", "value": 240.0, "unit": "mg/dL", "ref_low": 0.0, "ref_high": 200.0, "flag": "high"}]
    report_b_labs = [{"test_name": "Platelets", "original_name": "Platelets", "value": 250.0, "unit": "10^3/uL", "ref_low": 150.0, "ref_high": 450.0, "flag": "normal"}]

    prompt_b = build_patient_summary_prompt("Blood Test B", report_b_labs)

    res_b = await provider.generate(prompt_b)
    summary_b = res_b["content"]

    # Must not contain Cholesterol or 240
    assert "Cholesterol" not in summary_b
    assert "240" not in summary_b
    assert "Platelets" in summary_b or "250" in summary_b

def test_medication_extraction_preserves_dose_and_frequency():
    """Verify medication names, doses, and frequencies are correctly formatted without floating values."""
    ocr_text = (
        "CURRENT MEDICATIONS:\n"
        "1. Metformin 500 mg twice daily\n"
        "2. Amlodipine 5 mg once daily at 8:00 AM\n"
        "3. Atorvastatin 10 mg once daily"
    )
    labs = extract_lab_values(ocr_text)
    
    # Ensure medication frequencies like "Once daily" are not treated as independent numerical lab values
    lab_names = [l["test_name"].lower() for l in labs]
    assert "once daily" not in lab_names
    assert "8:00 am" not in lab_names
    assert "twice daily" not in lab_names
