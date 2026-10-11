from datetime import date

from app.services.provisional_lab_ranges import add_provisional_ranges


REPORT_DATE = date(2026, 10, 11)


def _lab(name: str, value: float, unit: str = "%") -> dict:
    return {
        "test_name": name,
        "value": value,
        "unit": unit,
        "ref_low": None,
        "ref_high": None,
        "flag": "not_classified",
    }


def test_adult_differential_uses_source_attributed_provisional_range() -> None:
    result = add_provisional_ranges(
        [_lab("Monocytes", 9.0)], "1990-05-01", REPORT_DATE
    )[0]
    assert result["flag"] == "high"
    assert (result["ref_low"], result["ref_high"]) == (2.0, 8.0)
    assert result["reference_source"] == "general_provisional"
    assert result["reference_source_url"].startswith("https://medlineplus.gov/")


def test_report_range_takes_precedence() -> None:
    lab = {**_lab("Monocytes", 9.0), "ref_low": 1.0, "ref_high": 10.0,
           "flag": "normal"}
    assert add_provisional_ranges([lab], "1990-05-01", REPORT_DATE) == [lab]


def test_unknown_age_unit_or_test_is_not_guessed() -> None:
    cases = [
        (_lab("Monocytes", 9.0), None),
        (_lab("Monocytes", 9.0), "2015-05-01"),
        (_lab("Monocytes", 9.0, "cells/uL"), "1990-05-01"),
        (_lab("Creatinine", 9.0), "1990-05-01"),
    ]
    for lab, birthdate in cases:
        assert add_provisional_ranges([lab], birthdate, REPORT_DATE) == [lab]
