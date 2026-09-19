import re
import json
import logging
from typing import Optional, List
from pydantic import BaseModel, ValidationError
from app.services.llm_client import generate
from app.services.normalization import normalize_lab_value

logger = logging.getLogger(__name__)

# Known demographic/administrative key patterns to exclude from Lab Results
DEMOGRAPHIC_PATTERNS = re.compile(
    r"\b(date of birth|dob|age|gender|sex|patient|mrn|id|hospital|doctor|physician|phone|address)\b",
    re.IGNORECASE
)

# Known calendar month / date / frequency words to exclude from Lab Results
NON_LAB_KEYWORDS = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|once daily|twice daily|thrice daily|daily|weekly|monthly|time|test-med|tab|tablet|capsule|mg|ml)\b",
    re.IGNORECASE
)

# Recognized lab test name patterns or valid units
KNOWN_LAB_TESTS = re.compile(
    r"\b(hemoglobin|hgb|hb|wbc|rbc|platelets|plt|hematocrit|hct|glucose|fbs|ppbs|hba1c|tsh|t3|t4|cholesterol|hdl|ldl|triglycerides|creatinine|bun|egfr|alt|ast|alp|sgot|sgpt|bilirubin|uric acid|sodium|potassium|chloride|calcium|vitamin|iron|ferritin|protein|albumin)\b",
    re.IGNORECASE
)

VALID_LAB_UNITS = re.compile(
    r"^(g/dl|mg/dl|mmol/l|umol/l|iu/l|u/l|%|pg|fl|g/l|mil/mm3|x10\^3/ul|10\^9/l|uIU/ml|ng/ml|mcg/dl|mEq/L)$",
    re.IGNORECASE
)

LAB_LINE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 /\-\(\)]{2,40}?)"
    r"(?:\s+[:\-]?\s*|[:\-]\s*)"
    r"(?P<value>-?\d+\.?\d*)\s*"
    r"(?P<unit>[^\(\n]*?)\s*"
    r"(?:\(?\s*(?:ref\s*range|reference\s*range|ref|reference|normal)?[:\s]*"
    r"(?P<low>\d+\.?\d*)?\s*[-–~to]*\s*(?P<high>\d+\.?\d*)?\s*\)?)?"
    r"(?:\s*[\(\[]?(?:normal|high|low|critical|abnormal)[\)\]]?)?"
    r"\s*$",
    re.IGNORECASE | re.MULTILINE
)

def classify_entity_category(name: str, unit: str = "") -> str:
    """
    Category-First classification into:
    PatientDemographic, LabResult, Medication, MedicationFrequency, MedicationTiming, Diagnosis, Finding, ReportDate, Other
    """
    name_clean = name.strip()
    unit_clean = unit.strip()

    if DEMOGRAPHIC_PATTERNS.search(name_clean):
        return "PatientDemographic"

    if NON_LAB_KEYWORDS.search(name_clean) and not KNOWN_LAB_TESTS.search(name_clean):
        if any(w in name_clean.lower() for w in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "sep", "sept"]):
            return "ReportDate"
        if any(w in name_clean.lower() for w in ["daily", "weekly", "monthly"]):
            return "MedicationFrequency"
        return "Other"

    return "LabResult"


def extract_lab_values(text: str) -> list[dict]:
    results = []
    for m in LAB_LINE_RE.finditer(text):
        name = m.group("name").strip()
        unit = (m.group("unit") or "").strip()

        # Category-First Check: Ensure entity is genuinely a LabResult
        category = classify_entity_category(name, unit)
        if category != "LabResult":
            logger.debug(f"Skipping non-lab entity '{name}' categorized as {category}")
            continue

        try:
            value = float(m.group("value"))
        except (TypeError, ValueError):
            continue

        low = float(m.group("low")) if m.group("low") else None
        high = float(m.group("high")) if m.group("high") else None

        # Status Hierarchy: Normal, High, Low, Critical, Not Classified
        # Only assign Normal if reference ranges exist and value is within bounds
        flag = "not_classified"
        if low is not None and high is not None:
            if value < low:
                flag = "low"
            elif value > high:
                flag = "high"
            else:
                flag = "normal"
        elif low is not None and value < low:
            flag = "low"
        elif high is not None and value > high:
            flag = "high"

        raw_dict = {
            "test_name": name,
            "value": value,
            "unit": unit,
            "ref_low": low,
            "ref_high": high,
            "flag": flag,
            "category": "LabResult"
        }
        results.append(normalize_lab_value(raw_dict))
    return results


class MedicationScheduleModel(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    times_of_day: List[str] = []
    duration_days: Optional[int] = None
    notes: Optional[str] = None
    provenance: str = "REPORT_EXTRACTED"


async def extract_medication_schedule(report_text: str) -> list[MedicationScheduleModel]:
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

