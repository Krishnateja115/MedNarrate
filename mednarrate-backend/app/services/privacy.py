import re
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def deidentify_prompt_text(text: str, mode: str | None = None) -> str:
    """
    De-identifies report text by redacting direct personal identifiers (Name, MRN, DOB, Phone, Email, Address)
    line by line while preserving all clinical facts, lab names, values, units, reference ranges, and dosages.
    """
    send_mode = (mode or getattr(settings, "LLM_SEND_MODE", "deidentified") or "deidentified").lower().strip()
    if send_mode == "full":
        logger.info("[PRIVACY] LLM_SEND_MODE is 'full'. Text passed without de-identification.")
        return text

    logger.info("[PRIVACY] Applying de-identification boundary to prompt payload.")
    lines = text.splitlines()
    scrubbed_lines = []

    for line in lines:
        scrubbed = line
        scrubbed = re.sub(r'(?i)\b(patient\s*name|name of patient|patient|pt\s*name)\s*:\s*([^\n\r]+)', r'\1: [REDACTED]', scrubbed)
        scrubbed = re.sub(r'(?i)\b(mrn|medical\s*record\s*(?:number|no|\#)|patient\s*id|pt\s*id)\s*:\s*([^\n\r]+)', r'\1: [REDACTED]', scrubbed)
        scrubbed = re.sub(r'(?i)\b(dob|date\s*of\s*birth|birth\s*date)\s*:\s*([^\n\r]+)', r'\1: [REDACTED]', scrubbed)
        scrubbed = re.sub(r'(?i)\b(phone|mobile|cell|tel|contact)\s*:\s*([^\n\r]+)', r'Phone: [REDACTED]', scrubbed)
        scrubbed = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[REDACTED]', scrubbed)
        scrubbed = re.sub(r'(?i)\b(address|residence)\s*:\s*([^\n\r]+)', r'\1: [REDACTED]', scrubbed)
        scrubbed_lines.append(scrubbed)

    return "\n".join(scrubbed_lines)
