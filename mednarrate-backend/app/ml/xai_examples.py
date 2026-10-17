"""Ready-made explanations used by the admin portal and the app."""
from __future__ import annotations

from typing import Any, Callable, Sequence

from app.ml import xai
from app.ml.dataset_loader import clean_report_text_features

# Short, invented report excerpts (no patient data) used as worked examples.
CLASSIFIER_SAMPLES = [
    {
        "title": "Blood test excerpt",
        "text": (
            "Hemoglobin 11.2 g/dL Total leucocyte count 11500 /cumm Platelet count 180000 /cumm "
            "Fasting glucose 112 mg/dL Serum creatinine 0.9 mg/dL"
        ),
    },
    {
        "title": "Pathology excerpt",
        "text": (
            "Histopathology: invasive ductal carcinoma, grade 2, tumor size 2.1 cm, margins negative, "
            "lymph nodes 0/12 positive, ER positive"
        ),
    },
]

NER_SAMPLES = [
    "The patient has type 2 diabetes mellitus and takes metformin 500 mg twice daily.",
    "A 45-year-old male presented with chest pain and shortness of breath.",
]

LAB_SAMPLES = [
    {"test_name": "Hemoglobin", "value": 11.2, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "flag": "low"},
    {"test_name": "Total Leucocyte Count", "value": 11500, "unit": "/cumm", "ref_low": 4000, "ref_high": 10000, "flag": "high"},
    {"test_name": "Platelet Count", "value": 180000, "unit": "/cumm", "ref_low": 150000, "ref_high": 410000, "flag": "normal"},
]

MAX_EXPLAIN_CHARS = 3000


def explain_classifier(text: str, classifier: Any, *, num_samples: int = 400, seed: int = 0) -> dict:
    """Prediction plus LIME and exact linear attribution for the predicted class."""
    if not classifier.is_trained:
        classifier.load_artifacts()
    cleaned = clean_report_text_features(text)[:MAX_EXPLAIN_CHARS]
    vec, model, enc = classifier.vectorizer, classifier.model, classifier.label_encoder

    def predict_proba(texts: list[str]):
        return model.predict_proba(vec.transform([clean_report_text_features(t) for t in texts]))

    probs = predict_proba([cleaned])[0]
    idx = int(probs.argmax())
    classes = [str(c) for c in enc.classes_]
    return {
        "predicted": classes[idx],
        "confidence": float(probs[idx]),
        "class_probabilities": {c: float(p) for c, p in zip(classes, probs)},
        "lime": xai.lime_explain(predict_proba, cleaned, idx, num_samples=num_samples, seed=seed),
        "linear": xai.linear_attribution(vec, model, cleaned, idx),
    }


def classifier_examples(classifier: Any) -> list[dict]:
    out = []
    for sample in CLASSIFIER_SAMPLES:
        result = explain_classifier(sample["text"], classifier)
        out.append({"title": sample["title"], "text": sample["text"], **result})
    return out


def ner_examples(predict: Callable[[str], Sequence[dict]]) -> list[dict]:
    out = []
    for text in NER_SAMPLES:
        result = xai.occlusion_ner(predict, text)
        out.append({"title": "Entity evidence", "text": text, **result})
    return out


def lab_examples() -> list[dict]:
    return [xai.explain_lab_flag(lab) for lab in LAB_SAMPLES]
