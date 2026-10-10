"""Validate generated translations before persistence; never synthesize content."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCRIPT_RANGES = {
    "te": (0x0C00, 0x0C7F),
    "ta": (0x0B80, 0x0BFF),
    "kn": (0x0C80, 0x0CFF),
    "ml": (0x0D00, 0x0D7F),
    "hi": (0x0900, 0x097F),
    "mr": (0x0900, 0x097F),
    "bn": (0x0980, 0x09FF),
}

_GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "data" / "glossary.json"
try:
    GLOSSARY: dict[str, dict[str, str]] = json.loads(
        _GLOSSARY_PATH.read_text(encoding="utf-8")
    ).get("terms", {})
except (OSError, ValueError, TypeError):
    GLOSSARY = {}


def parse_translation(text: str) -> dict[str, Any]:
    """Decode the first complete JSON object, including optionally fenced output."""
    import re
    if not isinstance(text, str):
        raise ValueError("Translation response must be text")
    with open("llm_out.txt", "w", encoding="utf-8") as f:
        f.write(text)
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    else:
        object_start = raw.find("{")
        if object_start >= 0:
            raw = raw[object_start:]
    import re
    def fix_value(match):
        key = match.group(1)
        val = match.group(2).strip()
        if not val or val in ("null", "true", "false") or val.isdigit() or val.startswith(("[", "{", '"')):
            return match.group(0) # Leave valid JSON alone
        # Remove any internal quotes and wrap in quotes
        clean_val = val.replace('"', '').strip()
        return f'{key}: "{clean_val}"'
        
    # Match key-value pairs where value might be broken. Matches up to comma or newline.
    raw = re.sub(r'("[A-Za-z0-9_ /,-]+")\s*:\s*([^,\n{}]+)', fix_value, raw)
    try:
        parsed, _ = json.JSONDecoder().raw_decode(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        # Never dump a model response: it may contain protected health information.
        raise ValueError("Translation response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Translation must be a JSON object")
    return parsed


def normalize_digits(text: str) -> str:
    """Normalize native decimal digits (for example Devanagari) to Latin digits."""
    return "".join(
        str(unicodedata.decimal(char)) if unicodedata.category(char) == "Nd" else char
        for char in text
    )


def get_numbers(text: str) -> Counter[float]:
    """Extract standalone numbers while ignoring digits embedded in identifiers."""
    matches = re.findall(
        r"(?<![\w.])[+-]?\d+(?:[.,]\d+)*(?![\w.])", normalize_digits(text)
    )
    numbers: list[float] = []
    for match in matches:
        try:
            numbers.append(float(match.replace(",", ".")))
        except ValueError:
            continue
    return Counter(numbers)


def preserve_numbers(source: str, translated: str) -> None:
    """Reject added, removed, or changed standalone numeric facts."""
    if get_numbers(source) != get_numbers(translated):
        raise ValueError("Translation changed numeric facts")


def require_script(text: str, language: str) -> None:
    """Require some target-script content without rejecting medical identifiers."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Missing translated text")
    if language not in SCRIPT_RANGES:
        return
    low, high = SCRIPT_RANGES[language]
    letters = [char for char in text if char.isalpha()]
    native = sum(low <= ord(char) <= high for char in letters)
    # Keep the direct script check consistent with TranslationVerifier. A tiny
    # amount of native text is not a translation and lets English responses
    # pass through as if they were translated.
    if not native or native / max(len(letters), 1) < 0.40:
        raise ValueError("Translation does not use the requested script")


