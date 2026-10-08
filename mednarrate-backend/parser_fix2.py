import re
from typing import List, Optional

VALID_LAB_UNITS_SET = {
    "g/dl", "mg/dl", "mmol/l", "umol/l", "iu/l", "u/l", "%", "pg", "fl", "g/l",
    "mil/mm3", "x10^3/ul", "10^9/l", "uiu/ml", "ng/ml", "mcg/dl", "meq/l",
    "cells/µl", "mm/hr", "bpm", "°c", "cells/ul"
}

KNOWN_LAB_TESTS_SET = {
    "hemoglobin", "hgb", "hb", "wbc", "rbc", "platelets", "plt", "hematocrit", "hct",
    "glucose", "fbs", "ppbs", "hba1c", "tsh", "t3", "t4", "cholesterol", "hdl", "ldl",
    "triglycerides", "creatinine", "bun", "egfr", "alt", "ast", "alp", "sgot", "sgpt",
    "bilirubin", "uric acid", "sodium", "potassium", "chloride", "calcium", "vitamin",
    "iron", "ferritin", "protein", "albumin", "ggtp", "ggt", "mcv"
}

DEMOGRAPHIC_PATTERNS = re.compile(
    r"^(date of birth|dob|age|gender|sex|patient|mrn|id|hospital|doctor|physician|phone|address|"
    r"date|collection|referred|report id|pathology|signature|interpretation|male|female|years|yrs|months)$",
    re.IGNORECASE,
)

def is_valid_unit(u: str) -> bool:
    if not u:
        return False
    # allow variations like u/l, u/L, U/L, U/l etc.
    return u.lower() in VALID_LAB_UNITS_SET or re.match(r"^(x10\^|10\^)\d", u.lower())

def extract_lab_values_robust(text: str) -> list[dict]:
    results = []
    
    # Pre-process text to insert spaces between numbers and letters if joined
    # e.g. "40ALT" -> "40 ALT"
    text = re.sub(r'([A-Za-z])(:|: )(\d)', r'\1 \3', text)
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    
    # We can split text into tokens
    tokens = [t.strip() for t in re.split(r'\s+', text.strip()) if t.strip()]
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Is it a value?
        num_match = re.match(r'^-?\d+\.?\d*$', token)
        if num_match:
            val = float(num_match.group(0))
            
            # Find context
            prev_tokens = tokens[max(0, i-4):i]
            next_tokens = tokens[i+1:min(len(tokens), i+5)]
            
            name = None
            unit = None
            ref_low = None
            ref_high = None
            
            # 1. Identify unit
            # It's usually the token immediately after or before, or 1 token away
            for t in next_tokens + prev_tokens:
                if is_valid_unit(t):
                    unit = t
                    break
                    
            # 2. Identify name
            # Check for KNOWN tests first in immediate vicinity
            for t in reversed(prev_tokens): # closest previous
                clean_t = re.sub(r'[^A-Za-z0-9]', '', t).lower()
                if clean_t in KNOWN_LAB_TESTS_SET:
                    name = t.strip(':')
                    break
            if not name:
                for t in next_tokens: # closest next
                    clean_t = re.sub(r'[^A-Za-z0-9]', '', t).lower()
                    if clean_t in KNOWN_LAB_TESTS_SET:
                        name = t.strip(':')
                        break
                        
            # If no known test name found, try to guess name from previous token
            if not name:
                if len(prev_tokens) > 0:
                    cand = prev_tokens[-1].strip(':')
                    # exclude units, demographic patterns, purely numeric
                    if not is_valid_unit(cand) and not DEMOGRAPHIC_PATTERNS.match(cand) and not re.match(r'^-?\d+\.?\d*$', cand):
                        if len(cand) > 1:
                            name = cand
            
            if name:
                results.append({
                    "test_name": name,
                    "value": val,
                    "unit": unit or ""
                })
        i += 1
        
    return results

print(extract_lab_values_robust("DELHI \n 110085 \n SWASTHFIT SUPER \n 4 \n U/L \n 40 ALT \n U/L \n 50 GGTP"))
