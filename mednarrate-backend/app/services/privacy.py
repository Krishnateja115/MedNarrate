import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)


_NAME_LABEL_RE = re.compile(
    r"(?i)^(\s*(?:patient'?s?\s+)?(?:full\s+)?name)\s*[:\-]\s*"
    r"[^\n\r]*?(?=\s{2,}|\s+(?:age|sex|gender|dob|date|uhid|mrn|ref|lab|id)\b|$)"
)
_HOSPITAL_ID_RE = re.compile(
    r"(?i)\b(uhid|reg(?:istration)?\.?\s*(?:no|number|id)|op\s*(?:no|number)|ip\s*(?:no|number))"
    r"\.?\s*[:#\-]\s*[A-Za-z0-9/\-]+"
)
_HONORIFIC_NAME_RE = re.compile(
    r"\b(?:Mr|Mrs|Ms|Miss|Shri|Smt|Dr)\b\.?\s+[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2}"
)
_AADHAAR_RE = re.compile(r"(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\d)")
_IN_PHONE_RE = re.compile(r"(?<![\d.])(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?![\d.])")


def deidentify_prompt_text(text: str, mode: str | None = None) -> str:
    """
    De-identifies report text by redacting direct personal identifiers (Name, MRN, DOB, Phone, Email, Address)
    line by line while preserving all clinical facts, lab names, values, units, reference ranges, and dosages.
    """
    send_mode = (
        (mode or getattr(settings, "LLM_SEND_MODE", "deidentified") or "deidentified")
        .lower()
        .strip()
    )
    if send_mode == "full":
        logger.info(
            "[PRIVACY] LLM_SEND_MODE is 'full'. Text passed without de-identification."
        )
        return text

    logger.info("[PRIVACY] Applying de-identification boundary to prompt payload.")
    lines = text.splitlines()
    scrubbed_lines = []

    for line in lines:
        scrubbed = line
        scrubbed = re.sub(
            r"(?i)\b(patient\s*name|name of patient|patient|pt\s*name)\s*:\s*([^\n\r]+)",
            r"\1: [REDACTED]",
            scrubbed,
        )
        scrubbed = re.sub(
            r"(?i)\b(mrn|medical\s*record\s*(?:number|no|\#)|patient\s*id|pt\s*id)\s*:\s*([^\n\r]+)",
            r"\1: [REDACTED]",
            scrubbed,
        )
        scrubbed = re.sub(
            r"(?i)\b(dob|date\s*of\s*birth|birth\s*date)\s*:\s*([^\n\r]+)",
            r"\1: [REDACTED]",
            scrubbed,
        )
        scrubbed = re.sub(
            r"(?i)\b(phone|mobile|cell|tel|contact)\s*:\s*([^\n\r]+)",
            r"Phone: [REDACTED]",
            scrubbed,
        )
        scrubbed = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "[REDACTED]",
            scrubbed,
        )
        scrubbed = re.sub(
            r"(?i)\b(address|residence)\s*:\s*([^\n\r]+)", r"\1: [REDACTED]", scrubbed
        )
        # Plain "Name : Mr X" label at the START of a line only, so lab-table
        # labels such as "Test Name: Hemoglobin" are preserved. The value stops
        # before the next field label (Age/Sex/...) or a run of 2+ spaces.
        scrubbed = _NAME_LABEL_RE.sub(r"\1: [REDACTED]", scrubbed)
        # Registration / hospital identifiers.
        scrubbed = _HOSPITAL_ID_RE.sub(r"\1: [REDACTED]", scrubbed)
        # Honorific + capitalised name(s): "Mr. Ravi Kumar", "Dr Anita Rao".
        scrubbed = _HONORIFIC_NAME_RE.sub("[REDACTED]", scrubbed)
        # Aadhaar (12 digits in 4-4-4 groups) and Indian mobile numbers.
        scrubbed = _AADHAAR_RE.sub("[REDACTED]", scrubbed)
        scrubbed = _IN_PHONE_RE.sub("[REDACTED]", scrubbed)
        scrubbed_lines.append(scrubbed)

    return "\n".join(scrubbed_lines)
