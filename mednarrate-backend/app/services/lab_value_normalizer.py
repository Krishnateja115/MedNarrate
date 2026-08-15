import re

LAB_PARAMETER_ALIASES = {
    # Hemoglobin variations
    "hb": "Hemoglobin",
    "hgb": "Hemoglobin",
    "haemoglobin": "Hemoglobin",
    "hemoglobin": "Hemoglobin",
    
    # Red blood cells
    "rbc": "RBC",
    "rbc count": "RBC",
    "red blood cells": "RBC",
    "red blood cell count": "RBC",
    "erythrocyte count": "RBC",
    
    # White blood cells
    "wbc": "WBC",
    "wbc count": "WBC",
    "white blood cells": "WBC",
    "white blood cell count": "WBC",
    "leukocyte count": "WBC",
    "tlc": "WBC",
    "total leukocyte count": "WBC",
    
    # Platelets
    "plt": "Platelets",
    "platelet count": "Platelets",
    "thrombocytes": "Platelets",
    "thrombocyte count": "Platelets",
    
    # Lipids
    "cholesterol total": "Cholesterol",
    "total cholesterol": "Cholesterol",
    "cholesterol": "Cholesterol",
    "tc": "Cholesterol",
    
    "hdl": "HDL Cholesterol",
    "hdl cholesterol": "HDL Cholesterol",
    "hdl-c": "HDL Cholesterol",
    
    "ldl": "LDL Cholesterol",
    "ldl cholesterol": "LDL Cholesterol",
    "ldl-c": "LDL Cholesterol",
    
    "triglycerides": "Triglycerides",
    "tg": "Triglycerides",
    "trig": "Triglycerides",
    
    # Sugar / Diabetes
    "fasting blood sugar": "Fasting Glucose",
    "fbs": "Fasting Glucose",
    "glucose fasting": "Fasting Glucose",
    "fasting plasma glucose": "Fasting Glucose",
    
    "ppbs": "Postprandial Glucose",
    "postprandial blood sugar": "Postprandial Glucose",
    
    "hba1c": "HbA1c",
    "glycated hemoglobin": "HbA1c",
    "glycosylated hemoglobin": "HbA1c",
    "a1c": "HbA1c",
    
    # Liver
    "sgpt": "ALT",
    "alt": "ALT",
    "alanine aminotransferase": "ALT",
    
    "sgot": "AST",
    "ast": "AST",
    "aspartate aminotransferase": "AST",
    
    "alkaline phosphatase": "ALP",
    "alp": "ALP",
    "alk phos": "ALP",
    
    "bilirubin total": "Total Bilirubin",
    "total bilirubin": "Total Bilirubin",
    "t.bili": "Total Bilirubin",
    
    # Kidney / Renal
    "creatinine": "Creatinine",
    "serum creatinine": "Creatinine",
    "creat": "Creatinine",
    
    "blood urea nitrogen": "BUN",
    "bun": "BUN",
    "urea": "Urea",
    
    "uric acid": "Uric Acid",
    "serum uric acid": "Uric Acid",
    
    # Thyroid
    "tsh": "TSH",
    "thyroid stimulating hormone": "TSH",
    
    "t3": "T3",
    "total t3": "T3",
    "triiodothyronine": "T3",
    
    "t4": "T4",
    "total t4": "T4",
    "thyroxine": "T4",
    
    # Basic Metabolic / Electrolytes
    "sodium": "Sodium",
    "na": "Sodium",
    
    "potassium": "Potassium",
    "k": "Potassium",
    
    "chloride": "Chloride",
    "cl": "Chloride",
    
    "calcium": "Calcium",
    "ca": "Calcium",
    
    # Iron
    "iron": "Iron",
    "serum iron": "Iron",
    
    "ferritin": "Ferritin",
    "serum ferritin": "Ferritin",
    
    "tibc": "TIBC",
    "total iron binding capacity": "TIBC"
}

def normalize_parameter_name(raw_name: str) -> str:
    """Maps variant spellings to canonical names."""
    # Clean up spaces, punctuation, and lowercase
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', raw_name).strip().lower()
    return LAB_PARAMETER_ALIASES.get(cleaned, raw_name.title())
