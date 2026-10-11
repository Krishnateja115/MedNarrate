"""Small, source-attributed fallback catalog for adult lab comparisons.

The report's own reference range always takes precedence. This catalog is not
a diagnosis and must never be used when age or measurement unit is uncertain.
"""

from dataclasses import dataclass
from datetime import date


DIFFERENTIAL_SOURCE = "https://medlineplus.gov/ency/article/003657.htm"


@dataclass(frozen=True)
class GeneralRange:
    low: float
    high: float
    unit: str
    source_url: str


_ADULT_DIFFERENTIAL_PERCENT = {
    "neutrophils": GeneralRange(40.0, 60.0, "%", DIFFERENTIAL_SOURCE),
    "lymphocytes": GeneralRange(20.0, 40.0, "%", DIFFERENTIAL_SOURCE),
    "monocytes": GeneralRange(2.0, 8.0, "%", DIFFERENTIAL_SOURCE),
    "eosinophils": GeneralRange(1.0, 4.0, "%", DIFFERENTIAL_SOURCE),
    "basophils": GeneralRange(0.5, 1.0, "%", DIFFERENTIAL_SOURCE),
}


def _adult_on(date_of_birth: str | None, report_date: date) -> bool:
    if not date_of_birth:
        return False
    try:
        born = date.fromisoformat(date_of_birth)
    except ValueError:
        return False
    years = report_date.year - born.year - (
        (report_date.month, report_date.day) < (born.month, born.day)
    )
    return 18 <= years <= 120


def add_provisional_ranges(
    labs: list[dict], date_of_birth: str | None, report_date: date
) -> list[dict]:
    """Return lab values with conservative, visibly provisional comparisons."""
    if not _adult_on(date_of_birth, report_date):
        return labs

    enriched: list[dict] = []
    for lab in labs:
        value = dict(lab)
        if value.get("ref_low") is not None or value.get("ref_high") is not None:
            enriched.append(value)
            continue
        if value.get("flag") != "not_classified":
            enriched.append(value)
            continue
        general = _ADULT_DIFFERENTIAL_PERCENT.get(
            str(value.get("test_name", "")).strip().lower()
        )
        if general is None or str(value.get("unit", "")).strip() != general.unit:
            enriched.append(value)
            continue
        measured = float(value["value"])
        value["ref_low"] = general.low
        value["ref_high"] = general.high
        value["flag"] = (
            "low" if measured < general.low
            else "high" if measured > general.high
            else "normal"
        )
        value["reference_source"] = "general_provisional"
        value["reference_source_url"] = general.source_url
        enriched.append(value)
    return enriched
