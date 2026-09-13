import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "\n\nDisclaimer: This report summary is for educational and informational purposes only "
    "and does not replace professional medical advice, diagnosis, or treatment."
)

def validate_and_ground_analysis(
    extracted_text: str,
    structured_lab_values: List[Dict[str, Any]],
    patient_summary: str,
    clinician_summary: str
) -> Dict[str, Any]:
    """
    Validates generated analysis against source document fidelity:
    1. Ensures extracted lab values are grounded in the source text.
    2. Ensures standard educational disclaimer is attached to patient summary.
    3. Logs warnings for ungrounded numerical claims.
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
            # Mark ungrounded flag for safety tracking
            lab_copy = dict(lab)
            lab_copy["ungrounded"] = True
            validated_labs.append(lab_copy)

    # Ensure disclaimer exists in patient summary
    final_patient_summary = patient_summary.strip() if patient_summary else ""
    if final_patient_summary and "disclaimer" not in final_patient_summary.lower():
        final_patient_summary += DISCLAIMER_TEXT

    return {
        "structured_lab_values": validated_labs,
        "patient_summary": final_patient_summary,
        "clinician_summary": clinician_summary.strip() if clinician_summary else ""
    }
