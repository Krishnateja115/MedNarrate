"""Conservative medical-document gate after OCR and before AI processing."""

import re

from app.services.text_extraction import ExtractionError


_MEDICAL_MARKERS = (
    r"\b(?:complete blood count|cbc|hemoglobin|haemoglobin|hematocrit|"
    r"platelet(?:s| count)?|neutrophils?|lymphocytes?|creatinine|"
    r"bilirubin|hba1c|glucose|cholesterol|tsh)\b",
    r"\b(?:lab(?:oratory)?|pathology|radiology|diagnostic)\s+"
    r"(?:report|results?|findings?|test)\b",
    r"\b(?:clinical findings?|impression|diagnosis|discharge summary|"
    r"prescription|medical history|treatment plan)\b",
    r"\b(?:reference range|ref\.?(?:erence)? interval|specimen|"
    r"sample collected|result\s+unit)\b",
    r"\b(?:patient name|patient id|mrn|consultant|referring physician)\b",
)
_UNRELATED_MARKERS = re.compile(
    r"\b(?:invoice|tax invoice|receipt|purchase order|tracking number|"
    r"shipping address|order total|subtotal|amount due|bank statement|"
    r"account balance|curriculum vitae|resume)\b",
    re.IGNORECASE,
)


def validate_medical_document(text: str) -> None:
    """Reject documents without enough independent evidence of medical content.

    The user's selected report type is intentionally not evidence: a receipt
    uploaded under "blood report" must not be sent to the medical AI.
    """
    sample = text[:12000]
    medical_signals = sum(
        bool(re.search(pattern, sample, re.IGNORECASE))
        for pattern in _MEDICAL_MARKERS
    )
    if medical_signals >= 2:
        return
    if _UNRELATED_MARKERS.search(sample):
        reason = "This appears to be a non-medical document."
    else:
        reason = "We could not confirm this is a medical report."
    raise ExtractionError(
        f"{reason} Please upload a clearer medical report or clinical document.",
        failure_category="NOT_MEDICAL_REPORT",
    )
