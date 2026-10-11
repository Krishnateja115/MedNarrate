"""Find literal source lines for extracted lab values; never invent citations."""

import re
from typing import Any


_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")


def build_lab_evidence_sources(
    source_text: str, labs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Attach only lines that visibly contain the lab name and measured value.

    OCR text has no reliable page mapping, so these are excerpts rather than
    page-number claims. Users should still inspect the original document.
    """
    lines = [" ".join(line.split()) for line in source_text.splitlines()]
    evidence: list[dict[str, Any]] = []
    for lab in labs:
        names = {
            str(lab.get("test_name") or "").casefold().strip(),
            str(lab.get("original_name") or "").casefold().strip(),
        }
        names.discard("")
        try:
            value = float(lab["value"])
        except (KeyError, TypeError, ValueError):
            continue

        matches: list[str] = []
        for line in lines:
            if not line or not any(name in line.casefold() for name in names):
                continue
            numbers = [float(match.group()) for match in _NUMBER.finditer(line)]
            if value not in numbers:
                continue
            matches.append(line[:300])
            if len(matches) == 2:
                break
        if matches:
            evidence.append(
                {
                    "finding": str(lab.get("test_name") or ""),
                    "chunk_ids": [],
                    "sources": matches,
                }
            )
    return evidence
