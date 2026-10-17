"""Evaluators for the models MedNarrate uses.

Each evaluator takes the model as a plain callable and a small labelled data
set, and returns ``{"n": ..., "metrics": {...}, "details": {...}}``. Keeping the
model behind a callable means the maths can be unit-tested here with fake models
and the real models are only wired in by ``scripts/evaluate_models.py``.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Callable, Iterable, Sequence

from app.ml import metrics as M

DATA_DIR = os.path.join(os.path.dirname(__file__), "eval_data")


def load_dataset(name: str) -> dict:
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- NER
# Entity types the app cares about; predictions of other types are not counted
# as false positives (the model knows about many more types than the app uses).
NER_SCORED_LABELS = {
    "Age", "Sex", "Sign_symptom", "Disease_disorder", "Medication", "Dosage",
    "Frequency", "Duration", "Diagnostic_procedure", "Therapeutic_procedure",
    "Biological_structure", "Lab_value",
}


def _gold_spans(text: str, entities: Sequence[dict]) -> list[tuple[int, int, str | None]]:
    spans, used = [], set()
    for ent in entities:
        start = 0
        while True:
            idx = text.find(ent["text"], start)
            if idx < 0:
                break
            if idx not in used:
                used.add(idx)
                spans.append((idx, idx + len(ent["text"]), ent.get("label")))
                break
            start = idx + 1
    return spans


def _iou(a: tuple[int, int], b: tuple[int, int]) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union else 0.0


def evaluate_ner(predict: Callable[[str], list[dict]], items: Sequence[dict]) -> dict:
    """*predict(text)* returns dicts with ``start``, ``end`` and ``entity_group``."""
    tp = fp = fn = 0
    label_ok = label_total = 0
    gold_total = 0
    latencies: list[float] = []
    for item in items:
        text = item["text"]
        started = time.perf_counter()
        preds = predict(text)
        latencies.append((time.perf_counter() - started) * 1000)
        gold = _gold_spans(text, item["entities"])
        gold_total += len(gold)
        taken: set[int] = set()
        for g_start, g_end, g_label in gold:
            best, best_iou = None, 0.0
            for i, p in enumerate(preds):
                if i in taken:
                    continue
                score = _iou((g_start, g_end), (int(p["start"]), int(p["end"])))
                if score > best_iou:
                    best, best_iou = i, score
            if best is not None and best_iou >= 0.5:
                tp += 1
                taken.add(best)
                if g_label:
                    label_total += 1
                    if str(preds[best].get("entity_group", "")).strip() == g_label:
                        label_ok += 1
            else:
                fn += 1
        for i, p in enumerate(preds):
            if i not in taken and str(p.get("entity_group", "")).strip() in NER_SCORED_LABELS:
                fp += 1
    prf = M.precision_recall_f1(tp, fp, fn)
    return {
        "n": len(items),
        "metrics": {
            **prf,
            "label_accuracy": M.accuracy(label_ok, label_total),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        },
        "details": {
            "sentences": len(items),
            "gold_entities": gold_total,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "matching": "A predicted span counts when it overlaps the labelled span with IoU >= 0.5.",
        },
    }


# ---------------------------------------------------------- Retrieval
def read_knowledge_passages(knowledge_dir: str) -> list[dict]:
    """Paragraphs of the knowledge base, split the way the ingest script does."""
    passages = []
    for name in sorted(os.listdir(knowledge_dir)):
        if not name.endswith((".md", ".txt")):
            continue
        with open(os.path.join(knowledge_dir, name), encoding="utf-8") as fh:
            text = fh.read()
        for para in (p.strip() for p in text.split("\n\n")):
            if para and not (para.startswith("#") and "\n" not in para):
                passages.append({"source": name, "text": para})
    return passages


def bm25_ranker(passages: Sequence[dict]) -> Callable[[str], list[int]]:
    from rank_bm25 import BM25Okapi

    tokenised = [re.findall(r"\w+", p["text"].lower()) for p in passages]
    bm25 = BM25Okapi(tokenised)

    def rank(query: str) -> list[int]:
        scores = bm25.get_scores(re.findall(r"\w+", query.lower()))
        return sorted(range(len(passages)), key=lambda i: scores[i], reverse=True)

    return rank


def embedding_ranker(
    passages: Sequence[dict],
    embed_docs: Callable[[list[str]], Sequence[Sequence[float]]],
    embed_query: Callable[[str], Sequence[float]] | None = None,
) -> Callable[[str], list[int]]:
    """Rank passages by cosine similarity. Some embedders (Gemini) use different
    task types for documents and queries, hence the optional *embed_query*."""
    import numpy as np

    matrix = np.asarray(embed_docs([p["text"] for p in passages]), dtype=float)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
    query_fn = embed_query or (lambda q: embed_docs([q])[0])

    def rank(query: str) -> list[int]:
        vec = np.asarray(query_fn(query), dtype=float)
        vec /= np.linalg.norm(vec) + 1e-12
        return [int(i) for i in np.argsort(-(matrix @ vec))]

    return rank


def evaluate_retrieval(
    rank: Callable[[str], list[int]], passages: Sequence[dict], queries: Sequence[dict]
) -> dict:
    ranks: list[int | None] = []
    latencies: list[float] = []
    for q in queries:
        started = time.perf_counter()
        order = rank(q["query"])
        latencies.append((time.perf_counter() - started) * 1000)
        found = None
        for position, idx in enumerate(order, 1):
            if q["answer_contains"].lower() in passages[idx]["text"].lower():
                found = position
                break
        ranks.append(found)
    return {
        "n": len(queries),
        "metrics": {
            "recall_at_1": M.recall_at_k(ranks, 1),
            "recall_at_3": M.recall_at_k(ranks, 3),
            "recall_at_5": M.recall_at_k(ranks, 5),
            "mrr": M.mean_reciprocal_rank(ranks),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        },
        "details": {"queries": len(queries), "passages": len(passages)},
    }


# -------------------------------------------------- Grounded Q&A (LLM)
ABSTAIN_MARKERS = (
    "not in", "not included", "not provided", "does not", "doesn't", "no information",
    "isn't", "is not", "not mentioned", "not listed", "not available", "cannot find",
    "can't find", "not present", "not part of", "not found", "don't see", "do not see",
    "no result", "not reported",
)


def evaluate_grounded_qa(answer: Callable[[str, str], str], data: dict) -> dict:
    ctx = data["context"]
    correct = 0
    latencies: list[float] = []
    misses: list[str] = []
    for item in data["in_report"]:
        started = time.perf_counter()
        reply = answer(item["question"], ctx)
        latencies.append((time.perf_counter() - started) * 1000)
        low = reply.lower()
        if any(token.lower() in low for token in item["any_of"]):
            correct += 1
        else:
            misses.append(item["question"])
    abstained = 0
    for question in data["out_of_report"]:
        started = time.perf_counter()
        reply = answer(question, ctx).lower()
        latencies.append((time.perf_counter() - started) * 1000)
        if any(marker in reply for marker in ABSTAIN_MARKERS):
            abstained += 1
    return {
        "n": len(data["in_report"]) + len(data["out_of_report"]),
        "metrics": {
            "answer_accuracy": M.accuracy(correct, len(data["in_report"])),
            "abstention_rate": M.accuracy(abstained, len(data["out_of_report"])),
            "latency_p50_ms": M.percentile(latencies, 50),
            "latency_p95_ms": M.percentile(latencies, 95),
        },
        "details": {
            "in_report_questions": len(data["in_report"]),
            "out_of_report_questions": len(data["out_of_report"]),
            "missed_questions": misses,
        },
    }


# ------------------------------------------------------ Speech to text
def evaluate_stt(
    transcribe: Callable[[bytes, str], str], clips: Sequence[dict]
) -> dict:
    """*clips*: ``{"language", "reference", "audio"}``; *transcribe(audio, lang)*."""
    per_lang: dict[str, list[float]] = {}
    latencies: list[float] = []
    for clip in clips:
        started = time.perf_counter()
        hypothesis = transcribe(clip["audio"], clip["language"])
        latencies.append((time.perf_counter() - started) * 1000)
        per_lang.setdefault(clip["language"], []).append(
            M.word_error_rate(clip["reference"], hypothesis)
        )
    metrics: dict[str, float] = {}
    for lang, values in per_lang.items():
        metrics[f"wer_{lang}"] = sum(values) / len(values)
    metrics["avg_latency_ms"] = sum(latencies) / len(latencies) if latencies else 0.0
    return {
        "n": len(clips),
        "metrics": metrics,
        "details": {"clips_per_language": {k: len(v) for k, v in per_lang.items()}},
    }


# ---------------------------------------------------------- Translation
def evaluate_translation(translate: Callable[[str, str], str], data: dict) -> dict:
    languages = data["languages"]
    per_lang: dict[str, list[float]] = {lang: [] for lang in languages}
    chrf_hi: list[float] = []
    latencies: list[float] = []
    all_kept = 0
    scored = 0  # sentences that contain a number (others cannot lose one)
    total = 0
    for item in data["items"]:
        has_numbers = bool(M.numbers_in(item["source"]))
        for lang in languages:
            started = time.perf_counter()
            out = translate(item["source"], lang)
            latencies.append((time.perf_counter() - started) * 1000)
            total += 1
            if has_numbers:
                kept = M.number_preservation(item["source"], out)
                per_lang[lang].append(kept)
                scored += 1
                all_kept += 1 if kept == 1.0 else 0
            if lang == "hi" and item.get("reference_hi"):
                chrf_hi.append(M.chrf(item["reference_hi"], out))
    metrics: dict[str, float] = {
        "number_preservation": sum(sum(v) for v in per_lang.values()) / max(1, scored),
        "sentences_with_all_numbers_kept": M.accuracy(all_kept, scored),
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
    }
    if chrf_hi:
        metrics["chrf_hindi"] = sum(chrf_hi) / len(chrf_hi)
    return {
        "n": total,
        "metrics": metrics,
        "details": {
            "number_preservation_by_language": {
                lang: (sum(v) / len(v) if v else 0.0) for lang, v in per_lang.items()
            },
            "sentences": len(data["items"]),
            "languages": languages,
        },
    }


# ------------------------------------------------------- Lab extraction
def _norm_name(name: str) -> str:
    from app.services.lab_value_normalizer import comparison_name

    return comparison_name(name or "") or (name or "").lower().strip()


def _names_agree(gold: str, pred: str) -> bool:
    g, p = _norm_name(gold), _norm_name(pred)
    if g == p or g in p or p in g:
        return True
    g_tokens = set(re.findall(r"[a-z0-9]+", g))
    p_tokens = set(re.findall(r"[a-z0-9]+", p))
    return bool(g_tokens & p_tokens - {"count", "total", "serum", "blood"})


def _same_value(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-6, 1e-3 * max(abs(a), abs(b)))


def evaluate_lab_extraction(
    extract: Callable[[str], list[dict]], cases: Sequence[dict]
) -> dict:
    tp = fp = fn = 0
    by_layout: dict[str, dict[str, Any]] = {}
    for case in cases:
        preds = extract(case["text"])
        taken: set[int] = set()
        c_tp = c_fn = 0
        for gold in case["gold"]:
            hit = None
            for i, p in enumerate(preds):
                if i in taken:
                    continue
                try:
                    value_ok = _same_value(float(p.get("value")), float(gold["value"]))
                except (TypeError, ValueError):
                    continue
                if value_ok and _names_agree(gold["name"], str(p.get("test_name", ""))):
                    hit = i
                    break
            if hit is None:
                c_fn += 1
            else:
                c_tp += 1
                taken.add(hit)
        c_fp = len(preds) - len(taken)
        tp, fp, fn = tp + c_tp, fp + c_fp, fn + c_fn
        by_layout[case["id"]] = {
            "layout": case.get("layout", ""),
            "gold": len(case["gold"]),
            "found": c_tp,
            "extra": c_fp,
            **M.precision_recall_f1(c_tp, c_fp, c_fn),
        }
    return {
        "n": sum(len(c["gold"]) for c in cases),
        "metrics": M.precision_recall_f1(tp, fp, fn),
        "details": {"by_layout": by_layout, "reports": len(cases)},
    }
