import io
import pytest
from PIL import Image, ImageDraw, ImageFont
from app.services.text_extraction import (
    extract_text_with_diagnostics,
    extract_text_from_file,
    clean_extracted_text,
    preprocess_image_variants,
    validate_extracted_text,
    run_ocr_on_image,
    ExtractionError,
    OCRUnavailableError,
    OCRNoMeaningfulTextError,
    ImageDecodeError,
    UnsupportedFileTypeError
)
from app.services.lab_value_extractor import extract_lab_values
from app.services.file_storage import sanitize_filename

def create_synthetic_image(text: str, fmt: str = "PNG") -> bytes:
    """Helper creating synthetic image bytes with text for OCR testing."""
    img = Image.new('RGB', (800, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Draw simple text
    d.text((50, 50), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def test_sanitize_filename_image_extensions():
    """Verify image filename sanitization and extensions."""
    assert sanitize_filename("report1.png") == "report1.png"
    assert sanitize_filename("../report1.jpg") == "report1.jpg"
    assert sanitize_filename("scan report (1).jpeg") == "scanreport1.jpeg"

def test_clean_extracted_text_preserves_numeric_fidelity():
    """Verify medical numeric values (decimals, ranges) are strictly preserved."""
    raw_ocr = "HbA1c = 6.5 % \n Glucose = 98 mg/dL \n Metformin = 500 mg twice daily"
    cleaned = clean_extracted_text(raw_ocr)
    assert "6.5" in cleaned
    assert "98" in cleaned
    assert "500" in cleaned
    assert "HbA1c" in cleaned

def test_preprocess_image_variants():
    """Verify image preprocessing generates grayscale and contrast variants."""
    img_bytes = create_synthetic_image("Blood Test Results\nHbA1c: 6.5 %")
    img = Image.open(io.BytesIO(img_bytes))
    variants = preprocess_image_variants(img)
    assert len(variants) >= 2
    assert variants[0].size == img.size

def test_validate_extracted_text_success():
    """Verify valid medical OCR text passes quality validation."""
    medical_text = "PATIENT LAB REPORT\nHbA1c: 6.5 %\nGlucose: 98 mg/dL\nNormal Range: 70-99"
    # Should not raise exception
    validate_extracted_text(medical_text, is_image=True)

def test_validate_extracted_text_garbage_fails():
    """Verify low quality garbage text raises OCRNoMeaningfulTextError."""
    garbage_text = "### ||| ___"
    with pytest.raises(OCRNoMeaningfulTextError) as exc_info:
        validate_extracted_text(garbage_text, is_image=True)
    assert exc_info.value.failure_category == "OCR_NO_MEANINGFUL_TEXT"

def test_image_decoding_failure(tmp_path):
    """Verify invalid image bytes raise ImageDecodeError."""
    corrupt_image_path = tmp_path / "corrupt_report.png"
    corrupt_image_path.write_bytes(b"NOT_A_REAL_PNG_IMAGE_HEADER_12345")
    
    with pytest.raises(ImageDecodeError) as exc_info:
        extract_text_with_diagnostics(str(corrupt_image_path), "image")
    assert exc_info.value.failure_category == "IMAGE_DECODE_ERROR"

def test_unsupported_file_type(tmp_path):
    """Verify unsupported file format raises UnsupportedFileTypeError."""
    dummy_file = tmp_path / "report.exe"
    dummy_file.write_bytes(b"MZ123456789")
    
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        extract_text_with_diagnostics(str(dummy_file), "exe")
    assert exc_info.value.failure_category == "FILE_INVALID"

def test_medical_fact_preservation_fixture():
    """Fixture test verifying HbA1c, Glucose, and Metformin facts are preserved."""
    ocr_text = (
        "PATIENT REPORT\n"
        "Date: 14 September 2026\n"
        "HbA1c: 6.5 %\n"
        "Glucose: 98 mg/dL\n"
        "Metformin: 500 mg twice daily"
    )
    cleaned = clean_extracted_text(ocr_text)
    labs = extract_lab_values(cleaned)
    
    # Check that lab values were extracted with exact numeric fidelity
    hba1c_lab = next((l for l in labs if "hba1c" in l["test_name"].lower() or "hba1c" in l["original_name"].lower()), None)
    glucose_lab = next((l for l in labs if "glucose" in l["test_name"].lower() or "glucose" in l["original_name"].lower()), None)
    
    assert hba1c_lab is not None
    assert hba1c_lab["value"] == 6.5
    assert glucose_lab is not None
    assert glucose_lab["value"] == 98.0
