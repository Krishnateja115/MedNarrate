import pytest

from app.services.document_validation import validate_medical_document
from app.services.text_extraction import ExtractionError


@pytest.mark.parametrize(
    "text",
    [
        "Laboratory report\nPatient name: A\nHemoglobin 13.4 g/dL\nReference range 12-16",
        "Discharge summary\nPatient name: A\nDiagnosis: pneumonia\nTreatment plan: follow up",
        "Radiology findings\nPatient ID 123\nImpression: no acute abnormality",
    ],
)
def test_accepts_medical_documents(text: str) -> None:
    validate_medical_document(text)


@pytest.mark.parametrize(
    "text",
    [
        "Tax invoice\nOrder total 1,000\nShipping address 5 Main St",
        "This is a long essay about a holiday trip with many ordinary words.",
    ],
)
def test_rejects_nonmedical_documents(text: str) -> None:
    with pytest.raises(ExtractionError) as caught:
        validate_medical_document(text)
    assert caught.value.failure_category == "NOT_MEDICAL_REPORT"
