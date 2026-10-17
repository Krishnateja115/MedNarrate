"""Every label the API enforces must exist, in every language, as fixed text."""

import pytest

from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
from app.services.translation_labels import (
    build_discussion_points,
    get_ui_labels,
    supported_languages,
)
from app.services.translation_validation import validate_translation

LANGUAGES = ["hi", "ta", "te", "kn", "ml", "bn", "mr"]


def test_required_key_list_is_consistent() -> None:
    assert len(REQUIRED_UI_LABEL_KEYS) == 78
    assert len(REQUIRED_UI_LABEL_KEYS) == len(set(REQUIRED_UI_LABEL_KEYS))


def test_all_target_languages_have_a_table() -> None:
    assert sorted(supported_languages()) == sorted(LANGUAGES)


@pytest.mark.parametrize("lang", LANGUAGES)
def test_every_required_label_exists_and_is_translated(lang: str) -> None:
    labels = get_ui_labels(lang)
    english = get_ui_labels("en")
    for key in REQUIRED_UI_LABEL_KEYS + ["label_what_is"]:
        assert labels.get(key, "").strip(), f"{lang}: missing {key}"
    # Not an English copy: most labels must differ from the English text.
    same = [k for k in REQUIRED_UI_LABEL_KEYS if labels[k] == english[k]]
    assert len(same) <= 3, f"{lang}: still English: {same}"
    assert "{name}" in labels["label_what_is"]


@pytest.mark.parametrize("lang", LANGUAGES)
def test_fixed_labels_and_bullets_pass_the_production_validator(lang: str) -> None:
    findings = [
        {"test_name": "Haemoglobin", "value": 10.2, "unit": "g/dL", "flag": "low", "explanation": ""},
        {"test_name": "MCHC", "value": 36.1, "unit": "g/dL", "flag": "high", "explanation": ""},
    ]
    payload = {
        "patient_summary": "",
        "clinician_summary": "",
        "abnormal_findings": [
            {"test_name": f["test_name"], "translated_test_name": f["test_name"], "translated_explanation": ""}
            for f in findings
        ],
        "medications": [],
        "ui_labels": get_ui_labels(lang),
        "doctor_discussion_points": build_discussion_points(
            lang, findings, {}, has_medications=False
        ),
    }
    validate_translation(payload, lang, "", "", findings, [], REQUIRED_UI_LABEL_KEYS)
    bullets = payload["doctor_discussion_points"]
    assert 2 <= len(bullets) <= 5
    assert "10.2" in bullets[0] and "g/dL" in bullets[0]


def test_discussion_points_rules() -> None:
    normal = [{"test_name": "Sodium", "value": 140, "unit": "mmol/L", "flag": "normal"}]
    pts = build_discussion_points("hi", normal, {}, has_medications=True)
    assert len(pts) == 3  # review + medication + follow-up
    many = [
        {"test_name": f"T{i}", "value": i, "unit": "u", "flag": "high"} for i in range(6)
    ]
    pts = build_discussion_points("te", many, {"T0": "టీ0"}, has_medications=False)
    assert len(pts) == 5 and "టీ0" in pts[0]
    assert get_ui_labels("zz") == get_ui_labels("en")  # unknown language never raises
