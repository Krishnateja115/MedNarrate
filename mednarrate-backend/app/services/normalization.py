TEST_NAME_SYNONYMS = {
    # Hemoglobin variants
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "haemoglobin": "hemoglobin",
    "hemoglobin": "hemoglobin",
    
    # White Blood Cells variants
    "wbc": "wbc_count",
    "white blood cell": "wbc_count",
    "white blood cells": "wbc_count",
    "white blood cell count": "wbc_count",
    "wbc count": "wbc_count",
    "leukocyte count": "wbc_count",
    
    # Red Blood Cells variants
    "rbc": "rbc_count",
    "red blood cell": "rbc_count",
    "red blood cells": "rbc_count",
    "red blood cell count": "rbc_count",
    "rbc count": "rbc_count",
    "erythrocyte count": "rbc_count",
    
    # Platelets
    "plt": "platelets",
    "platelet count": "platelets",
    "platelets": "platelets",
    
    # Glucose
    "glucose (fasting)": "fasting_glucose",
    "fbs": "fasting_glucose",
    "fasting blood sugar": "fasting_glucose",
    "glucose fasting": "fasting_glucose",
    "glucose": "glucose",
    
    # TSH
    "tsh": "tsh",
    "thyroid (tsh)": "tsh",
    "thyroid stimulating hormone": "tsh",
    
    # Cholesterol
    "cholesterol": "cholesterol",
    "total cholesterol": "cholesterol",
    
    # Creatinine
    "creatinine": "creatinine",
    "creat": "creatinine",
    
    # Uric Acid
    "uric acid": "uric_acid",
}

UNIT_SYNONYMS = {
    "g/dl": "g/dL",
    "gm/dl": "g/dL",
    "mg/dl": "mg/dL",
    "mg/dL": "mg/dL",
    "mil/mm3": "mil/mm3",
    "10*9/l": "10^9/L",
    "10^9/l": "10^9/L",
    "x 10^3 / ul": "x10^3/uL",
    "x 10^3/ul": "x10^3/uL",
    "x10^3/ul": "x10^3/uL",
    "µiu/ml": "µIU/mL",
    "ui/l": "U/L",
    "u/l": "U/L",
}

def normalize_lab_value(lab_dict: dict) -> dict:
    """
    Normalizes the test name and unit in a lab value dictionary.
    Preserves the original name and unit in 'original_name' and 'original_unit'.
    """
    original_name = lab_dict.get("test_name", "").strip()
    original_unit = lab_dict.get("unit", "").strip()
    
    # Lowercase for dictionary lookup
    name_lookup = original_name.lower().strip()
    # Normalize excessive spaces in name
    name_lookup = " ".join(name_lookup.split())
    
    unit_lookup = original_unit.lower().strip()
    unit_lookup = " ".join(unit_lookup.split())
    
    # Lookup canonical name, fallback to original if not found
    canonical_name = TEST_NAME_SYNONYMS.get(name_lookup, original_name)
    canonical_unit = UNIT_SYNONYMS.get(unit_lookup, original_unit)
    
    # Create the new dictionary
    normalized_dict = dict(lab_dict)
    normalized_dict["original_name"] = original_name
    normalized_dict["original_unit"] = original_unit
    normalized_dict["test_name"] = canonical_name
    normalized_dict["unit"] = canonical_unit
    
    return normalized_dict
