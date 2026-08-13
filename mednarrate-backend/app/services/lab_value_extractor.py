import re

LAB_LINE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 /\-\(\)]{2,40}?)"
    r"(?:\s+[:\-]?\s*|[:\-]\s*)"
    r"(?P<value>-?\d+\.?\d*)\s*"
    r"(?P<unit>.*?)\s*"
    r"(?:\(?\s*(?:ref|reference|normal)?[:\s]*"
    r"(?P<low>\d+\.?\d*)\s*[-–~to]+\s*(?P<high>\d+\.?\d*)\s*\)?)?\s*$",
    re.IGNORECASE | re.MULTILINE
)

from app.services.normalization import normalize_lab_value

def extract_lab_values(text: str) -> list[dict]:
    results = []
    for m in LAB_LINE_RE.finditer(text):
        name = m.group("name").strip()
        try:
            value = float(m.group("value"))
        except (TypeError, ValueError):
            continue
        low = float(m.group("low")) if m.group("low") else None
        high = float(m.group("high")) if m.group("high") else None
        flag = "normal"
        if low is not None and value < low:
            flag = "low"
        elif high is not None and value > high:
            flag = "high"
        raw_dict = {
            "test_name": name, "value": value, "unit": m.group("unit") or "",
            "ref_low": low, "ref_high": high, "flag": flag,
        }
        results.append(normalize_lab_value(raw_dict))
    return results
