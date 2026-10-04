"""Validate generated translations before persistence; never synthesize content."""

import json
import re
import unicodedata
from collections import Counter

SCRIPT_RANGES = {
    "te": (0x0C00, 0x0C7F), "ta": (0x0B80, 0x0BFF),
    "kn": (0x0C80, 0x0CFF), "ml": (0x0D00, 0x0D7F),
    "hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F),
    "bn": (0x0980, 0x09FF), "en": (0x0041, 0x007A),
}

import os
GLOSSARY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "glossary.json")
try:
    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        GLOSSARY = json.load(f).get("terms", {})
except Exception:
    GLOSSARY = {}

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

def normalize_digits(text: str) -> str:
    """Normalize native digits (e.g. Devanagari) to Latin digits."""
    return "".join([str(unicodedata.decimal(c)) if unicodedata.category(c) == "Nd" else c for c in text])

def get_numbers(text: str) -> Counter:
    """Extract all numbers (integers, decimals) after normalizing."""
    norm = normalize_digits(text)
    # Extract strings
    matches = re.findall(r"(?<![\w.])[+-]?\d+(?:[.,]\d+)*(?![\w.])", norm)
    # Parse as floats to treat 40.0 == 40
    floats = []
    for m in matches:
        try:
            floats.append(float(m.replace(',', '.')))
        except ValueError:
            pass
    return Counter(floats)


def validate_translation(*args, **kwargs):
    # Temp stub
    return {}

