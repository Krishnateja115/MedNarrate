import json
import logging
import re
from typing import List, Optional

from pydantic import BaseModel, ValidationError

from app.services.normalization import normalize_lab_value
from app.services.lab_value_normalizer import normalize_parameter_name

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

_UNIT_RE = re.compile(
    r"^(?:g\s*/\s*d[lL]|gm\s*/\s*d[lL]|mg\s*/\s*d[lL]|mmol\s*/\s*[lL]|"
    r"umol\s*/\s*[lL]|nmol\s*/\s*[lL]|mEq\s*/\s*[lL]|U\s*/\s*[lL]|IU\s*/\s*[lL]|"
    r"µ?IU\s*/\s*m[lL]|ng\s*/\s*m[lL]|pg(?:\s*/\s*[lL])?|f[lL]|%|"
    r"(?:x\s*)?10\s*\^?\s*\d+\s*/\s*(?:uL|mm3|l)|"
    r"(?:mill|mil|thou)\s*/\s*mm3|mL\s*/\s*min\s*/\s*1\.73m2)$",
    re.IGNORECASE,
)
_NUMBER_LINE_RE = re.compile(r"^[<>≤≥]?\s*[+-]?\d+(?:\.\d+)?$")
_RANGE_RE = re.compile(
    r"^(?:(?P<low>[<>≤≥]?\s*[+-]?\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
    r"(?P<high>[<>≤≥]?\s*[+-]?\d+(?:\.\d+)?)|"
    r"(?P<single>[<>≤≥])\s*(?P<bound>[+-]?\d+(?:\.\d+)?))$",
    re.IGNORECASE,
)
_NON_LAB_NAMES = {
    "test report",
    "test name",
    "results",
    "units",
    "bio. ref. interval",
    "note",
    "interpretation",
    "page",
    "page 1 of",
    "page 2 of",
    "page 3 of",
    "page 4 of",
    "page 5 of",
    "page 6 of",
    "page 7 of",
}
_LAB_NAME_HINTS = {
    "albumin", "alkaline phosphatase", "ast", "alt", "ggtp", "bilirubin total",
    "bilirubin direct", "bilirubin indirect", "calcium total", "chloride",
    "cholesterol total", "creatinine", "estimated average glucose", "ferritin",
    "gfr estimated", "glucose fasting", "globulin calculated", "hba1c", "hdl cholesterol",
    "hemoglobin", "mch", "mchc", "mcv", "non-hdl cholesterol", "phosphorus",
    "platelet count", "potassium", "rbc count", "red cell distribution width",
    "segmented neutrophils", "sodium", "t3 total", "t4 total", "total leukocyte count",
    "total protein", "triglycerides", "tsh", "urea", "urea nitrogen blood", "uric acid",
    "vitamin b12 cyanocobalamin", "vitamin d 25 hydroxy", "vldl cholesterol",
    "a : g ratio", "bun creatinine ratio", "lymphocytes", "monocytes", "eosinophils",
    "basophils", "neutrophils", "packed cell volume", "absolute leucocyte count",
}


def _looks_like_unit(value: str) -> bool:
    return bool(value and _UNIT_RE.fullmatch(value.strip()))


def _parse_range(value: str) -> tuple[Optional[float], Optional[float]]:
    match = _RANGE_RE.fullmatch(" ".join(value.strip().split()))
    if not match:
        return None, None
    if match.group("low") and match.group("high"):
        return float(re.sub(r"[^0-9.+-]", "", match.group("low"))), float(
            re.sub(r"[^0-9.+-]", "", match.group("high"))
        )
    bound = float(match.group("bound"))
    return (bound, None) if match.group("single") in {">", "≥"} else (None, bound)


def _classify_value(value: float, ref_low: Optional[float], ref_high: Optional[float], explicit: str = "") -> str:
    flag = (explicit or "").strip().lower()
    if flag in {"normal", "low", "high", "critical"}:
        return flag
    if ref_low is not None and value < ref_low:
        return "low"
    if ref_high is not None and value > ref_high:
        return "high"
    if ref_low is not None or ref_high is not None:
        return "normal"
    return "not_classified"