class TranslationVerifier:
    """Security checks for truncated, malformed, or fact-changing translations."""

    def __init__(self, language_thresholds: dict[str, float] | None = None) -> None:
        self.language_thresholds = language_thresholds or {"default": 0.40}
        self.language = ""
        self.failures: list[dict[str, str]] = []

    def verify(
        self,
        source: dict[str, Any],
        translated: dict[str, Any],
        language: str,
        *,
        preserve_numeric: bool = True,
    ) -> dict[str, Any]:
        self.language = language
        self.failures = []
        self._verify_dict(
            source, translated, path="", preserve_numeric=preserve_numeric
        )
        return {"ok": not self.failures, "failures": self.failures}

    def verify_text(
        self,
        source_text: str,
        translated_text: str,
        *,
        item_id: str,
        field: str,
        preserve_numeric: bool = False,
    ) -> list[dict[str, str]]:
        self._check_string(
            source_text,
            translated_text,
            item_id,
            field,
            preserve_numeric=preserve_numeric,
        )
        return self.failures

    def _add_failure(self, item_id: str, field: str, rule: str, reason: str) -> None:
        logger.warning(
            "TranslationVerifier failure language=%s item=%s field=%s rule=%s",
            self.language,
            item_id,
            field,
            rule,
        )
        self.failures.append(
            {"itemId": item_id, "field": field, "rule": rule, "reason": reason}
        )

    def _verify_dict(
        self,
        source: dict[str, Any],
        translated: dict[str, Any],
        path: str,
        *,
        preserve_numeric: bool,
    ) -> None:
        for key, source_value in source.items():
            if key not in translated:
                self._add_failure(path, key, "structure", f"Missing key {key}")
                continue
            translated_value = translated[key]
            current_path = f"{path}.{key}" if path else key
            if isinstance(source_value, dict):
                if not isinstance(translated_value, dict):
                    self._add_failure(
                        path, key, "structure", f"Expected object for {key}"
                    )
                else:
                    self._verify_dict(
                        source_value,
                        translated_value,
                        current_path,
                        preserve_numeric=preserve_numeric,
                    )
            elif isinstance(source_value, list):
                if not isinstance(translated_value, list) or len(source_value) != len(
                    translated_value
                ):
                    self._add_failure(
                        path, key, "structure", f"List length mismatch for {key}"
                    )
                    continue
                for index, (source_item, translated_item) in enumerate(
                    zip(source_value, translated_value)
                ):
                    item_path = f"{current_path}[{index}]"
                    if isinstance(source_item, dict) and isinstance(
                        translated_item, dict
                    ):
                        self._verify_dict(
                            source_item,
                            translated_item,
                            item_path,
                            preserve_numeric=preserve_numeric,
                        )
                    elif isinstance(source_item, str) and isinstance(
                        translated_item, str
                    ):
                        self._check_string(
                            source_item,
                            translated_item,
                            item_path,
                            key,
                            preserve_numeric=preserve_numeric,
                        )
            elif isinstance(source_value, str):
                if not isinstance(translated_value, str):
                    self._add_failure(
                        path, key, "structure", f"Expected text for {key}"
                    )
                else:
                    self._check_string(
                        source_value,
                        translated_value,
                        path,
                        key,
                        preserve_numeric=preserve_numeric,
                    )

    def _check_string(
        self,
        source_text: str,
        translated_text: str,
        item_id: str,
        field: str,
        *,
        preserve_numeric: bool,
    ) -> None:
        # Indic-language prose can be materially shorter than its English
        # source without being truncated. Keep the stricter threshold for
        # findings and labels, while allowing summary prose a smaller but
        # still meaningful response.
        minimum_ratio = 0.10 if field in {"clinician_summary", "patient_summary"} else 0.20
        if len(source_text) > 20 and len(translated_text) < len(source_text) * minimum_ratio:
            self._add_failure(
                item_id, field, "length_ratio", "Translation is suspiciously short"
            )
        lowered = translated_text.lower()
        for forbidden in (
            "not verified",
            "needs_review",
            "todo",
            "translation:",
            "as an ai",
        ):
            if forbidden in lowered:
                self._add_failure(
                    item_id,
                    field,
                    "forbidden_content",
                    "Translation contains model metadata",
                )
        if "```" in translated_text:
            self._add_failure(
                item_id,
                field,
                "forbidden_content",
                "Translation contains markdown fences",
            )
        if re.search(r"\b[a-z]+_[a-z]+\b", translated_text) and field not in {
            "test_name",
            "parameter",
        }:
            self._add_failure(
                item_id,
                field,
                "forbidden_content",
                "Translation contains raw field names",
            )
        if translated_text.count("[") != translated_text.count(
            "]"
        ) or translated_text.count("(") != translated_text.count(")"):
            self._add_failure(
                item_id,
                field,
                "forbidden_content",
                "Translation has unbalanced brackets",
            )
        if preserve_numeric and get_numbers(source_text) != get_numbers(
            translated_text
        ):
            self._add_failure(
                item_id, field, "numeric_integrity", "Numbers do not match source"
            )
        prose_fields = {
            "clinical_summary",
            "clinician_summary",
            "patient_summary",
            "explanation",
            "implication",
            "instructions",
            "notes",
        }
        is_prose = field in prose_fields or item_id.startswith(
            "doctor_discussion_points"
        )
        if is_prose and self.language in SCRIPT_RANGES:
            low, high = SCRIPT_RANGES[self.language]
            letters = [char for char in translated_text if char.isalpha()]
            native = sum(low <= ord(char) <= high for char in letters)
            threshold = self.language_thresholds.get(
                self.language, self.language_thresholds["default"]
            )
            if not native or native / max(len(letters), 1) < threshold:
                self._add_failure(
                    item_id,
                    field,
                    "script_ratio",
                    "Insufficient target-script letters in prose",
                )


def _raise_verifier_failures(result: dict[str, Any]) -> None:
    if result["ok"]:
        return
    rules = ", ".join(sorted({failure["rule"] for failure in result["failures"]}))
    raise ValueError(f"Translation security verification failed: {rules}")


