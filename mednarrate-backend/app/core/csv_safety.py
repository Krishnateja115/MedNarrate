"""Neutralise spreadsheet formula injection in CSV exports.

Cells that begin with ``= + - @`` (or a tab / carriage return) are executed as
formulas by Excel / Sheets / LibreOffice. Values here come from user-controlled
text (ticket subjects, names, OCR'd lab names), so prefix a single quote.
Plain negative numbers (``-5``, ``-0.3``) are left intact.
"""

from __future__ import annotations

from typing import Any

_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    if value[0] in _DANGEROUS:
        try:
            float(value)
            return value  # a real number such as "-5" or "+1.5"
        except ValueError:
            return "'" + value
    return value


def csv_safe_row(row) -> list:
    return [csv_safe(v) for v in row]
