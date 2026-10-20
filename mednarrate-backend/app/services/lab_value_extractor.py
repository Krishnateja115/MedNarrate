import json
import logging
import re
from typing import List, Optional

from pydantic import BaseModel, ValidationError, field_validator

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
    r"(?P<single><=|>=|[<>≤≥])\s*(?P<bound>[+-]?\d+(?:\.\d+)?))$",
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
    return (bound, None) if match.group("single") in {">", ">=", "≥"} else (None, bound)


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


def _extract_simple_lab_lines(text: str) -> list[dict]:
    """Parse unambiguous one-line results without a remote model call."""
    results: list[dict] = []
    seen: set[tuple[str, float]] = set()
    for match in LAB_LINE_RE.finditer(text):
        name = match.group("name").strip()
        canonical = normalize_parameter_name(name)
        if not (_looks_like_lab_name(name) or KNOWN_LAB_TESTS.search(canonical)):
            continue
        unit = (match.group("unit") or "").strip()
        reference = (match.group("ref_str") or "").strip()
        record = _sanitize_lab_record(
            {
                "test_name": name,
                "original_name": name,
                "value": match.group("value"),
                "unit": unit,
                "original_unit": unit,
                "ref_range_str": reference or None,
                "flag": match.group("flag") or "not_classified",
            }
        )
        if record is None:
            continue
        key = (record["test_name"].lower(), record["value"])
        if key not in seen:
            seen.add(key)
            results.append(record)
    return results


_COLUMN_HEADER_WORDS = {
    "test description", "test", "test name", "result", "results", "ref. range", "ref range",
    "reference range", "reference", "unit", "units", "parameter", "investigation", "value",
    "bio. ref. interval", "biological reference interval", "method", "flag",
}
_GENERIC_UNIT_RE = re.compile(
    r"^(?:%|fl|pg|mm|mmhg|ratio|"
    r"/\s*[A-Za-z0-9\u00b5^]{1,8}|"
    r"[A-Za-z\u00b5]{1,10}\s*/\s*[A-Za-z0-9\u00b5^.]{1,10}|"
    r"(?:million|mil|thousand|thou|lakhs?)\s*/\s*[A-Za-z0-9\u00b5^]{1,8})$",
    re.IGNORECASE,
)
_SECTION_END_RE = re.compile(r"^(?:interpretation|end of report|note|comments?|disclaimer)\b", re.IGNORECASE)
_ROW_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9 /().,'\-]{1,60}?)\s+"
    r"(?P<value>[<>]?\s*\d+(?:\.\d+)?)\s+"
    r"(?P<range>\d+(?:\.\d+)?\s*(?:-|\u2013|to)\s*\d+(?:\.\d+)?|[<>]=?\s*\d+(?:\.\d+)?)\s+"
    r"(?P<unit>\S+(?:\s\S+)?)"
    r"(?:\s+(?P<flag>H|L|HIGH|LOW))?$",
    re.IGNORECASE,
)


def _is_unit_line(value: str) -> bool:
    value = " ".join(value.strip().split())
    if not value or len(value) > 24:
        return False
    return _looks_like_unit(value) or bool(_GENERIC_UNIT_RE.fullmatch(value))


def _is_column_name_candidate(line: str) -> bool:
    cleaned = " ".join(line.split())
    if not cleaned or len(cleaned) > 70 or not re.search(r"[A-Za-z]", cleaned):
        return False
    if cleaned.lower().rstrip(":") in _COLUMN_HEADER_WORDS or cleaned.endswith(":"):
        return False
    if _NUMBER_LINE_RE.fullmatch(cleaned) or _RANGE_RE.fullmatch(cleaned) or _is_unit_line(cleaned):
        return False
    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", cleaned) or ":" in cleaned:
        return False
    return not _is_rejected_name(cleaned)


