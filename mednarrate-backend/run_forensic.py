import json
import time
from llama_cpp import Llama
from app.services.translation_planner import _build_chunks
from app.services.prompts import TRANSLATION_PROMPT

def get_tokenizer():
    # Load just enough to tokenize
    model_path = "models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model = Llama(model_path=model_path, n_ctx=4096, vocab_only=True)
    return model

def build_test_data():
    findings = []
    for i in range(23):
        findings.append({
            "test_name": f"Test {i}",
            "value": "12.3",
            "unit": "mg/dL",
            "flag": "HIGH",
            "ref_range_str": "1.0 - 10.0"
        })
    
    clinician_summary = "Patient shows elevated Test 0 and others. " * 10
    patient_summary = "Your blood test showed some high values. " * 10
    unique_params = [f"Test {i}" for i in range(23)]
    
    return clinician_summary, patient_summary, findings, unique_params

def run_forensic():
    clinician, patient, findings, params = build_test_data()
    chunks = _build_chunks(clinician, patient, findings, [], params, 1500)
    
    print(f"A. Number of chunks created: {len(chunks)}")
    
    chunk0 = chunks[0]
    prompt = TRANSLATION_PROMPT.format(
        target_language="Hindi",
        clinician_summary=chunk0["clinician_summary"],
        patient_summary=chunk0["patient_summary"],
        abnormal_findings_json=json.dumps(chunk0["abnormal_findings"], ensure_ascii=False),
        medications_json="[]",
        unique_parameters_json=json.dumps(chunk0["unique_params"], ensure_ascii=False),
    )
    
    model = get_tokenizer()
    tokens = model.tokenize(prompt.encode('utf-8'))
    print(f"B. Input token count for chunk 0: {len(tokens)}")
    
    print(f"C. Max output tokens allowed (max_tokens arg): 4000")
    print(f"D. Local provider timeout: 45 seconds")
    print(f"E. Generation tokens/sec from previous diagnostic: ~9.66 to 11.0 t/s")
    
    # Estimate output token length. 
    # ui_labels has 78 keys. Each key is string + colon + translated string.
    # A single ui_labels block in JSON will easily be ~500-1000 tokens.
    
    # Just the JSON structure of ui_labels:
    mock_ui_labels_json = "{" + ", ".join([f'"{k}": "अनुवादित पाठ (Translated Text)"' for k in range(78)]) + "}"
    mock_ui_tokens = model.tokenize(mock_ui_labels_json.encode('utf-8'))
    print(f"F. Estimated token count for just the ui_labels output: {len(mock_ui_tokens)}")
    
    estimated_time = len(mock_ui_tokens) / 9.66
    print(f"G. Estimated time to generate just the ui_labels: {estimated_time:.2f} seconds")
    print(f"H. Will it timeout before finishing? {'YES' if estimated_time > 45 else 'NO'}")

if __name__ == '__main__':
    run_forensic()
