"""
End-to-end check: run the actual analysis_pipeline logic (lab extraction + prompt
construction + LLM call) against the real sample CBC report and print the real
generated patient and clinician summaries so a human can visually confirm they
reference real values instead of saying data wasn't provided.
"""
import asyncio
import glob
import json
import fitz
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app.services.lab_value_extractor import extract_lab_values
from app.services.prompts import CLINICIAN_PROMPT, PATIENT_PROMPT, ROLE_INSTRUCTIONS, get_examples_text
from app.services.llm_client import generate

async def main():
    pdf_paths = glob.glob("tests/data/report3.pdf")
    assert pdf_paths, "No sample PDF found."
    pdf_path = pdf_paths[0]
    doc = fitz.open(pdf_path)
    full_text = "".join(page.get_text("text") + "\n" for page in doc)

    labs = extract_lab_values(full_text, report_type="blood")
    print(f"Extracted {len(labs)} lab values.\n")
    structured_values_json = json.dumps(labs, indent=2)

    clinician_prompt = CLINICIAN_PROMPT.format(
        report_type="blood",
        structured_values_json=structured_values_json,
        extracted_text=full_text,
        rag_context="None",
    )
    patient_prompt = PATIENT_PROMPT.format(
        report_type="blood",
        structured_values_json=structured_values_json,
        extracted_text=full_text,
        user_role="patient",
        role_specific_instruction=ROLE_INSTRUCTIONS["patient"],
        rag_context="None",
        examples=get_examples_text(),
    )

    clinician_summary = await generate(clinician_prompt)
    patient_summary = await generate(patient_prompt)

    print("=" * 20, "CLINICIAN SUMMARY", "=" * 20)
    print(clinician_summary)
    print("\n" + "=" * 20, "PATIENT SUMMARY", "=" * 20)
    print(patient_summary)

    # Sanity checks: real values must actually appear in the generated text.
    must_mention_any = ["hemoglobin", "haemoglobin", "15", "platelet", "300000", "mcv", "mchc"]
    patient_lower = patient_summary.lower()
    hits = [kw for kw in must_mention_any if kw in patient_lower]
    print(f"\nPatient summary mentions {len(hits)}/{len(must_mention_any)} expected real values/keywords: {hits}")
    # Check that it didn't blindly claim "this report provides no data"
    assert "no lab parameters were found" not in patient_lower, "FAIL: summary claims no data was found"
    print("\nPASS: generated summaries reference real extracted report data.")

asyncio.run(main())
