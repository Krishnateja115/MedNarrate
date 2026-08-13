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
        file_type = "image" if filename.endswith(".png") else "pdf"
        
        # 1. Extract text
        raw_text = extract_text_from_file(file_path, file_type)
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
