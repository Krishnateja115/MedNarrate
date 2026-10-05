from app.services.translation_planner import _build_chunks
from app.services.prompts import TRANSLATION_PROMPT
import json

abnormal_findings_source = [{"test_name": "Test1", "explanation": "A long string of explanation text here" * 100}] * 50
chunks = _build_chunks(
    "clinician", "patient", abnormal_findings_source, [], ["test1"], 4000
)
print("Num chunks:", len(chunks))
for i, chunk in enumerate(chunks):
    prompt = TRANSLATION_PROMPT.format(
        target_language="Hindi",
        clinician_summary=chunk["clinician_summary"],
        patient_summary=chunk["patient_summary"],
        abnormal_findings_json=json.dumps(chunk["abnormal_findings"], ensure_ascii=False),
        medications_json="[]",
        unique_parameters_json=json.dumps(chunk["unique_params"], ensure_ascii=False)
    )
    print(f"Chunk {i+1} total char length:", len(prompt), "approx tokens:", len(prompt)//4)
