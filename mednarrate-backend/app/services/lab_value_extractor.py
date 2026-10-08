import json
import logging
import re
from typing import List, Optional

from pydantic import BaseModel, ValidationError

from app.services.normalization import normalize_lab_value

logger = logging.getLogger(__name__)

# Known demographic/administrative key patterns to exclude from Lab Results
# Includes bare 'date', 'collection', 'referred', 'pathology', etc. observed as
# non-lab table rows in real CBC/blood reports that slip through the numeric regex.
DEMOGRAPHIC_PATTERNS = re.compile(
    r"\b(date of birth|dob|age|gender|sex|patient|mrn|id|hospital|doctor|physician|phone|address|"
    r"date|collection|referred|report id|pathology|signature|interpretation|male|female|years|yrs|months)\b",
    re.IGNORECASE,
)

# Known names of non-lab rows that survive all other filters, captured verbatim
# from real report PDFs. Only block exact name matches to avoid over-filtering.
KNOWN_NON_LAB_NAMES = frozenset(
    {
        "md pathology",
        "collection date",
        "report date",
        "report id",
        "referred by",
        "lab signature",
        "lab interpretation",
    }
)

# Known calendar month / date / frequency words to exclude from Lab Results
NON_LAB_KEYWORDS = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|once daily|twice daily|thrice daily|daily|weekly|monthly|time|test-med|tab|tablet|capsule|mg|ml)\b",
    re.IGNORECASE,
)

# Recognized lab test name patterns or valid units
KNOWN_LAB_TESTS = re.compile(
    r"\b(hemoglobin|hgb|hb|wbc|rbc|platelets|plt|hematocrit|hct|glucose|fbs|ppbs|hba1c|tsh|t3|t4|cholesterol|hdl|ldl|triglycerides|creatinine|bun|egfr|alt|ast|alp|sgot|sgpt|bilirubin|uric acid|sodium|potassium|chloride|calcium|vitamin|iron|ferritin|protein|albumin)\b",
    re.IGNORECASE,
)

VALID_LAB_UNITS = re.compile(
    r"^(g/dl|mg/dl|mmol/l|umol/l|iu/l|u/l|%|pg|fl|g/l|mil/mm3|x10\^3/ul|10\^9/l|uIU/ml|ng/ml|mcg/dl|mEq/L)$",
    re.IGNORECASE,
)