def _extract_column_layout_table(text: str) -> list[dict]:
    """Parse reports whose cells are stacked as name / result / range / unit.

    Many lab PDFs (react-pdf, LIS exports) extract either as one row per line
    ("Neutrophils 50 40 - 80 %") or as one cell per line. Reference ranges and
    units are read from the report itself so values can be classified.
    """
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    results: list[dict] = []
    seen: set[tuple[str, float]] = set()
    in_table = False
    anchored = 0

    def add(name: str, value: str, ref: Optional[str], unit: str, flag: str = "") -> bool:
        raw_name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip() or name
        record = _sanitize_lab_record(
            {
                "test_name": raw_name,
                "original_name": raw_name,
                "value": float(re.sub(r"[^0-9.+-]", "", value)),
                "unit": unit,
                "original_unit": unit,
                "ref_range_str": ref,
                "flag": {"h": "high", "l": "low"}.get(flag.lower(), flag.lower()) if flag else "",
            }
        )
        if not record:
            return False
        key = (record["test_name"].lower(), record["value"])
        if key in seen:
            return True
        seen.add(key)
        results.append(record)
        return True

    index = 0
    while index < len(lines):
        line = lines[index]
        if _SECTION_END_RE.match(line):
            in_table = False
        row = _ROW_LINE_RE.match(line)
        if row and _is_column_name_candidate(row.group("name")) and _is_unit_line(row.group("unit")):
            if add(row.group("name"), row.group("value"), row.group("range"), row.group("unit"), row.group("flag") or ""):
                in_table = True
                anchored += 1
            index += 1
            continue
        if (
            index + 1 < len(lines)
            and _is_column_name_candidate(line)
            and _NUMBER_LINE_RE.fullmatch(lines[index + 1])
        ):
            cursor = index + 2
            ref = None
            unit = ""
            if cursor < len(lines) and _RANGE_RE.fullmatch(lines[cursor]):
                ref = lines[cursor]
                cursor += 1
            if cursor < len(lines) and _is_unit_line(lines[cursor]):
                unit = lines[cursor]
                cursor += 1
            has_anchor = bool(ref or unit)
            if (has_anchor or in_table) and add(line, lines[index + 1], ref, unit):
                if has_anchor:
                    in_table = True
                    anchored += 1
                index = cursor
                continue
        index += 1
    return results if anchored >= 3 else []


def extract_lab_values_rules(text: str) -> list[dict]:
    """The deterministic (no AI) part of :func:`extract_lab_values`.

    Used by the model evaluation to measure the rule-based parser on its own.
    """
    return (
        _extract_column_layout_table(text)
        or _extract_report_table(text)
        or _extract_simple_lab_lines(text)
    )


async def extract_lab_values(text: str, report_type: str = "blood") -> list[dict]:
    # Skip only for explicit imaging/radiology report types
    rt = (report_type or "").lower().strip()
    if rt in ["radiology", "mri", "xray", "ct", "ultrasound", "imaging"]:
        return []

    # Most laboratory PDFs expose a stable value -> test name -> reference
    # range -> unit layout. Parse that locally first so an LLM cannot shift a
    # unit into the test-name column or turn page/header text into a lab test.
    column_results = _extract_column_layout_table(text)
    if column_results:
        return column_results
    table_results = _extract_report_table(text)
    if table_results:
        return table_results
    line_results = _extract_simple_lab_lines(text)
    if line_results:
        return line_results

    # Privacy boundary: never send raw identifiers to an external LLM.
    from app.services.privacy import deidentify_prompt_text

    text = deidentify_prompt_text(text)

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


_CLOCK_RE = re.compile(
    r"^\s*(\d{1,2})(?:[:.](\d{2}))?(?::\d{2})?\s*([ap])?\.?\s*(?:m\.?)?\s*$",
    re.IGNORECASE,
)


def normalize_clock_time(value: str) -> Optional[str]:
    """Return a clock time as 24-hour ``HH:MM`` or None if it is not one.

    Accepts "08:00", "8:00 AM", "8 pm", "08.30 a.m.", "20:00:00". The mobile
    app schedules alerts from 24-hour HH:MM strings only, so report-extracted
    "08:00 AM" style times must be normalised or no alert would ever fire.
    """
    if not isinstance(value, str):
        return None
    match = _CLOCK_RE.match(value)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = (match.group(3) or "").lower()
    if match.group(2) is None and not meridiem:
        return None  # a bare number ("3") is a count, not a clock time
    if minute > 59:
        return None
    if meridiem:
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if meridiem == "p" else 0)
    elif hour > 23:
        return None
    return f"{hour:02d}:{minute:02d}"


class MedicationScheduleModel(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    times_of_day: List[str] = []
    duration_days: Optional[int] = None
    notes: Optional[str] = None
    provenance: str = "REPORT_EXTRACTED"

    @field_validator("times_of_day", mode="before")
    @classmethod
    def _normalise_times(cls, v):
        if not v:
            return []
        if isinstance(v, str):
            v = [v]
        out: list[str] = []
        for item in v:
            normalised = normalize_clock_time(item)
            # Unparseable free text ("after breakfast") is dropped rather than
            # stored as an alert time that can never be scheduled.
            if normalised and normalised not in out:
                out.append(normalised)
        return out


async def extract_medication_schedule(
    report_text: str,
) -> list[MedicationScheduleModel]:
    from app.services.privacy import deidentify_prompt_text

    report_text = deidentify_prompt_text(report_text)
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