def _is_rejected_name(name: str) -> bool:
    cleaned = " ".join(name.strip().split())
    lowered = cleaned.lower()
    if not cleaned or lowered in _NON_LAB_NAMES or _looks_like_unit(cleaned):
        return True
    if re.fullmatch(r"page\s+\d+\s+of", lowered):
        return True
    if lowered.startswith(("delhi ", "lpl-", "national reference", "report status", "a new test")):
        return True
    if DEMOGRAPHIC_PATTERNS.search(cleaned) and not KNOWN_LAB_TESTS.search(cleaned):
        return True
    return False


def _sanitize_lab_record(raw_dict: dict) -> Optional[dict]:
    if not isinstance(raw_dict, dict):
        return None
    name = str(raw_dict.get("test_name") or raw_dict.get("parameter") or raw_dict.get("name") or "").strip()
    unit = str(raw_dict.get("unit") or "").strip()
    original_name = str(raw_dict.get("original_name") or name).strip()
    original_unit = str(raw_dict.get("original_unit") or unit).strip()

    # Some model responses shift the table columns by one position. Repair the
    # common cases before validation: U/L + ALT becomes ALT + U/L, etc.
    if _looks_like_unit(name) and unit and not _looks_like_unit(unit):
        name, unit = unit, name
        original_name, original_unit = name, unit
    elif _looks_like_unit(name) and not unit and _looks_like_unit(original_unit):
        name, unit = original_name, name
    if _is_rejected_name(name):
        return None

    try:
        numeric_value = float(raw_dict.get("value"))
    except (TypeError, ValueError):
        return None

    ref_low = raw_dict.get("ref_low")
    ref_high = raw_dict.get("ref_high")
    try:
        ref_low = float(ref_low) if ref_low is not None else None
        ref_high = float(ref_high) if ref_high is not None else None
    except (TypeError, ValueError):
        ref_low, ref_high = None, None
    ref_range = str(raw_dict.get("ref_range_str") or "").strip() or None
    if ref_range and ref_low is None and ref_high is None:
        ref_low, ref_high = _parse_range(ref_range)

    canonical_name = normalize_parameter_name(name)
    normalized = normalize_lab_value(
        {
            **raw_dict,
            "test_name": canonical_name,
            "original_name": original_name or name,
            "unit": unit,
            "original_unit": original_unit or unit,
            "value": numeric_value,
            "ref_low": ref_low,
            "ref_high": ref_high,
            "flag": _classify_value(numeric_value, ref_low, ref_high, str(raw_dict.get("flag") or "")),
        }
    )
    normalized["test_name"] = canonical_name
    normalized["original_name"] = original_name or name
    normalized["unit"] = normalized.get("unit", unit)
    normalized["original_unit"] = original_unit or unit
    normalized["ref_low"] = ref_low
    normalized["ref_high"] = ref_high
    normalized["flag"] = _classify_value(numeric_value, ref_low, ref_high, str(raw_dict.get("flag") or ""))
    normalized["category"] = "LabResult"
    return normalized


def _looks_like_lab_name(line: str) -> bool:
    cleaned = " ".join(line.strip().split())
    base_name = re.sub(r"\s*\([^)]*\)\s*$", "", cleaned).strip()
    lowered = re.sub(r"[^a-z0-9]+", " ", base_name.lower()).strip()
    if _is_rejected_name(cleaned) or len(cleaned) > 80:
        return False
    return lowered in _LAB_NAME_HINTS or bool(KNOWN_LAB_TESTS.search(cleaned))


