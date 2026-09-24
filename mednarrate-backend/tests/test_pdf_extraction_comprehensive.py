import os
from unittest.mock import patch

import fitz  # PyMuPDF
import pytest

from app.core.config import settings
from app.services.lab_value_extractor import extract_lab_values
from app.services.text_extraction import (
    CorruptPDFError,
    EmptyFileError,
    ExtractionFileNotFoundError,
    OCRUnavailableError,
    extract_text_with_diagnostics,
    resolve_physical_path,
)


def test_resolve_physical_path_relative_and_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    # Create sample file inside tmp_path
    user_dir = tmp_path / "user_123"
    user_dir.mkdir()
    sample_file = user_dir / "report.pdf"
    sample_file.write_bytes(b"%PDF-1.4 text payload inside sample file")

    # POSIX slash relative path
    resolved_posix = resolve_physical_path("/uploads/user_123/report.pdf")
    assert os.path.exists(resolved_posix)
    assert resolved_posix == str(sample_file)

    # Windows slash relative path
    resolved_win = resolve_physical_path("uploads\\user_123\\report.pdf")
    assert os.path.exists(resolved_win)

    # Bare relative path
    resolved_bare = resolve_physical_path("user_123/report.pdf")
    assert os.path.exists(resolved_bare)

    # Path traversal attack
    with pytest.raises(ExtractionFileNotFoundError) as exc_info:
        resolve_physical_path("../../../etc/passwd")
    assert exc_info.value.failure_category == "FILE_NOT_FOUND"

def test_resolve_physical_path_nonexistent(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    with pytest.raises(ExtractionFileNotFoundError) as exc_info:
        resolve_physical_path("nonexistent_folder/missing.pdf")
    assert exc_info.value.failure_category == "FILE_NOT_FOUND"

def test_zero_byte_file_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    empty_file = tmp_path / "zero_bytes.pdf"
    empty_file.write_bytes(b"")

    with pytest.raises(EmptyFileError) as exc_info:
        extract_text_with_diagnostics(str(empty_file), "pdf")
    assert exc_info.value.failure_category == "EMPTY_FILE"

def test_corrupt_pdf_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"%PDF-1.4 INVALID CORRUPT HEADER DATA NOT A REAL PDF")

    with pytest.raises(CorruptPDFError) as exc_info:
        extract_text_with_diagnostics(str(corrupt_file), "pdf")
    assert exc_info.value.failure_category == "CORRUPT_PDF"

def test_valid_text_pdf_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    pdf_path = tmp_path / "valid_lab_report.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "COMPLETE BLOOD COUNT REPORT\nHemoglobin: 14.2 g/dL\nWBC Count: 5.5 x 10^3 / uL\nPlatelets: 300 10*9/L")
    doc.save(str(pdf_path))
    doc.close()

    text, diagnostics = extract_text_with_diagnostics(str(pdf_path), "pdf")
    
    assert "Hemoglobin: 14.2 g/dL" in text
    assert diagnostics["extraction_method"] == "pymupdf"
    assert diagnostics["ocr_attempted"] is False
    assert diagnostics["page_count"] == 1
    assert diagnostics["char_count"] > 15
    assert diagnostics["failure_category"] is None

def test_scanned_pdf_ocr_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    # Create PDF page with image-like non-text content
    pdf_path = tmp_path / "scanned_document.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Draw a line so page has content but zero selectable text
    page.draw_line((10, 10), (100, 100))
    doc.save(str(pdf_path))
    doc.close()

    with patch("app.services.text_extraction.is_tesseract_available", return_value=False):
        with pytest.raises(OCRUnavailableError) as exc_info:
            extract_text_with_diagnostics(str(pdf_path), "pdf")
        assert exc_info.value.failure_category in ["OCR_UNAVAILABLE", "OCR_ENGINE_UNAVAILABLE"]

def test_fictional_report_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    
    report_filename = "MedNarrate_Fictional_Medical_Report_1.pdf"
    pdf_path = tmp_path / report_filename
    
    doc = fitz.open()
    page = doc.new_page()
    medical_content = (
        "MEDNARRATE FICTIONAL CLINICAL LABORATORY REPORT\n"
        "Patient: Jane Doe | DOB: 1990-04-15 | Date: 2026-09-12\n"
        "Hospital: City General Hospital\n\n"
        "LABORATORY TEST RESULTS:\n"
        "Hemoglobin: 13.8 g/dL (Ref Range: 12.0 - 15.5) Normal\n"
        "White Blood Cell Count: 6.2 x 10^3/uL (Ref Range: 4.5 - 11.0) Normal\n"
        "Glucose (Fasting): 112 mg/dL (Ref Range: 70 - 99) HIGH\n"
        "Platelets: 245 x 10^3/uL (Ref Range: 150 - 450) Normal\n"
    )
    page.insert_text((50, 50), medical_content)
    doc.save(str(pdf_path))
    doc.close()

    # 1. Path Resolution
    resolved = resolve_physical_path(f"/uploads/{report_filename}")
    assert os.path.exists(resolved)

    # 2. Text Extraction & Diagnostics
    text, diagnostics = extract_text_with_diagnostics(resolved, "pdf")
    assert "Hemoglobin: 13.8 g/dL" in text
    assert diagnostics["char_count"] > 100
    assert diagnostics["extraction_method"] == "pymupdf"

    # 3. Lab Extraction
    labs = extract_lab_values(text)
    assert len(labs) >= 3
    test_names = [val["original_name"].lower() for val in labs]
    assert any("hemoglobin" in n for n in test_names)
    assert any("glucose" in n for n in test_names)
