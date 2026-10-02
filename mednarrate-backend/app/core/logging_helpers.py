import re

def redact_secrets(text: str) -> str:
    """Redacts sensitive credentials like DATABASE_URL, API keys, etc."""
    if not isinstance(text, str):
        text = str(text)

    # Redact PostgreSQL/SQLite URLs
    text = re.sub(
        r"([a-zA-Z0-9+]+://)([^@\s]+)@([^/\s]+)(/[^\s]*)?",
        r"\1[REDACTED_CREDENTIALS]@[REDACTED_HOST]\4",
        text
    )

    # Redact common key patterns
    text = re.sub(r"(?i)(api_key|token|secret|password|bearer|jwt)[\s:=]+[\"']?([a-zA-Z0-9_\-\.]{12,})[\"']?", r"\1: [REDACTED]", text)

    return text
