"""Explainability (XAI) methods used by MedNarrate.

Everything here is plain numpy so it runs without extra dependencies, and the
model is always passed in as a callable so the methods can be tested with fakes.

* ``lime_explain``       - LIME-style local surrogate for any text classifier.
* ``linear_attribution`` - exact per-feature contributions for a linear model
                           (equals SHAP for a linear model, zero baseline).
* ``occlusion_ner``      - occlusion saliency for entity-recognition output.
* ``explain_lab_flag``   - rule trace for a High/Low lab flag.
"""
from __future__ import annotations

import math
import re
from typing import Any, Callable, Sequence

import numpy as np

_WORD_RE = re.compile(r"\S+")


# ------------------------------------------------------------------ LIME
def lime_explain(
    predict_proba: Callable[[list[str]], Any],
    text: str,
    class_index: int,
    *,
    num_samples: int = 400,
    num_features: int = 8,
    kernel_width: float = 0.25,
    ridge: float = 1.0,
    seed: int = 0,
) -> dict:
    """Explain why *predict_proba* gave class *class_index* for *text*.

    Words are switched on/off at random, the model is queried on every variant,
    and a weighted ridge regression of the class probability on the on/off
    pattern is fitted. A positive weight means the word supports the class.
    """
    words = _WORD_RE.findall(text)
    unique = list(dict.fromkeys(w.lower() for w in words))
    n = len(unique)
    if n == 0:
        return {"method": "lime", "features": [], "fidelity_r2": 0.0, "samples": 0}
    rng = np.random.default_rng(seed)
    index = {w: i for i, w in enumerate(unique)}

    masks = rng.integers(0, 2, size=(num_samples, n))
    masks[0, :] = 1  # first row is the original text
    variants = []
    for row in masks:
        kept = [w for w in words if row[index[w.lower()]] == 1]
        variants.append(" ".join(kept))
    probs = np.asarray(predict_proba(variants), dtype=float)[:, class_index]

    # Cosine distance to the original (all ones) -> exponential kernel.
    cos = masks.sum(axis=1) / (math.sqrt(n) * np.sqrt(np.maximum(masks.sum(axis=1), 1)))
    dist = 1.0 - cos
    weights = np.exp(-(dist**2) / (kernel_width**2))

    X = np.hstack([masks.astype(float), np.ones((num_samples, 1))])
    W = np.diag(weights)
    reg = ridge * np.eye(n + 1)
    reg[-1, -1] = 0.0  # do not shrink the intercept
    coef = np.linalg.solve(X.T @ W @ X + reg, X.T @ W @ probs)
    pred = X @ coef
    ss_res = float(np.sum(weights * (probs - pred) ** 2))
    mean = float(np.average(probs, weights=weights))
    ss_tot = float(np.sum(weights * (probs - mean) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 1.0

    order = np.argsort(-np.abs(coef[:n]))[:num_features]
    features = [
        {"word": unique[i], "weight": float(coef[i])} for i in order if abs(coef[i]) > 1e-9
    ]
    return {
        "method": "lime",
        "features": features,
        "fidelity_r2": float(max(0.0, min(1.0, r2))),
        "samples": int(num_samples),
        "original_probability": float(probs[0]),
    }


# ------------------------------------------------------ linear attribution
def linear_attribution(
    vectorizer: Any, model: Any, text: str, class_index: int, *, top_k: int = 8
) -> dict:
    """Exact contribution of each TF-IDF feature to a linear model's score.

    For logistic regression the class score is ``intercept + sum(coef * x)``,
    so each feature contributes ``coef * x``. The contributions plus the
    intercept reproduce ``decision_function`` exactly.
    """
    X = vectorizer.transform([text])
    coo = X.tocoo()
    names = vectorizer.get_feature_names_out()
    coef_row = np.asarray(model.coef_)
    row = coef_row[0] if coef_row.shape[0] == 1 else coef_row[class_index]
    intercept = float(np.asarray(model.intercept_)[0 if coef_row.shape[0] == 1 else class_index])
    contributions = [
        (str(names[j]), float(row[j] * v)) for j, v in zip(coo.col, coo.data)
    ]
    total = intercept + sum(c for _, c in contributions)
    contributions.sort(key=lambda kv: abs(kv[1]), reverse=True)
    return {
        "method": "linear_attribution",
        "features": [{"word": w, "weight": c} for w, c in contributions[:top_k]],
        "intercept": intercept,
        "score": float(total),
        "feature_count": len(contributions),
    }


# --------------------------------------------------------------- occlusion
def _iou(a: tuple[int, int], b: tuple[int, int]) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union else 0.0


def occlusion_ner(
    predict: Callable[[str], Sequence[dict]],
    text: str,
    *,
    top_k: int = 5,
    max_entities: int = 6,
) -> dict:
    """For each detected entity, which *other* words support it most.

    A word is blanked with spaces of equal length (so character offsets stay
    valid) and the model is run again; importance is the fall in the entity's
    confidence. Entities never use their own words as evidence.
    """
    base = list(predict(text))[:max_entities]
    words = [(m.start(), m.end(), m.group()) for m in _WORD_RE.finditer(text)]
    perturbed: dict[int, list[dict]] = {}
    for i, (s, e, _) in enumerate(words):
        blanked = text[:s] + " " * (e - s) + text[e:]
        perturbed[i] = list(predict(blanked))

    explained = []
    for ent in base:
        span = (int(ent["start"]), int(ent["end"]))
        label = str(ent.get("entity_group", ""))
        score = float(ent.get("score", 0.0))
        impacts = []
        for i, (s, e, w) in enumerate(words):
            if _iou((s, e), span) > 0 or (s >= span[0] and e <= span[1]):
                continue
            new_score = 0.0
            for p in perturbed[i]:
                if str(p.get("entity_group", "")) == label and _iou(
                    span, (int(p["start"]), int(p["end"]))
                ) >= 0.5:
                    new_score = float(p.get("score", 0.0))
                    break
            impacts.append({"word": w.strip(".,;:()"), "importance": score - new_score})
        impacts.sort(key=lambda d: abs(d["importance"]), reverse=True)
        explained.append(
            {
                "entity": text[span[0]:span[1]],
                "label": label,
                "confidence": score,
                "evidence": [d for d in impacts if abs(d["importance"]) > 1e-6][:top_k],
            }
        )
    return {"method": "occlusion", "entities": explained}


# ----------------------------------------------------------------- lab rule
def explain_lab_flag(lab: dict) -> dict:
    """Plain-language trace of how a lab value earned its flag."""
    name = str(lab.get("test_name") or lab.get("name") or "This test")
    unit = str(lab.get("unit") or "").strip()
    flag = str(lab.get("flag") or "not_classified").lower()
    try:
        value = float(lab.get("value"))
    except (TypeError, ValueError):
        return {"method": "rule_trace", "flag": flag, "name": name, "rule": "no_numeric_value"}
    low, high = lab.get("ref_low"), lab.get("ref_high")
    low = float(low) if low not in (None, "") else None
    high = float(high) if high not in (None, "") else None

    outcome, rule, distance, pct = "not_classified", "no_reference_range", None, None
    if low is not None and value < low:
        outcome, rule, distance = "low", "value_below_low", low - value
        pct = distance / abs(low) * 100 if low else None
    elif high is not None and value > high:
        outcome, rule, distance = "high", "value_above_high", value - high
        pct = distance / abs(high) * 100 if high else None
    elif low is not None or high is not None:
        outcome, rule = "normal", "value_within_range"
    return {
        "method": "rule_trace",
        "name": name,
        "value": value,
        "unit": unit,
        "ref_low": low,
        "ref_high": high,
        "flag": flag,
        "computed_flag": outcome,
        "rule": rule,
        "distance": distance,
        "distance_percent": pct,
        "source": str(lab.get("reference_source") or "report"),
        "agrees_with_flag": outcome == flag or flag in ("critical", "abnormal"),
    }
