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
    "total iron binding capacity": "TIBC",
}


_ACRONYMS = {
    "mcv", "mch", "mchc", "rdw", "cv", "sd", "mpv", "pdw", "pct", "hct", "rbc", "wbc",
    "alt", "ast", "alp", "ggt", "ggtp", "ldl", "hdl", "vldl", "tsh", "bun", "egfr",
    "hba1c", "crp", "esr", "inr", "pt", "aptt", "psa", "t3", "t4", "ft3", "ft4", "hb",
    "hgb", "plt", "tlc", "dlc", "sgot", "sgpt", "ck", "ldh", "gfr", "mg", "na", "k",
}


def normalize_parameter_name(raw_name: str) -> str:
    """Maps variant spellings to canonical names."""
    # Clean up spaces, punctuation, and lowercase
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", raw_name).strip().lower()
    alias = LAB_PARAMETER_ALIASES.get(cleaned)
    if alias:
        return alias
    # Keep medical acronyms upper-case ("MCV", "RDW-CV") instead of "Mcv".
    words = []
    for word in raw_name.split():
        pieces = word.split("-")
        fixed = [
            piece.upper() if piece.lower() in _ACRONYMS else piece.title()
            for piece in pieces
        ]
        words.append("-".join(fixed))
    return " ".join(words)


# Extra spellings that mean the same test. Used ONLY to line up the same test
# across different reports (trend / comparison); stored names are never changed.
_COMPARISON_ALIASES = {
    "total rbc count": "RBC",
    "total red blood cell count": "RBC",
    "total rbc": "RBC",
    "total leucocyte count": "WBC",
    "leucocyte count": "WBC",
    "total wbc count": "WBC",
    "total white blood cell count": "WBC",
    "mean corpuscular volume": "MCV",
    "mean cell volume": "MCV",
    "mean corpuscular hemoglobin": "MCH",
    "mean corpuscular haemoglobin": "MCH",
    "mean cell hemoglobin": "MCH",
    "mean corpuscular hemoglobin concentration": "MCHC",
    "mean corpuscular haemoglobin concentration": "MCHC",
    "mean cell hemoglobin concentration": "MCHC",
    "rdw": "RDW-CV",
    "rdw cv": "RDW-CV",
    "rdwcv": "RDW-CV",
    "hematocrit": "Hematocrit",
    "haematocrit": "Hematocrit",
    "hct": "Hematocrit",
    "pcv": "Hematocrit",
    "packed cell volume": "Hematocrit",
}


def comparison_name(raw_name: str) -> str:
    """Canonical name used to match the same test in different reports.

    "rbc_count", "Total RBC Count" and "RBC" all give "RBC"; "Mean Corpuscular
    Volume" and "MCV" both give "MCV".
    """
    spaced = re.sub(r"\s+", " ", raw_name.replace("_", " ")).strip()
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", spaced).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    alias = _COMPARISON_ALIASES.get(cleaned)
    if alias:
        return alias
    return normalize_parameter_name(spaced)
