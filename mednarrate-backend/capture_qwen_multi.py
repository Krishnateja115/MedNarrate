import asyncio
import time
import json
from app.services.translation_planner import _build_chunks
from app.services.llm_client import llm_client_instance
from app.services.translation_validation import validate_translation
from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
from llama_cpp import Llama

async def run_capture_multi():
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
    
    from app.services.prompts import TRANSLATION_PROMPT
    prompt = TRANSLATION_PROMPT.format(
        target_language="Hindi",
        clinician_summary=chunks[0]["clinician_summary"],
        patient_summary=chunks[0]["patient_summary"],
        abnormal_findings_json=json.dumps(chunks[0]["abnormal_findings"], ensure_ascii=False),
        medications_json=json.dumps(chunks[0]["medications"], ensure_ascii=False),
        unique_parameters_json=json.dumps(chunks[0]["unique_params"], ensure_ascii=False),
    )
    
    provider = llm_client_instance.get_provider("local")
    model = Llama(model_path="models/qwen2.5-1.5b-instruct-q4_k_m.gguf", n_ctx=4096, vocab_only=True)
    
    for i in range(1, 4):
        print(f"--- Starting Repetition {i} ---")
        start = time.time()
        try:
            result = await provider.generate(prompt, timeout=1000.0)
            total_time = time.time() - start
            content = result["content"]
            
            with open(f"qwen_capture_{i}.json", "w", encoding="utf-8") as f:
                f.write(content)
                
            out_tokens = len(model.tokenize(content.encode('utf-8')))
            
            # check json valid
            is_json = False
            try:
                parsed = json.loads(content)
                is_json = True
            except:
                pass
                
            print(f"Rep {i}: time={total_time:.2f}s, tokens={out_tokens}, json={is_json}")
        except Exception as e:
            total_time = time.time() - start
            print(f"Rep {i} FAILED: {type(e).__name__} - {e} (time={total_time:.2f}s)")
        
if __name__ == "__main__":
    asyncio.run(run_capture_multi())
