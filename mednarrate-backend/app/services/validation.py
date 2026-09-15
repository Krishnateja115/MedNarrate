import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "\n\nDisclaimer: This report summary is for educational and informational purposes only "
    "and does not replace professional medical advice, diagnosis, or treatment."
)

def verify_summary_grounding(summary: str, source_text: str, structured_lab_values: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scans generated summary text for numerical values/claims and compares them against
    source report facts to detect unsupported/hallucinated alterations.
    """
    if not summary:
        return {"is_valid": True, "unsupported_numbers": []}

    # Find all standalone float/integer numbers in summary text
    numbers_in_summary = re.findall(r'\b\d+(?:\.\d+)?\b', summary)
    
    # Collect all numbers from source text and structured lab values
    source_lower = source_text.lower()
    known_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', source_text))
    
    for lab in structured_lab_values:
        val = lab.get("value")
        if val is not None:
            known_numbers.add(str(val))
            if isinstance(val, float) and val.is_integer():
                known_numbers.add(str(int(val)))
        for k in ["ref_low", "ref_high"]:
            if lab.get(k) is not None:
                known_numbers.add(str(lab[k]))

    ignored_numbers = {"1", "2", "3", "4", "5"}
    
    unsupported_numbers = []
    for num in numbers_in_summary:
        if num not in known_numbers and num not in ignored_numbers and num not in source_lower:
            unsupported_numbers.append(num)

    is_valid = len(unsupported_numbers) == 0
    if not is_valid:
        logger.warning(f"[VALIDATION:WARN] Found unsupported numerical claims in summary: {unsupported_numbers}")

    return {
        "is_valid": is_valid,
        "unsupported_numbers": unsupported_numbers
    }

def validate_and_ground_analysis(
    extracted_text: str,
    structured_lab_values: List[Dict[str, Any]],
    patient_summary: str,
    clinician_summary: str
) -> Dict[str, Any]:
    """
    Validates generated analysis against source document fidelity:
    1. Ensures extracted lab values are grounded in the source text.
    2. Verifies patient and clinician summaries against source numeric grounding.
    3. Ensures standard educational disclaimer is attached to patient summary.
    """
    text_lower = extracted_text.lower()
    validated_labs = []

    for lab in structured_lab_values:
        test_name = lab.get("test_name", "").lower()
        val = lab.get("value")
        
        # Grounding check: verify numerical value or test name appears in source text
        is_grounded = False
        if test_name in text_lower or (val is not None and str(val) in text_lower):
            is_grounded = True
        else:
            logger.warning(f"Lab value {test_name}={val} could not be strictly grounded in extracted text.")
            
        if is_grounded:
            validated_labs.append(lab)
        else:
            lab_copy = dict(lab)
            lab_copy["ungrounded"] = True
            validated_labs.append(lab_copy)

    # Check grounding of summary texts
    patient_grounding = verify_summary_grounding(patient_summary, extracted_text, structured_lab_values)
    clinician_grounding = verify_summary_grounding(clinician_summary, extracted_text, structured_lab_values)

    # Ensure disclaimer exists in patient summary
    final_patient_summary = patient_summary.strip() if patient_summary else ""
    if final_patient_summary and "disclaimer" not in final_patient_summary.lower():
        final_patient_summary += DISCLAIMER_TEXT

    return {
        "structured_lab_values": validated_labs,
        "patient_summary": final_patient_summary,
        "clinician_summary": clinician_summary.strip() if clinician_summary else "",
        "patient_grounding_valid": patient_grounding["is_valid"],
        "unsupported_claims": patient_grounding["unsupported_numbers"] + clinician_grounding["unsupported_numbers"]
    }