LAB_LINE_RE = re.compile(
    r"^[ \t]*(?P<name>[A-Za-z][A-Za-z0-9 /\-\(\)\.]{1,40}?)"
    r"\s*[:\-]?\s*"
    r"(?P<value>-?\d+\.?\d*)\s*"
    r"(?P<unit>(?:x[ \t]*)?\d*\^?\d*[A-Za-z\^/%µ][A-Za-z0-9\^/%µ]*(?:/[A-Za-z0-9]+)?)*\s*"
    r"(?:\(?\s*(?:ref\s*range|reference\s*range|ref|reference|normal)?[:\s]*"
    r"(?P<ref_str>(?:<=?|>=?|<|>)\s*\d+\.?\d*|\d+\.?\d*\s*(?:[\-–~]|\bto\b)\s*\d+\.?\d*)\s*(?P<ref_unit>(?:x[ \t]*)?\d*\^?\d*[A-Za-z\^/%µ][A-Za-z0-9\^/%µ]*(?:/[A-Za-z0-9]+)?)?\s*\)?)?"
    r"\s*(?:\([^)]*\))?"  # swallow any trailing non-numeric parenthesised group (e.g. "( - )")
    r"\s*(?:(?:\[|\()*(?P<flag>LOW|HIGH|NORMAL|CRITICAL|ABNORMAL)(?:\]|\))*)?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def classify_entity_category(name: str, unit: str = "") -> str:
    """
    Category-First classification into:
    PatientDemographic, LabResult, Medication, MedicationFrequency, MedicationTiming, Diagnosis, Finding, ReportDate, Other
    """
    name_clean = name.strip()
    unit.strip()

    if DEMOGRAPHIC_PATTERNS.search(name_clean):
        return "PatientDemographic"

    if NON_LAB_KEYWORDS.search(name_clean) and not KNOWN_LAB_TESTS.search(name_clean):
        if any(
            w in name_clean.lower()
            for w in [
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "august",
                "september",
                "october",
                "november",
                "december",
                "sep",
                "sept",
            ]
        ):
            return "ReportDate"
        if any(w in name_clean.lower() for w in ["daily", "weekly", "monthly"]):
            return "MedicationFrequency"
        return "Other"

    return "LabResult"


VALID_SHORT_NAMES = frozenset({"ph"})


async def extract_lab_values(text: str, report_type: str = "blood") -> list[dict]:
    # Skip only for explicit imaging/radiology report types
    rt = (report_type or "").lower().strip()
    if rt in ["radiology", "mri", "xray", "ct", "ultrasound", "imaging"]:
        return []

    prompt = f"""From the following medical report text, extract all laboratory test results.
The parser must strictly follow these rules:
1. Correctly handle common laboratory formats (e.g., ALT 40 U/L) and table-style formats.
2. Reconstruct split entries (e.g., ALT on one line, 40 on next, U/L on next).
3. Detect when a unit appears before or after the value.
4. Detect values embedded in strings (e.g., 40 ALT, ALT 40, ALT: 40 U/L).
5. Prevent location names, hospital names, lab names, addresses, dates, and patient identifiers from becoming test names.
6. A unit-only name (like U/L or %) is invalid as a test name. Treat unit-only tokens as units.
7. Preserve decimal values exactly. Do not round.
8. Preserve negative values, ranges, <, >, <=, and >= when they are part of the source report.
9. Extract reference ranges without confusing them with measured values.
10. Calculate 'normal', 'high', 'low', or 'critical' flag ONLY when a valid reference range is available. Use 'not_classified' if no reference range exists and the flag is not explicitly stated in the text.
11. Keep test identifiers and medical abbreviations intact (e.g., ALT, AST, WBC).
12. Do not infer a diagnosis from an isolated result.

Return ONLY a valid JSON array of objects. For each lab result, extract:
- test_name: (string) The name of the test.
- value: (float) The measured numeric value.
- unit: (string) The unit of measurement (empty string if none).
- ref_low: (float or null) The lower bound of the reference range, if available.
- ref_high: (float or null) The upper bound of the reference range, if available.
- ref_range_str: (string or null) The original reference range string (e.g., "12 - 16 g/dL").
- flag: (string) "normal", "high", "low", "critical", "abnormal", or "not_classified".
- category: (string) Always "LabResult".

Report text:
{text}
"""
    try:
        from app.services.llm_orchestrator import extract_structured_json
        response = await extract_structured_json(prompt)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        data = json.loads(response)
        
        results = []
        seen = set()
        for raw_dict in data:
            # Enforce non-empty test name and non-unit test name
            test_name = raw_dict.get("test_name", "").strip()
            if not test_name:
                continue
            if test_name.lower() in ["g/dl", "mg/dl", "mmol/l", "umol/l", "iu/l", "u/l", "%", "pg", "fl", "g/l", "mil/mm3", "x10^3/ul", "10^9/l", "uiu/ml", "ng/ml", "mcg/dl", "meq/l"]:
                continue
                
            norm = normalize_lab_value(raw_dict)
            key = (norm["test_name"].strip().lower(), norm["value"])
            if key not in seen:
                seen.add(key)
                results.append(norm)
                
        return results
    except Exception as e:
        logger.error(f"Failed to extract lab values via LLM: {e}")
        return []


class MedicationScheduleModel(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    times_of_day: List[str] = []
    duration_days: Optional[int] = None
    notes: Optional[str] = None
    provenance: str = "REPORT_EXTRACTED"


async def extract_medication_schedule(
    report_text: str,
) -> list[MedicationScheduleModel]:
    prompt = f"""From the following medical report text, extract all prescribed or current medications mentioned.
For each medication, extract:
- medication_name: exact medication name
- dosage: e.g. "500 mg", "5 mg" (null if not mentioned)
- frequency: e.g. "once daily", "twice daily" (null if not mentioned)
- times_of_day: list of exact specific times explicitly mentioned in the text (e.g. ["08:00 AM"]). DO NOT fabricate or invent timestamps if not explicitly written in the report. If no explicit clock times are in the text, return [].
- duration_days: integer duration in days if explicitly mentioned, else null
- notes: special instructions if mentioned (e.g. "take with food")

Return ONLY a valid JSON array of objects. If no medications are found, return [].
Report text: {report_text}"""

    try:
        from app.services.llm_orchestrator import extract_structured_json

        response = await extract_structured_json(prompt)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        data = json.loads(response)

        schedules = []
        for item in data:
            try:
                if "duration" in item and "duration_days" not in item:
                    item["duration_days"] = item["duration"]
                item["provenance"] = "REPORT_EXTRACTED"
                schedules.append(MedicationScheduleModel(**item))
            except ValidationError:
                continue

        return schedules
    except Exception as e:
        logger.error(f"Failed to extract medications: {e}")
        return []
