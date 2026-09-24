import logging
import re
from datetime import date, datetime

logger = logging.getLogger(__name__)

# Patterns for explicit report/test/specimen dates (excluding DOB)
REPORT_DATE_PATTERNS = [
    re.compile(
        r"(?:report|specimen|collection|test|examination|draw)\s*date\s*[:\-]?\s*(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:report|specimen|collection|test|examination|draw)\s*date\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:report|specimen|collection|test|examination|draw)\s*date\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"date\s*of\s*(?:report|specimen|collection|test|service)\s*[:\-]?\s*(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})",
        re.IGNORECASE,
    ),
    re.compile(
        r"date\s*of\s*(?:report|specimen|collection|test|service)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        re.IGNORECASE,
    ),
]


def extract_report_date(text: str, fallback_date: date) -> date:
    """
    Extracts an explicit report/specimen date from medical text.
    Strictly avoids patient Date of Birth (DOB).
    Returns fallback_date if no explicit report date is identified.
    """
    if not text:
        return fallback_date

    # Filter out DOB lines first
    lines = [
        line
        for line in text.splitlines()
        if not re.search(r"\b(?:dob|birth)\b", line, re.IGNORECASE)
    ]
    filtered_text = "\n".join(lines)

    for pattern in REPORT_DATE_PATTERNS:
        match = pattern.search(filtered_text)
        if match:
            date_str = match.group(1).strip()
            parsed = _parse_date_string(date_str)
            if parsed:
                logger.info(f"Extracted explicit report date from text: {parsed}")
                return parsed

    return fallback_date


def _parse_date_string(date_str: str) -> date | None:
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None
