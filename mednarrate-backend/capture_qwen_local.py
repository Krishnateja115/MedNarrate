import asyncio
import time
import json
from app.services.translation_planner import _build_chunks
from app.services.llm_client import llm_client_instance

async def run_capture_local():
    clinician_summary = "CLINICAL INDICATION: 45-year-old male with chronic cough and shortness of breath." * 5
    patient_summary = "The patient has a cough and trouble breathing." * 5
    
    abnormal_findings = [
        {"test_name": "Hemoglobin", "translated_test_name": "Hemoglobin", "translated_explanation": "Low hemoglobin"}
    ] * 5
    meds = [
        {"medication_name": "Albuterol", "translated_medication_name": "Albuterol", "translated_dosage": "90 mcg", "translated_frequency": "Every 4 hours", "translated_times_of_day": [], "translated_instructions": "Inhale"}
    ] * 2
    unique_params = ["Hemoglobin"]
    
    chunks = _build_chunks(clinician_summary, patient_summary, abnormal_findings, meds, unique_params, 1500)
    
    from app.services.prompts import LOCAL_TRANSLATION_PROMPT
    prompt = LOCAL_TRANSLATION_PROMPT.format(
        target_language="Hindi",
        clinician_summary=chunks[0]["clinician_summary"],
        patient_summary=chunks[0]["patient_summary"],
        abnormal_findings_json=json.dumps(chunks[0]["abnormal_findings"], ensure_ascii=False),
        medications_json=json.dumps(chunks[0]["medications"], ensure_ascii=False),
        unique_parameters_json=json.dumps(chunks[0]["unique_params"], ensure_ascii=False),
    )
    
    provider = llm_client_instance.get_provider("local")
    print("--- Starting Test With LOCAL_TRANSLATION_PROMPT ---")
    start = time.time()
    
    try:
        result = await provider.generate(prompt, timeout=1000.0)
        total_time = time.time() - start
        content = result["content"]
        with open("qwen_capture_local.json", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Total latency: {total_time:.2f}s")
        print("Success! Output captured in qwen_capture_local.json.")
        
        # Now run validation on it
        from app.services.translation_validation import validate_translation, parse_translation
        from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
        try:
            parsed = parse_translation(content)
            validate_translation(parsed, "Hindi", clinician_summary, patient_summary, abnormal_findings, meds, REQUIRED_UI_LABEL_KEYS)
            print("Validation PASSED")
        except Exception as e:
            print(f"Validation FAILED: {type(e).__name__} - {e}")
            
    except Exception as e:
        total_time = time.time() - start
        print(f"FAILED: {type(e).__name__} - {e}")
        
if __name__ == "__main__":
    asyncio.run(run_capture_local())
