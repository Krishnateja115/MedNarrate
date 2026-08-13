import pytest
from app.services.normalization import normalize_lab_value

def test_normalization_basic():
    # Test identical canonicalization from two different strings
    
    # Report A: "Hb"
    lab_a = {
        "test_name": "Hb",
        "value": 14.5,
        "unit": "g/dl",
        "ref_low": 13.0,
        "ref_high": 17.0,
        "flag": "normal"
    }
    
    # Report B: "Hemoglobin"
    lab_b = {
        "test_name": "Hemoglobin",
        "value": 14.5,
        "unit": "g/dL",
        "ref_low": 13.0,
        "ref_high": 17.0,
        "flag": "normal"
    }
    
    norm_a = normalize_lab_value(lab_a)
    norm_b = normalize_lab_value(lab_b)
    
    assert norm_a["test_name"] == "hemoglobin"
    assert norm_b["test_name"] == "hemoglobin"
    
    assert norm_a["unit"] == "g/dL"
    assert norm_b["unit"] == "g/dL"
    
    assert norm_a["original_name"] == "Hb"
    assert norm_b["original_name"] == "Hemoglobin"

def test_normalization_unmatched():
    # Unknown test shouldn't break, just pass through
    lab = {
        "test_name": "Random Unknown Test",
        "value": 4.0,
        "unit": "unknown_unit",
    }
    
    norm = normalize_lab_value(lab)
    assert norm["test_name"] == "Random Unknown Test"
    assert norm["unit"] == "unknown_unit"
    assert norm["original_name"] == "Random Unknown Test"
