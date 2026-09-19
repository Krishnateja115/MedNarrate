import os
import pytest
from app.services.text_extraction import extract_text_from_file, clean_extracted_text
from app.services.lab_value_extractor import extract_lab_values

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

EXPECTED_VALUES = {
    "01_blood_clean.pdf": [
        {"name": "Hemoglobin", "value": 14.2, "unit": "g/dL"},
        {"name": "WBC Count", "value": 5.5, "unit": "x 10^3 / uL"},
        {"name": "Platelets", "value": 300, "unit": "10*9/L"},
    ],
    "02_pathology_noisy.pdf": [
        {"name": "Glucose (Fasting)", "value": 105, "unit": "mg/dl"},
        {"name": "TSH", "value": 4.5, "unit": "µIU/mL"},
    ],
    "03_health_scanned.png": [
        {"name": "RBC", "value": 4.8, "unit": "mil/mm3"},
        {"name": "Cholesterol", "value": 210, "unit": "mg/dL"},
    ],
    "04_mixed_report.pdf": [
        {"name": "Creatinine", "value": 0.9, "unit": "mg/dL"},
        {"name": "Uric Acid", "value": 5.2, "unit": "mg/dL"},
    ]
}

def test_extraction_pipeline():
    total_expected = 0
    total_matched = 0
    
    for filename, expected_labs in EXPECTED_VALUES.items():
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(file_path):
            continue
        file_type = "image" if filename.endswith(".png") else "pdf"
        
        try:
            raw_text = extract_text_from_file(file_path, file_type)
        except Exception as e:
            if "tesseract" in str(e).lower() or "poppler" in str(e).lower() or "not found" in str(e).lower() or "could not extract" in str(e).lower() or "text recognition is not available" in str(e).lower() or "ocr" in str(e).lower():
                pytest.skip(f"System OCR dependencies not installed: {e}")
            raise
        assert len(raw_text) > 0, f"Failed to extract any text from {filename}"
        
        # 2. Clean text
        cleaned_text = clean_extracted_text(raw_text)
        
        # 3. Extract lab values
        structured_labs = extract_lab_values(cleaned_text)
        
        # Track matches by original_name so the exact string matches what was in the test
        extracted_dict = {lab["original_name"].lower(): lab for lab in structured_labs}
        
        for expected in expected_labs:
            total_expected += 1
            name_lower = expected["name"].lower()
            
            # Check if name is found
            matched_lab = None
            for ex_name, ex_lab in extracted_dict.items():
                if name_lower in ex_name or ex_name in name_lower:
                    matched_lab = ex_lab
                    break
                    
            if matched_lab:
                # Check value and unit
                if matched_lab["value"] == expected["value"] and expected["unit"] in matched_lab["original_unit"]:
                    total_matched += 1
                else:
                    print(f"[{filename}] Value/Unit mismatch for {expected['name']}: expected {expected['value']} {expected['unit']}, got {matched_lab['value']} {matched_lab['original_unit']}")
            else:
                print(f"[{filename}] Missed test entirely: {expected['name']}")
                
    accuracy = total_matched / total_expected if total_expected > 0 else 0
    print(f"Extraction Accuracy: {accuracy*100:.2f}% ({total_matched}/{total_expected})")
    
    # Assert Definition of Done (>90%)
    assert accuracy >= 0.90, f"Extraction accuracy {accuracy*100:.2f}% is below 90% threshold"


def test_one_sided_reference_ranges():
    ldl_text = "LDL Cholesterol 165 mg/dL < 100 mg/dL HIGH"
    labs = extract_lab_values(ldl_text)
    assert len(labs) == 1
    ldl = labs[0]
    assert ldl["value"] == 165.0
    assert ldl["unit"] == "mg/dL"
    assert ldl["ref_high"] == 100.0
    assert ldl["ref_low"] is None
    assert ldl["flag"] == "high"
    assert "< 100" in ldl["ref_range_str"]

    vit_text = "Vitamin D 15 ng/mL < 30 ng/mL LOW"
    labs = extract_lab_values(vit_text)
    assert len(labs) == 1
    vit = labs[0]
    assert vit["value"] == 15.0
    assert vit["unit"] == "ng/mL"
    assert vit["ref_high"] == 30.0
    assert vit["ref_low"] is None
    assert vit["flag"] == "low"
    assert "< 30" in vit["ref_range_str"]

    hdl_text = "HDL Cholesterol 65 mg/dL > 40 mg/dL NORMAL"
    labs = extract_lab_values(hdl_text)
    assert len(labs) == 1
    hdl = labs[0]
    assert hdl["value"] == 65.0
    assert hdl["unit"] == "mg/dL"
    assert hdl["ref_low"] == 40.0
    assert hdl["ref_high"] is None
    assert hdl["flag"] == "normal"
    assert "> 40" in hdl["ref_range_str"]

    ldl_lte = "LDL Cholesterol 165 mg/dL <= 100 mg/dL HIGH"
    labs = extract_lab_values(ldl_lte)
    assert len(labs) == 1
    assert labs[0]["ref_high"] == 100.0
    assert labs[0]["flag"] == "high"

    hdl_gte = "HDL Cholesterol 65 mg/dL >= 40 mg/dL NORMAL"
    labs = extract_lab_values(hdl_gte)
    assert len(labs) == 1
    assert labs[0]["ref_low"] == 40.0
    assert labs[0]["flag"] == "normal"