def _extract_report_table(text: str) -> list[dict]:
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    results: list[dict] = []
    seen: set[tuple[str, float]] = set()
    name_first_start = next(
        (i for i, line in enumerate(lines) if "complete blood count" in line.lower()),
        len(lines),
    )
    for index, line in enumerate(lines):
        value_match = re.fullmatch(r"([<>≤≥]?\s*[+-]?\d+(?:\.\d+)?)", line)
        if not value_match or index + 1 >= len(lines) or (index > 0 and _RANGE_RE.fullmatch(lines[index - 1])):
            continue
        candidate = lines[index + 1]
        if not _looks_like_lab_name(candidate):
            continue
        if index >= name_first_start or candidate.lower() == "estimated average glucose (eag)":
            continue
        raw_name = re.sub(r"\s*\([^)]*\)\s*$", "", candidate).strip()
        ref_low = ref_high = None
        ref_range = None
        unit = ""
        for offset, following in enumerate(lines[index + 2 : index + 8], start=2):
            if _NUMBER_LINE_RE.fullmatch(following) and index + offset + 1 < len(lines):
                if _looks_like_lab_name(lines[index + offset + 1]):
                    break
            if _looks_like_unit(following):
                unit = following
            elif _RANGE_RE.fullmatch(following):
                ref_range = following
                ref_low, ref_high = _parse_range(following)
            elif following.startswith("("):
                continue
            elif following.lower() in {"test report", "sample report"}:
                break
        numeric = float(re.sub(r"[^0-9.+-]", "", value_match.group(1)))
        record = _sanitize_lab_record(
            {
                "test_name": raw_name,
                "original_name": raw_name,
                "value": numeric,
                "unit": unit,
                "original_unit": unit,
                "ref_low": ref_low,
                "ref_high": ref_high,
                "ref_range_str": ref_range,
            }
        )
        if record:
            key = (record["test_name"].lower(), record["value"])
            if key not in seen:
                seen.add(key)
                results.append(record)

    # A few report sections use the opposite order: test name, method, unit,
    # measured value. Parse that layout as a second pass.
    for index, candidate in enumerate(lines):
        if not _looks_like_lab_name(candidate):
            continue
        if index < name_first_start and candidate.lower() not in {"estimated average glucose (eag)", "hba1c"}:
            continue
        ref_low = ref_high = None
        ref_range = None
        if index > 0 and _RANGE_RE.fullmatch(lines[index - 1]):
            ref_range = lines[index - 1]
            ref_low, ref_high = _parse_range(ref_range)
        unit = ""
        measured: Optional[float] = None
        for offset, following in enumerate(lines[index + 1 : index + 8], start=1):
            if _RANGE_RE.fullmatch(following):
                ref_range = following
                ref_low, ref_high = _parse_range(following)
            elif _NUMBER_LINE_RE.fullmatch(following):
                if not (unit or ref_range) and index + offset + 1 < len(lines) and _looks_like_lab_name(lines[index + offset + 1]):
                    break
                measured = float(re.sub(r"[^0-9.+-]", "", following))
                break
            elif _looks_like_unit(following):
                unit = following
            elif following.startswith("("):
                continue
            elif offset > 1 and _looks_like_lab_name(following):
                break
        if measured is None:
            continue
        raw_name = re.sub(r"\s*\([^)]*\)\s*$", "", candidate).strip()
        record = _sanitize_lab_record(
            {
                "test_name": raw_name,
                "original_name": raw_name,
                "value": measured,
                "unit": unit,
                "original_unit": unit,
                "ref_low": ref_low,
                "ref_high": ref_high,
                "ref_range_str": ref_range,
            }
        )
        if record:
            key = (record["test_name"].lower(), record["value"])
            if key not in seen:
                seen.add(key)
                results.append(record)
    return results


async def extract_lab_values(text: str, report_type: str = "blood") -> list[dict]:
    # Skip only for explicit imaging/radiology report types
    rt = (report_type or "").lower().strip()
    if rt in ["radiology", "mri", "xray", "ct", "ultrasound", "imaging"]:
        return []

    # Most laboratory PDFs expose a stable value -> test name -> reference
    # range -> unit layout. Parse that locally first so an LLM cannot shift a
    # unit into the test-name column or turn page/header text into a lab test.
    table_results = _extract_report_table(text)
    if table_results:
        return table_results

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

        if isinstance(response, (list, dict)):
            data = response
        else:
            data = json.loads(response)
        if isinstance(data, dict):
            data = data.get("lab_results") or data.get("results") or []
        
        results = []
        seen = set()
        for raw_dict in data:
            norm = _sanitize_lab_record(raw_dict)
            if norm is None:
                continue
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
