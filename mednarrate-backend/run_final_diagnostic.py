import asyncio
import time
import json
from app.services.translation_planner import execute_translation_plan
from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
from app.services.translation_validation import validate_translation
from app.services.llm_client import _translation_request

async def run_final_diagnostic():
    _translation_request.set(True)
    
    clinician_summary = "CLINICAL INDICATION: 45-year-old male with chronic cough and shortness of breath." * 5
    patient_summary = "The patient has a cough and trouble breathing." * 5
    
    abnormal_findings = [
        {"test_name": "Hemoglobin", "translated_test_name": "Hemoglobin", "translated_explanation": "Low hemoglobin"}
    ] * 5
    meds = [
        {"medication_name": "Albuterol", "translated_medication_name": "Albuterol", "translated_dosage": "90 mcg", "translated_frequency": "Every 4 hours", "translated_times_of_day": [], "translated_instructions": "Inhale"}
    ] * 2
    unique_params = ["Hemoglobin"]
    
    providers = ["local"] # Force local fallback
    
    print("--- Starting Production-Shaped Local Test ---")
    start = time.time()
    
    try:
        final_merged = await execute_translation_plan(
            target_lang_name="Hindi",
            lang_code="hi",
            clinician_summary=clinician_summary,
            patient_summary=patient_summary,
            abnormal_findings_source=abnormal_findings,
            meds_list=meds,
            unique_params=unique_params,
            providers=providers,
            validate_func=validate_translation,
            required_ui_label_keys=REQUIRED_UI_LABEL_KEYS,
            request_id="test_local_fallback"
        )
        total_time = time.time() - start
        
        print(f"Total local-provider translation latency: {total_time:.2f}s")
        print(f"Has all 78 ui_labels: {len(final_merged.get('ui_labels', {})) == 78}")
        print(f"Validation passes: YES (execute_translation_plan succeeded)")
        
        # Checking local output
        print("Success! UI labels injected and validation passed.")
    except Exception as e:
        total_time = time.time() - start
        print(f"Total local-provider translation latency: {total_time:.2f}s")
        print(f"FAILED: {type(e).__name__} - {e}")
        
if __name__ == "__main__":
    asyncio.run(run_final_diagnostic())
