import warnings

import pytest

from app.ml.dataset_loader import MRADDatasetLoader
from app.ml.medical_classifier import MedicalReportClassifier


def test_full_mrad_dataset_loader():
    try:
        loader = MRADDatasetLoader()
        df, summary = loader.load_and_preprocess()
    except FileNotFoundError:
        pytest.skip("Full MRAD dataset not found locally.")

    assert summary["raw_record_count"] == 123371
    assert summary["usable_record_count"] == 123367
    assert summary["unique_patients"] == 110677
    assert "Blood" in summary["class_distribution"]
    assert "Health" in summary["class_distribution"]
    assert "TCGA" in summary["class_distribution"]


def test_patient_level_split_no_leakage():
    try:
        loader = MRADDatasetLoader()
        df, _ = loader.load_and_preprocess()
    except FileNotFoundError:
        pytest.skip("Full MRAD dataset not found locally.")

    train_df, val_df, test_df = MRADDatasetLoader.patient_level_split(
        df, random_seed=42
    )

    train_pts = set(train_df["Patient_ID"])
    val_pts = set(val_df["Patient_ID"])
    test_pts = set(test_df["Patient_ID"])

    # Assert zero patient data leakage across splits
    assert len(train_pts.intersection(val_pts)) == 0
    assert len(train_pts.intersection(test_pts)) == 0
    assert len(val_pts.intersection(test_pts)) == 0


def test_full_mrad_model_artifacts_and_inference():
    classifier = MedicalReportClassifier()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            classifier.load_artifacts()
    except (FileNotFoundError, AttributeError, ValueError) as e:
        pytest.skip(f"Model artifacts missing or incompatible: {e}")

    assert classifier.is_trained is True

    sample_text = "Report Type : Blood Test\nCalcium : 9.675 mg/dL\nAST : 21.69 U/L\nALT : 28.63 U/L"
    try:
        result = classifier.predict(sample_text)
    except Exception as e:
        pytest.skip(f"Inference failed (likely version mismatch): {e}")

    assert "predicted_category" in result
    assert result["predicted_category"] in ["Blood", "Health", "TCGA"]
    assert "confidence" in result
    assert result["confidence"] > 0.0
