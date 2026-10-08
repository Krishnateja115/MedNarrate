import re

VALID_LAB_UNITS_SET = {
    "g/dl", "mg/dl", "mmol/l", "umol/l", "iu/l", "u/l", "%", "pg", "fl", "g/l",
    "mil/mm3", "x10^3/ul", "10^9/l", "uiu/ml", "ng/ml", "mcg/dl", "meq/l",
    "cells/µl", "mm/hr", "bpm", "°c", "cells/ul", "µmol/l", "iu/ml"
}

KNOWN_LAB_TESTS = [
    "hemoglobin", "hgb", "hb", "wbc", "rbc", "platelets", "plt", "hematocrit", "hct",
    "glucose", "fbs", "ppbs", "hba1c", "tsh", "t3", "t4", "cholesterol", "hdl", "ldl",
    "triglycerides", "creatinine", "bun", "egfr", "alt", "ast", "alp", "sgot", "sgpt",
    "bilirubin", "uric acid", "sodium", "potassium", "chloride", "calcium", "vitamin",
    "iron", "ferritin", "protein", "albumin", "ggtp", "ggt", "mcv"
]

def extract_lab_values_new(text: str) -> list[dict]:
    results = []
    
    # 1. Clean up spacing to avoid newline issues where possible, 
    # but we need to handle "ALT \n 40 \n U/L"
    # Actually, if we just split the text by whitespace into tokens, it's easier to scan.
    tokens = re.split(r'\s+', text.strip())
    
    # To handle embedded values like "40ALT" or "ALT:40" or "40 U/L", 
    # we should first normalize these by inserting spaces.
    # e.g., "40ALT" -> "40 ALT"
    # e.g., "ALT: 40" -> "ALT 40"
    text = re.sub(r'([A-Za-z])(:|: )(\d)', r'\1 \3', text)
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    
    tokens = re.split(r'\s+', text.strip())
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Check if token is a number
        # Allow negative and decimals
        num_match = re.match(r'^-?\d+\.?\d*$', token)
        if num_match:
            val = float(num_match.group(0))
            
            # Context window
            # prev 3 tokens, next 3 tokens
            prev_tokens = tokens[max(0, i-3):i]
            next_tokens = tokens[i+1:min(len(tokens), i+4)]
            
            name = None
            unit = None
            ref_low = None
            ref_high = None
            
            # Find unit
            for t in next_tokens + prev_tokens:
                if t.lower() in VALID_LAB_UNITS_SET:
                    unit = t
                    break
            
            # Find name
            for t in prev_tokens + next_tokens:
                clean_t = re.sub(r'[^A-Za-z0-9]', '', t).lower()
                if clean_t in KNOWN_LAB_TESTS:
                    name = t.strip(':')
                    break
            
            if name:
                results.append({
                    "test_name": name,
                    "value": val,
                    "unit": unit or ""
                })
        i += 1
    
    return results

print(extract_lab_values_new("DELHI \n 110085 \n SWASTHFIT SUPER \n 4 \n U/L \n 40 ALT \n U/L \n 50 GGTP"))
