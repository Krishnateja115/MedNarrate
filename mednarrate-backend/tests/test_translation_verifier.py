import pytest
from app.services.translation_validation import TranslationVerifier

def test_script_check_mostly_english():
    verifier = TranslationVerifier()
    source = {"clinical_summary": "Patient has mild anemia."}
    bad_output = {"clinical_summary": "Patient has mild anemia in blood. The values are checked."}
    result = verifier.verify(source, bad_output, "te")
    assert not result["ok"]
    assert any(f["rule"] == "script_ratio" for f in result["failures"])

def test_truncated_fragment():
    verifier = TranslationVerifier()
    source = {"clinical_summary": "This is a very long clinical summary that provides authoritative values above."}
    bad_output = {"clinical_summary": "…authoritative):"}
    result = verifier.verify(source, bad_output, "te")
    assert not result["ok"]
    assert any(f["rule"] in ("forbidden_content", "length_ratio") for f in result["failures"])

def test_raw_snake_case():
    verifier = TranslationVerifier()
    source = {"clinical_summary": "Patient has low rbc count."}
    bad_output = {"clinical_summary": "Patient has low rbc_count."}
    result = verifier.verify(source, bad_output, "te")
    assert not result["ok"]
    assert any(f["rule"] == "forbidden_content" for f in result["failures"])

def test_changed_or_missing_number():
    verifier = TranslationVerifier()
    source = {"clinical_summary": "Hemoglobin 10.5 g/dL (range 12-16)"}
    
    # Missing number
    bad_output_1 = {"clinical_summary": "హీమోగ్లోబిన్ g/dL (range 12-16)"}
    result_1 = verifier.verify(source, bad_output_1, "te")
    assert not result_1["ok"]
    assert any(f["rule"] == "numeric_integrity" for f in result_1["failures"])
    
    # Added number
    bad_output_2 = {"clinical_summary": "హీమోగ్లోబిన్ 10.5 g/dL 99 (range 12-16)"}
    result_2 = verifier.verify(source, bad_output_2, "te")
    assert not result_2["ok"]
    assert any(f["rule"] == "numeric_integrity" for f in result_2["failures"])

def test_markdown_fence():
    verifier = TranslationVerifier()
    source = {"clinical_summary": "Hello"}
    bad_output = {"clinical_summary": "```json\nHello\n```"}
    result = verifier.verify(source, bad_output, "te")
    assert not result["ok"]
    assert any(f["rule"] == "forbidden_content" for f in result["failures"])
