from app.services.evidence_sources import build_lab_evidence_sources


def test_lab_source_excerpt_requires_name_and_measured_value() -> None:
    text = "Hemoglobin 13.2 g/dL 12-16\nCreatinine 1.4 mg/dL 0.6-1.2"
    labs = [
        {"test_name": "Hemoglobin", "value": 13.2},
        {"test_name": "Creatinine", "value": 1.4},
    ]
    evidence = build_lab_evidence_sources(text, labs)
    assert evidence[0]["sources"] == ["Hemoglobin 13.2 g/dL 12-16"]
    assert evidence[1]["sources"] == ["Creatinine 1.4 mg/dL 0.6-1.2"]


def test_lab_source_excerpt_does_not_fabricate_missing_match() -> None:
    text = "Hemoglobin 13.2 g/dL 12-16\nCreatinine 0.8 mg/dL"
    labs = [{"test_name": "Creatinine", "value": 1.4}]
    assert build_lab_evidence_sources(text, labs) == []
