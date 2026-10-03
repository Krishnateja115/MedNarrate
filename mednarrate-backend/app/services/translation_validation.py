"""Validate generated translations before persistence; never synthesize content."""

import json
import re
from collections import Counter


SCRIPT_RANGES = {
    "te": (0x0C00, 0x0C7F), "ta": (0x0B80, 0x0BFF),
    "kn": (0x0C80, 0x0CFF), "ml": (0x0D00, 0x0D7F),
    "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F),
    "bn": (0x0980, 0x09FF),
}


def parse_translation(text: str) -> dict:
    """Accept a JSON object, optionally fenced, but reject trailing/partial JSON."""
    raw = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if fence:
        raw = fence.group(1)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Translation must be a JSON object")
    return parsed


def require_script(text: str, language: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Missing translated text")
    low, high = SCRIPT_RANGES[language]
    letters = [c for c in text if c.isalpha()]
    native = sum(low <= ord(c) <= high for c in letters)
    # Medical reports legitimately contain many English-preserved identifiers
    # (test names, units, dosages, dates, abbreviations like WBC/RBC/Hb).
    # These dilute the native-script letter ratio well below 15%, even for
    # a correct translation.  Use a 5 % floor to avoid false rejections while
    # still catching a completely un-translated response.
    if not native or native / max(len(letters), 1) < 0.05:
        raise ValueError("Translation does not use the requested script")


def _numbers(text: str) -> Counter:
    # Do not confuse digits in identifiers (B12, HbA1c) with measurements.
    return Counter(re.findall(r"(?<![\w.])[+-]?\d+(?:[.,]\d+)*(?![\w.])", text))


def preserve_numbers(source: str, translated: str) -> None:
    if _numbers(source) != _numbers(translated):
        raise ValueError("Translation changed numerical facts")


def validate_translation(
    parsed: dict, language: str, summary: str, findings: list,
    medications: list, label_keys: list[str],
) -> dict:
    """Require complete aligned sections, native script and unchanged facts.

    This is a structural/numeric guard, not proof of linguistic equivalence.
    Medical identifiers and dosage fields are copied from the source, not an LLM.
    """
    translated = parsed.get("patient_summary")
    try:
        require_script(translated, language)
    except ValueError as e:
        raise ValueError(f"patient_summary failed: {e}")
    preserve_numbers(summary, translated)
    
    clinician_translated = parsed.get("clinician_summary")
    if clinician_translated:
        try:
            require_script(clinician_translated, language)
        except ValueError as e:
            raise ValueError(f"clinician_summary failed: {e}")
    for item in findings + medications:
        for key in ("unit",):
            fact = str(item.get(key) or "")
            if fact:
                pattern = r"(?<!\w)" + re.escape(fact) + r"(?!\w)"
                count = len(re.findall(pattern, summary))
                if count and len(re.findall(pattern, translated)) != count:
                    raise ValueError("Translation changed a medical identifier or unit")
    labels = parsed.get("ui_labels")
    if not isinstance(labels, dict):
        raise ValueError("Missing translated labels")
    for key in label_keys:
        exempt_keys = {
            "label_high", "label_low", "label_normal", "label_critical", "label_not_classified",
            "chip_blood", "chip_urine", "label_rag_search_index", "label_active_retriever",
            "label_cat_cbc", "label_cat_lipid_panel", "label_cat_liver_function",
            "label_cat_kidney_function", "label_cat_vitamins_&_minerals",
            "label_medical_validation", "label_passed_rules", "label_uncategorized",
            "label_search_parameters"
        }
        if key not in exempt_keys:
            try:
                require_script(labels.get(key), language)
            except ValueError as e:
                raise ValueError(f"Key {key} failed validation: {e}")
    discussion = parsed.get("doctor_discussion_points")
    if not isinstance(discussion, list) or not discussion:
        raise ValueError("Missing discussion points")
    for i, point in enumerate(discussion):
        try:
            require_script(point, language)
        except ValueError as e:
            raise ValueError(f"discussion point {i} failed: {e}")
    # Generated discussion/explanations may repeat facts, but cannot invent numbers.
    allowed_numbers = set(_numbers(summary + " " + json.dumps(findings) + " " + json.dumps(medications)))
    for point in discussion:
        if set(_numbers(point)) - allowed_numbers:
            raise ValueError("Translation invented numerical facts")
    output_findings = parsed.get("abnormal_findings")
    output_meds = parsed.get("medications")
    for source, output, identifier in (
        (findings, output_findings, "test_name"),
        (medications, output_meds, "medication_name"),
    ):
        if not isinstance(output, list) or len(source) != len(output):
            raise ValueError("Translation omitted or added report entries")
        for original, result in zip(source, output):
            if not isinstance(result, dict) or result.get(identifier) != original.get(identifier):
                raise ValueError("Translation changed report identifiers or order")
    for i, (original, result) in enumerate(zip(findings, output_findings)):
        try:
            require_script(result.get("translated_explanation"), language)
        except ValueError as e:
            raise ValueError(f"finding {i} explanation failed: {e}")
        # We intentionally skip require_script for translated_test_name because tests like 'RBC' or 'HbA1c' are frequently preserved in English without translating to native scripts.
        if set(_numbers(result["translated_explanation"])) - allowed_numbers:
            raise ValueError("Translation invented a finding value")
        # Keep structured values available without trusting model copies.
        for key in ("test_name", "translated_test_name", "value", "unit", "ref_low", "ref_high", "flag"):
            if key in original or key in result:
                result[key] = result.get(key) if key == "translated_test_name" else original.get(key)
    for i, (original, result) in enumerate(zip(medications, output_meds)):
        # Skip require_script for medication names because they are frequently preserved in English.
        for key in ("translated_dosage", "translated_frequency", "translated_instructions"):
            if not isinstance(result.get(key), str):
                raise ValueError("Invalid translated medication field")
        # Dosage is a clinical fact, not free-form model output.
        dosage = str(original.get("dosage") or "")
        if result.get("translated_dosage") != dosage:
            raise ValueError("Translation changed medication dosage")
        frequency = str(original.get("frequency") or "")
        if frequency:
            try:
                require_script(result.get("translated_frequency"), language)
            except ValueError as e:
                raise ValueError(f"medication {i} frequency failed: {e}")
            preserve_numbers(frequency, result["translated_frequency"])
        times = result.get("translated_times_of_day")
        source_times = original.get("times_of_day") or []
        if not isinstance(times, list) or len(times) != len(source_times):
            raise ValueError("Translation changed medication timings")
        for before, after in zip(source_times, times):
            if not isinstance(after, str):
                raise ValueError("Invalid medication timing")
            preserve_numbers(str(before), after)
            if re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?", str(before)):
                if before != after:
                    raise ValueError("Translation changed a clock time")
            else:
                require_script(after, language)
        instructions = str(original.get("instructions") or "")
        if instructions:
            require_script(result.get("translated_instructions"), language)
            preserve_numbers(instructions, result["translated_instructions"])
    return parsed