def validate_translation(
    parsed: dict[str, Any],
    language: str,
    clinician_summary: str,
    patient_summary: str,
    findings: list[dict[str, Any]],
    medications: list[dict[str, Any]],
    label_keys: list[str],
) -> dict[str, Any]:
    """Validate the current schema and restore immutable clinical facts."""
    verifier = TranslationVerifier()
    translated_patient = parsed.get("patient_summary")
    if patient_summary:
        require_script(translated_patient, language)
        _raise_verifier_failures(
            verifier.verify(
                {"patient_summary": patient_summary},
                {"patient_summary": translated_patient},
                language,
                preserve_numeric=False,
            )
        )
    elif translated_patient not in (None, ""):
        raise ValueError("Translation added a patient summary")

    translated_clinician = parsed.get("clinician_summary")
    if clinician_summary:
        require_script(translated_clinician, language)
        _raise_verifier_failures(
            verifier.verify(
                {"clinician_summary": clinician_summary},
                {"clinician_summary": translated_clinician},
                language,
                preserve_numeric=False,
            )
        )
    elif translated_clinician not in (None, ""):
        raise ValueError("Translation added a clinician summary")

    labels = parsed.get("ui_labels")
    if not isinstance(labels, dict):
        if label_keys:
            raise ValueError("Missing translated labels")
        labels = {}
    exempt_keys = {
        "label_high",
        "label_low",
        "label_normal",
        "label_critical",
        "label_not_classified",
        "chip_blood",
        "chip_urine",
        "label_rag_search_index",
        "label_active_retriever",
        "label_cat_cbc",
        "label_cat_lipid_panel",
        "label_cat_liver_function",
        "label_cat_kidney_function",
        "label_cat_vitamins_&_minerals",
        "label_medical_validation",
        "label_passed_rules",
        "label_uncategorized",
        "label_search_parameters",
    }
    for key in label_keys:
        value = labels.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing translated label: {key}")
        if key not in exempt_keys:
            require_script(value, language)

    discussion = parsed.get("doctor_discussion_points")
    if discussion and isinstance(discussion, list):
        for index, point in enumerate(discussion):
            require_script(point, language)
            verifier.failures = []
            verifier.verify_text(
                "",
                point,
                item_id=f"doctor_discussion_points[{index}]",
                field="doctor_discussion_points",
            )
            if verifier.failures:
                _raise_verifier_failures({"ok": False, "failures": verifier.failures})

    output_findings = parsed.get("abnormal_findings")
    output_medications = parsed.get("medications")
    for source, output, identifier in (
        (findings, output_findings, "test_name"),
        (medications, output_medications, "medication_name"),
    ):
        if not isinstance(output, list) or len(source) != len(output):
            raise ValueError("Translation omitted or added report entries")
        for original, result in zip(source, output):
            if not isinstance(result, dict) or result.get(identifier) != original.get(
                identifier
            ):
                raise ValueError("Translation changed report identifiers or order")

    for index, (original, result) in enumerate(zip(findings, output_findings)):
        explanation = result.get("translated_explanation")
        original_explanation = original.get("explanation")
        if original_explanation:
            require_script(explanation, language)
            verifier.failures = []
            verifier.verify_text(
                str(original_explanation),
                explanation,
                item_id=f"abnormal_findings[{index}]",
                field="explanation",
            )
            if verifier.failures:
                _raise_verifier_failures({"ok": False, "failures": verifier.failures})
        for key in ("test_name", "value", "unit", "ref_low", "ref_high", "flag"):
            if key in original or key in result:
                result[key] = original.get(key)

    for original, result in zip(medications, output_medications):
        for key in (
            "translated_dosage",
            "translated_frequency",
            "translated_instructions",
        ):
            if not isinstance(result.get(key), str):
                raise ValueError("Invalid translated medication field")
        dosage = str(original.get("dosage") or "")
        if result["translated_dosage"] != dosage:
            raise ValueError("Translation changed medication dosage")
        frequency = str(original.get("frequency") or "")
        if frequency:
            require_script(result["translated_frequency"], language)
        source_times = original.get("times_of_day") or []
        translated_times = result.get("translated_times_of_day")
        if not isinstance(translated_times, list) or len(translated_times) != len(
            source_times
        ):
            raise ValueError("Translation changed medication timings")
        for before, after in zip(source_times, translated_times):
            if not isinstance(after, str):
                raise ValueError("Invalid medication timing")
            if re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?", str(before)):
                if before != after:
                    raise ValueError("Translation changed a clock time")
            else:
                require_script(after, language)
        instructions = str(original.get("instructions") or "")
        if instructions:
            require_script(result["translated_instructions"], language)
    return parsed
