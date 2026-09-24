from datetime import date

import pytest

from app.services.lab_value_extractor import extract_lab_values
from app.services.report_date_extractor import extract_report_date
from app.services.text_extraction import extract_text_from_file
from app.services.validation import validate_and_ground_analysis


def test_empty_extraction_fail_fast(tmp_path):
    # Create an empty file
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"%PDF-1.4 empty")

    with pytest.raises(ValueError, match="Could not extract readable medical text"):
        extract_text_from_file(str(empty_file), "pdf")


def test_source_aware_date_extractor():
    text = (
        "PATIENT REPORT\nDOB: 1985-05-12\nSpecimen Date: 2026-09-10\nGlucose: 95 mg/dL"
    )
    fallback = date(2026, 1, 1)
    extracted = extract_report_date(text, fallback)
    assert extracted == date(2026, 9, 10)
    assert extracted != date(1985, 5, 12)  # DOB must NOT be chosen


def test_medical_validation_disclaimer():
    extracted_text = "Glucose: 105 mg/dL (Ref: 70-99) [HIGH]"
    labs = extract_lab_values(extracted_text)

    res = validate_and_ground_analysis(
        extracted_text=extracted_text,
        structured_lab_values=labs,
        patient_summary="Your glucose level is 105 mg/dL which is slightly elevated.",
        clinician_summary="Mild hyperglycemia detected.",
    )

    assert "disclaimer" in res["patient_summary"].lower()
    assert len(res["structured_lab_values"]) == 1
    assert res["structured_lab_values"][0]["test_name"].lower() == "glucose"


@pytest.mark.asyncio
async def test_llm_client_missing_config_fails_cleanly(monkeypatch):
    from app.core.config import settings
    from app.services.llm_client import generate

    # Ensure no API key or Ollama URL is available
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "OLLAMA_URL", "http://invalid-localhost-url:9999")
    monkeypatch.setattr(settings, "ENABLE_LLM_FALLBACK", False)

    from app.services.llm_client import LLMConfigurationError

    with pytest.raises(LLMConfigurationError, match="not configured or is invalid"):
        await generate("Test prompt", timeout=1.0)
