import json
from app.services.translation_validation import validate_translation
from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
from app.services.translation_planner import _build_chunks

clinician_summary = "CLINICAL INDICATION: 45-year-old male with chronic cough and shortness of breath." * 5
patient_summary = "The patient has a cough and trouble breathing." * 5
abnormal_findings = [
    {"test_name": "Hemoglobin", "explanation": "Low hemoglobin", "translated_test_name": "Hemoglobin", "translated_explanation": "Low hemoglobin"}
] * 5
meds = [
    {"medication_name": "Albuterol", "dosage": "90 mcg", "frequency": "Every 4 hours", "instructions": "Inhale", "translated_medication_name": "Albuterol", "translated_dosage": "90 mcg", "translated_frequency": "Every 4 hours", "translated_times_of_day": [], "translated_instructions": "Inhale"}
] * 2

try:
    with open("qwen_capture_1.json", "r", encoding="utf-8") as f:
        content = f.read()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        # It's truncated. Let's fix it by appending missing braces.
        # But wait, did the user's test have a valid JSON that reached validation?
        # "Generated JSON reached validation..."
        pass
except Exception as e:
    print(e)