class TranslationVerifier:
    def __init__(self, language_thresholds=None):
        self.language_thresholds = language_thresholds or {"default": 0.5}

    def verify(self, source: dict, translated: dict, language: str) -> dict:
        self.language = language
        self.failures = []
        
        self._verify_dict(source, translated, path="")
        
        return {
            "ok": len(self.failures) == 0,
            "failures": self.failures
        }

    def _add_failure(self, item_id, field, rule, reason):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "TranslationVerifier FAILURE | language=%s | itemId=%s | field=%s | rule=%s | reason=%s",
            self.language, item_id, field, rule, reason
        )
        self.failures.append({
            "itemId": item_id,
            "field": field,
            "rule": rule,
            "reason": reason
        })

    def _verify_dict(self, source: dict, translated: dict, path: str):
        for k, v_src in source.items():
            if k not in translated:
                self._add_failure(path, k, "structure", f"Missing key {k}")
                continue
            
            v_trn = translated[k]
            current_path = f"{path}.{k}" if path else k
            
            if isinstance(v_src, dict):
                if not isinstance(v_trn, dict):
                    self._add_failure(path, k, "structure", f"Expected dict for {k}")
                else:
                    self._verify_dict(v_src, v_trn, current_path)
            elif isinstance(v_src, list):
                if not isinstance(v_trn, list) or len(v_src) != len(v_trn):
                    self._add_failure(path, k, "structure", f"List length mismatch for {k}")
                else:
                    for i, (item_src, item_trn) in enumerate(zip(v_src, v_trn)):
                        item_path = f"{current_path}[{i}]"
                        if isinstance(item_src, dict) and isinstance(item_trn, dict):
                            self._verify_dict(item_src, item_trn, item_path)
                        elif isinstance(item_src, str) and isinstance(item_trn, str):
                            self._check_string(item_src, item_trn, item_path, k)
            elif isinstance(v_src, str):
                if not isinstance(v_trn, str):
                    self._add_failure(path, k, "structure", f"Expected string for {k}")
                else:
                    self._check_string(v_src, v_trn, path, k)

    def _check_string(self, source_text: str, trans_text: str, item_id: str, field: str):
        # 1. Length Ratio / Truncation Check
        if len(source_text) > 20 and len(trans_text) < len(source_text) * 0.2:
            self._add_failure(item_id, field, "length_ratio", "Translation is suspiciously short")

        # 2. Forbidden Content Check
        forbidden_substrings = ["not verified", "NEEDS_REVIEW", "TODO", "translation:", "as an AI"]
        for f in forbidden_substrings:
            if f.lower() in trans_text.lower():
                self._add_failure(item_id, field, "forbidden_content", f"Found meta text: {f}")
        
        if "```" in trans_text:
            self._add_failure(item_id, field, "forbidden_content", "Found markdown fences")
            
        if re.search(r'\b[a-z]+_[a-z]+\b', trans_text) and field not in ["test_name", "parameter"]:
            self._add_failure(item_id, field, "forbidden_content", "Found raw snake_case keys")
            
        if trans_text.count("[") != trans_text.count("]") or trans_text.count("(") != trans_text.count(")"):
            self._add_failure(item_id, field, "forbidden_content", "Unclosed brackets")

        # Glossary check for lab tests
        if item_id.startswith("abnormal_findings[") and field in ["test_name", "translated_test_name"]:
            # source_text is the English test name, or an ID like 'rbc_count'
            # Look up in glossary by canonicalizing the name
            canonical_id = re.sub(r'[^a-z0-9_]', '_', source_text.lower())
            if canonical_id in GLOSSARY:
                expected_term = GLOSSARY[canonical_id].get(self.language)
                if expected_term and expected_term not in trans_text:
                    self._add_failure(item_id, field, "glossary", f"Expected glossary term: {expected_term}")

        # 3. Numeric Integrity
        src_nums = get_numbers(source_text)
        trn_nums = get_numbers(trans_text)
        if src_nums != trn_nums:
            self._add_failure(item_id, field, "numeric_integrity", "Numbers do not match source")

        # 4. Script Check (for non-English)
        prose_fields = {"clinician_summary", "patient_summary", "explanation", "implication", "instructions", "notes"}
        is_prose = field in prose_fields or item_id.startswith("doctor_discussion_points")
        if is_prose and self.language in SCRIPT_RANGES and self.language != "en":
            low, high = SCRIPT_RANGES[self.language]
            
            # Remove allowlisted tokens like abbreviations, URLs, codes, and units
            # (Very rough proxy: remove words with digits, entirely uppercase words, common units)
            clean_trans = re.sub(r'\b([A-Z0-9]+|mg/dL|g/dL|mEq/L|mmol/L|%|/|cm|mm|kg)\b', '', trans_text, flags=re.IGNORECASE)
            
            native = sum(low <= ord(c) <= high for c in clean_trans if c.isalpha())
            english = sum(0x0041 <= ord(c) <= 0x007A for c in clean_trans if c.isalpha())
            if native + english > 0:
                if native / (native + english) < self.language_thresholds.get(self.language, self.language_thresholds["default"]):
                    self._add_failure(item_id, field, "script_ratio", "Insufficient target script letters in prose")


def require_script(text: str, language: str) -> None:
    from app.exceptions import TranslationServiceError
    verifier = TranslationVerifier()
    if language not in SCRIPT_RANGES or language == "en":
        return
    low, high = SCRIPT_RANGES[language]
    native = sum(low <= ord(c) <= high for c in text if c.isalpha())
    english = sum(0x0041 <= ord(c) <= 0x007A for c in text if c.isalpha())
    if native + english > 0:
        if native / (native + english) < verifier.language_thresholds.get(language, verifier.language_thresholds["default"]):
            raise TranslationServiceError("Insufficient target script letters")

def preserve_numbers(source: str, translated: str) -> None:
    from app.exceptions import TranslationServiceError
    src_nums = get_numbers(source)
    trans_nums = get_numbers(translated)
    for num, count in src_nums.items():
        if trans_nums.get(num, 0) < count:
            raise TranslationServiceError(f"Missing number: {num}")
    for num, count in trans_nums.items():
        if src_nums.get(num, 0) < count:
            raise TranslationServiceError(f"Added number: {num}")

def validate_translation(source_text: str, translated_data: dict, language: str) -> None:
    verifier = TranslationVerifier(source_text, translated_data, language=language)
    errors = verifier.verify()
    if errors:
        from app.exceptions import TranslationServiceError
        raise TranslationServiceError(f"Validation failed: {'; '.join(errors)}")
