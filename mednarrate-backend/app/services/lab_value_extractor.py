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
    r"date|collection|referred|report id|pathology|signature|interpretation)\b",
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


def extract_lab_values(text: str, report_type: str = "blood") -> list[dict]:
    # Skip only for explicit imaging/radiology report types
    rt = (report_type or "").lower().strip()
    if rt in ["radiology", "mri", "xray", "ct", "ultrasound", "imaging"]:
        return []

    results = []
    for m in LAB_LINE_RE.finditer(text):
        name = m.group("name").strip()
        unit = (m.group("unit") or "").strip()

        if len(name) <= 2 and name.lower() not in VALID_SHORT_NAMES:
            logger.debug("Skipping implausibly short candidate name.")
            continue

        raw_matched_segment = m.group(0)
        name_start = m.start("name") - m.start(0)
        name_end_idx = name_start + len(m.group("name"))
        value_start_idx = m.start("value") - m.start(0)
        between = raw_matched_segment[name_end_idx:value_start_idx]
        if between.strip() == "" and between == "":
            logger.debug(
                "Skipping candidate — name and value are glued together with no separator, looks like an ID code."
            )
            continue

        # Category-First Check: Ensure entity is genuinely a LabResult
        category = classify_entity_category(name, unit)
        if category != "LabResult":
            logger.debug(f"Skipping non-lab entity categorized as {category}")
            continue

        # Known-non-lab name guard: reject specific recurring metadata rows
        # observed in real reports that survive the regex and category filters.
        if name.strip().lower() in KNOWN_NON_LAB_NAMES:
            logger.debug("Skipping known non-lab row.")
            continue

        # Date-unit fragment guard: reject rows whose unit looks like a date/time
        # fragment (e.g. value=24, unit='/06/2023 08:49 PM') from date table rows.
        if re.search(r"\d{4}|\bam\b|\bpm\b|/\d{2}/", unit, re.IGNORECASE):
            logger.debug("Skipping row — unit field looks like a date/time fragment.")
            continue

        # Ambiguous PCT guard: only skip PCT when its unit is clearly not a
        # hematology unit — catches the table-column-merge bug where the
        # next row's name ('MPV') leaks into PCT's unit field.
        if (
            name.strip().lower() == "pct"
            and unit.strip()
            and not re.match(r"^(%|fl|pg|g/dl|mg/dl)?$", unit.strip(), re.IGNORECASE)
        ):
            logger.debug("Skipping ambiguous 'PCT' row with implausible unit.")
            continue

        try:
            value = float(m.group("value"))
        except (TypeError, ValueError):
            continue

        ref_str = m.group("ref_str")
        ref_unit = (m.group("ref_unit") or "").strip()
        target_unit = ref_unit if ref_unit else unit

        low = None
        high = None
        formatted_ref_str = None

        if ref_str:
            ref_clean = ref_str.strip()
            if (
                "-" in ref_clean
                or "–" in ref_clean
                or "~" in ref_clean
                or " to " in ref_clean.lower()
            ):
                parts = re.split(r"[\-–~]|\bto\b", ref_clean, flags=re.IGNORECASE)
                if len(parts) == 2:
                    try:
                        low = float(parts[0].strip())
                        high = float(parts[1].strip())
                        formatted_ref_str = f"{parts[0].strip()} - {parts[1].strip()} {target_unit}".strip()
                    except ValueError:
                        pass
            elif ref_clean.startswith("<=") or ref_clean.startswith("<"):
                val_str = ref_clean.replace("<=", "").replace("<", "").strip()
                try:
                    high = float(val_str)
                    op = "<=" if ref_clean.startswith("<=") else "<"
                    formatted_ref_str = f"{op} {val_str} {target_unit}".strip()
                except ValueError:
                    pass
            elif ref_clean.startswith(">=") or ref_clean.startswith(">"):
                val_str = ref_clean.replace(">=", "").replace(">", "").strip()
                try:
                    low = float(val_str)
                    op = ">=" if ref_clean.startswith(">=") else ">"
                    formatted_ref_str = f"{op} {val_str} {target_unit}".strip()
                except ValueError:
                    pass

        explicit_flag = (m.group("flag") or "").lower().strip()
        if explicit_flag in ["low", "high", "normal", "critical", "abnormal"]:
            flag = explicit_flag
        elif low is not None and high is not None:
            if value < low:
                flag = "low"
            elif value > high:
                flag = "high"
            else:
                flag = "normal"
        elif low is not None:
            if value < low:
                flag = "low"
            else:
                flag = "normal"
        elif high is not None:
            if value > high:
                flag = "high"
            else:
                flag = "normal"
        else:
            flag = "not_classified"

        raw_dict = {
            "test_name": name,
            "value": value,
            "unit": unit,
            "ref_low": low,
            "ref_high": high,
            "flag": flag,
            "ref_range_str": formatted_ref_str,
            "category": "LabResult",
        }
        results.append(normalize_lab_value(raw_dict))

    seen = set()
    deduped_results = []
    for r in results:
        key = (r["test_name"].strip().lower(), r["value"])
        if key in seen:
            continue
        seen.add(key)
        deduped_results.append(r)
    return deduped_results


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
