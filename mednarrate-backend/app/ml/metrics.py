"""Small, dependency-free metric functions used by the model evaluation.

Everything here is plain Python so the maths can be unit-tested without any
model, dataset or network.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Iterable, Sequence


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def accuracy(correct: int, total: int) -> float:
    return correct / total if total else 0.0


def _words(text: str) -> list[str]:
    """Whitespace-separated words with punctuation removed.

    Splitting on ``\\w`` would cut Indic words at every vowel sign (they are
    combining marks, not letters), so punctuation is stripped by Unicode
    category instead.
    """
    cleaned = "".join(ch for ch in text.lower() if not unicodedata.category(ch).startswith("P"))
    return cleaned.split()


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Word-level edit distance divided by the number of reference words."""
    ref, hyp = _words(reference), _words(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i]
        for j, h in enumerate(hyp, 1):
            cost = 0 if r == h else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1] / len(ref)


def _char_ngrams(text: str, n: int) -> Counter:
    s = re.sub(r"\s+", "", text)
    return Counter(s[i : i + n] for i in range(len(s) - n + 1)) if len(s) >= n else Counter()


def chrf(reference: str, hypothesis: str, max_n: int = 6, beta: float = 2.0) -> float:
    """Character n-gram F-score (chrF, Popovic 2015) on a 0..100 scale.

    Works for any script, which matters for Hindi, Tamil and the other
    languages the app translates into.
    """
    precisions, recalls = [], []
    for n in range(1, max_n + 1):
        ref_n, hyp_n = _char_ngrams(reference, n), _char_ngrams(hypothesis, n)
        if not ref_n or not hyp_n:
            continue
        overlap = sum((ref_n & hyp_n).values())
        precisions.append(overlap / sum(hyp_n.values()))
        recalls.append(overlap / sum(ref_n.values()))
    if not precisions:
        return 0.0
    p, r = sum(precisions) / len(precisions), sum(recalls) / len(recalls)
    if p + r == 0:
        return 0.0
    b2 = beta * beta
    return 100.0 * (1 + b2) * p * r / (b2 * p + r)


def numbers_in(text: str) -> list[str]:
    """Digit sequences, e.g. '11.2' or '4,000', normalised to ASCII digits."""
    table = str.maketrans(
        "०१२३४५६७८९௦௧௨௩௪௫௬௭௮௯౦౧౨౩౪౫౬౭౮౯೦೧೨೩೪೫೬೭೮೯൦൧൨൩൪൫൬൭൮൯০১২৩৪৫৬৭৮৯",
        "0123456789" * 6,
    )
    return [m.replace(",", "") for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text.translate(table))]


def number_preservation(source: str, translated: str) -> float:
    """Share of the numbers in *source* that still appear in *translated*.

    A translation that changes "11.2" into "12.2" is dangerous in a medical
    report, so this is reported next to the language-quality score.
    """
    src = numbers_in(source)
    if not src:
        return 1.0
    out = Counter(numbers_in(translated))
    kept = 0
    for n in src:
        if out[n] > 0:
            out[n] -= 1
            kept += 1
    return kept / len(src)


def recall_at_k(ranks: Sequence[int | None], k: int) -> float:
    """*ranks* holds the 1-based rank of the first relevant hit, or None."""
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks) if ranks else 0.0


def mean_reciprocal_rank(ranks: Sequence[int | None]) -> float:
    return sum(1.0 / r for r in ranks if r) / len(ranks) if ranks else 0.0


def percentile(values: Iterable[float], pct: float) -> float:
    data = sorted(values)
    if not data:
        return 0.0
    k = (len(data) - 1) * pct / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return data[lo] if lo == hi else data[lo] + (data[hi] - data[lo]) * (k - lo)
