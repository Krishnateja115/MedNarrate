import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "\n\nDisclaimer: This report summary is for educational and informational purposes only "
    "and does not replace professional medical advice, diagnosis, or treatment."
)


def verify_summary_grounding(
    summary: str, source_text: str, structured_lab_values: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Scans generated summary text for numerical values and medical diagnostic claims,
    comparing them against source report facts to detect unsupported alterations or assertions.
    """
    if not summary:
        return {
            "is_valid": True,
            "unsupported_numbers": [],
            "unsupported_diagnoses": [],
        }

    source_lower = source_text.lower()
    summary_lower = summary.lower()

    # 1. Numerical grounding check
    numbers_in_summary = re.findall(r"\b\d+(?:\.\d+)?\b", summary)
    known_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", source_text))

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
        if (
            num not in known_numbers
            and num not in ignored_numbers
            and num not in source_lower
        ):
            unsupported_numbers.append(num)

    # 2. High-risk medical diagnostic claims check
    high_risk_diagnoses = [
        "diabetes",
        "type 2 diabetes",
        "heart failure",
        "congestive heart failure",
        "cancer",
        "leukemia",
        "lymphoma",
        "stroke",
        "kidney failure",
        "renal failure",
    ]
    unsupported_diagnoses = []
    for diag in high_risk_diagnoses:
        if diag in summary_lower and diag not in source_lower:
            # Check if it was negated or explicitly stated as absent/educational
            if (
                f"no {diag}" not in summary_lower
                and "not provided" not in summary_lower
                and "does not replace" not in summary_lower
            ):
                unsupported_diagnoses.append(diag)

    is_valid = len(unsupported_numbers) == 0 and len(unsupported_diagnoses) == 0
    if not is_valid:
        logger.warning(
            "[VALIDATION:WARN] Unsupported claims detected in summary. "
            "(Raw diagnoses and numerical claims omitted for privacy)"
        )

    return {
        "is_valid": is_valid,
        "unsupported_numbers": unsupported_numbers,
        "unsupported_diagnoses": unsupported_diagnoses,
    }


def validate_and_ground_analysis(
    extracted_text: str,
    structured_lab_values: List[Dict[str, Any]],
    patient_summary: str,
    clinician_summary: str,
) -> Dict[str, Any]:
    """
    Validates generated analysis against source document fidelity:
    1. Ensures extracted lab values are grounded in the source text.
    2. Verifies patient and clinician summaries against source numeric and medical claim grounding.
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
            logger.warning(
                "A lab value could not be strictly grounded in extracted text (validation error)."
            )

        if is_grounded:
            validated_labs.append(lab)
        else:
            lab_copy = dict(lab)
            lab_copy["ungrounded"] = True
            validated_labs.append(lab_copy)

    # Check grounding of summary texts
    patient_grounding = verify_summary_grounding(
        patient_summary, extracted_text, structured_lab_values
    )
    clinician_grounding = verify_summary_grounding(
        clinician_summary, extracted_text, structured_lab_values
    )

    # Ensure disclaimer exists in patient summary
    final_patient_summary = patient_summary.strip() if patient_summary else ""
    if final_patient_summary and "disclaimer" not in final_patient_summary.lower():
        final_patient_summary += DISCLAIMER_TEXT

    return {
        "structured_lab_values": validated_labs,
        "patient_summary": final_patient_summary,
        "clinician_summary": clinician_summary.strip() if clinician_summary else "",
        "patient_grounding_valid": patient_grounding["is_valid"],
        "unsupported_claims": (
            patient_grounding["unsupported_numbers"]
            + clinician_grounding["unsupported_numbers"]
            + patient_grounding["unsupported_diagnoses"]
            + clinician_grounding["unsupported_diagnoses"]
        ),
    }
