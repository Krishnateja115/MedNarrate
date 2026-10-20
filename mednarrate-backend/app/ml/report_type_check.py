"""Experimental "document type check" built on the MRAD-trained classifier.

The classifier compares the wording of a report with the three kinds of records
it was trained on (blood tests, general health records, TCGA records). It is
shown to the user as an experimental hint only: it never changes a summary, a
lab value or a report's status, and every failure simply means "no hint".
"""
from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

# The hint is only shown when the model clearly prefers one type. These values
# are deliberately modest: the model's probabilities are not well calibrated (a
# real blood-count report scores about 60%), so the margin over the runner-up
# is checked as well. The caller must also check that the document really looks
# medical, because the model will confidently label unrelated text.
MIN_CONFIDENCE = 0.55
MIN_MARGIN = 0.15
# The first part of a report is enough to recognise its style and keeps this fast.
MAX_CHARS = 20_000
MIN_CHARS = 40

KNOWN_TYPES = {"Blood", "Health", "TCGA"}

_lock = threading.Lock()
_classifier: Any = None


def _get_classifier():
    """Load the trained model once; the first caller pays the small load cost."""
    global _classifier
    with _lock:
        if _classifier is None:
            from app.ml.medical_classifier import MedicalReportClassifier

            clf = MedicalReportClassifier()
            clf.load_artifacts()
            _classifier = clf
        return _classifier


def reset_cache() -> None:
    """For tests."""
    global _classifier
    with _lock:
        _classifier = None


def classify_report_text(text: str | None) -> dict | None:
    """Return ``{"label", "confidence"}`` or ``None`` when there is no usable hint.

    Never raises: a missing model file, a missing library or odd text all give
    ``None``.
    """
    try:
        cleaned = (text or "").strip()
        if len(cleaned) < MIN_CHARS:
            return None
        prediction = _get_classifier().predict(cleaned[:MAX_CHARS])
        label = prediction.get("predicted_category")
        confidence = float(prediction.get("confidence") or 0.0)
        others = sorted(
            (
                float(v)
                for k, v in (prediction.get("class_probabilities") or {}).items()
                if k != label
            ),
            reverse=True,
        )
        margin = confidence - (others[0] if others else 0.0)
        if label not in KNOWN_TYPES or confidence < MIN_CONFIDENCE or margin < MIN_MARGIN:
            return None
        return {"label": label, "confidence": round(confidence, 4)}
    except Exception:  # noqa: BLE001 - this hint must never affect the app
        logger.warning("Document type check unavailable", exc_info=True)
        return None
