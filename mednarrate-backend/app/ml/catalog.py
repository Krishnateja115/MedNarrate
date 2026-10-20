"""Catalogue of every model MedNarrate relies on, and how each is measured.

This is descriptive metadata only. The numbers live in ``artifacts/model_report.json``
(written by ``scripts/evaluate_models.py``) and, for the report-type classifier,
in ``artifacts/metrics.json`` (written when that model was trained).
"""
from __future__ import annotations

from typing import Any

KIND_DEEP = "deep_learning"
KIND_CLASSICAL = "classical_ml"
KIND_RULES = "rule_based"

# How the UI should print each metric. ``higher_is_better`` drives colouring.
METRIC_INFO: dict[str, dict[str, Any]] = {
    "precision": {"label": "Precision", "format": "percent", "higher_is_better": True},
    "recall": {"label": "Recall", "format": "percent", "higher_is_better": True},
    "f1": {"label": "F1 score", "format": "percent", "higher_is_better": True},
    "label_accuracy": {"label": "Entity-type accuracy", "format": "percent", "higher_is_better": True},
    "recall_at_1": {"label": "Recall@1", "format": "percent", "higher_is_better": True},
    "recall_at_3": {"label": "Recall@3", "format": "percent", "higher_is_better": True},
    "recall_at_5": {"label": "Recall@5", "format": "percent", "higher_is_better": True},
    "mrr": {"label": "Mean reciprocal rank", "format": "decimal", "higher_is_better": True},
    "answer_accuracy": {"label": "Answer accuracy", "format": "percent", "higher_is_better": True},
    "abstention_rate": {"label": "Correctly says 'not in report'", "format": "percent", "higher_is_better": True},
    "wer_en": {"label": "Word error rate (English)", "format": "percent", "higher_is_better": False},
    "wer_hi": {"label": "Word error rate (Hindi)", "format": "percent", "higher_is_better": False},
    "number_preservation": {"label": "Numbers kept in translation", "format": "percent", "higher_is_better": True},
    "sentences_with_all_numbers_kept": {"label": "Sentences with every number kept", "format": "percent", "higher_is_better": True},
    "chrf_hindi": {"label": "chrF (Hindi, 0-100)", "format": "points", "higher_is_better": True},
    "avg_latency_ms": {"label": "Average latency", "format": "ms", "higher_is_better": False},
    "latency_p50_ms": {"label": "Median latency", "format": "ms", "higher_is_better": False},
    "latency_p95_ms": {"label": "95th-percentile latency", "format": "ms", "higher_is_better": False},
    "accuracy": {"label": "Accuracy", "format": "percent", "higher_is_better": True},
    "macro_precision": {"label": "Macro precision", "format": "percent", "higher_is_better": True},
    "macro_recall": {"label": "Macro recall", "format": "percent", "higher_is_better": True},
    "macro_f1": {"label": "Macro F1", "format": "percent", "higher_is_better": True},
}

XAI_METHODS: dict[str, dict[str, str]] = {
    "lime": {
        "name": "LIME (local surrogate)",
        "summary": (
            "Hides random words from the text, asks the model again, and fits a small weighted "
            "linear model to the answers. The weights show which words pushed the prediction."
        ),
    },
    "linear_attribution": {
        "name": "Exact linear attribution (SHAP for linear models)",
        "summary": (
            "For a linear model each word's contribution is its weight times its TF-IDF value. "
            "These contributions plus the intercept add up exactly to the model's score, which is "
            "what SHAP values equal for a linear model against a zero baseline."
        ),
    },
    "occlusion": {
        "name": "Occlusion saliency",
        "summary": (
            "Blanks out one word at a time and measures how much the model's confidence in a "
            "detected entity drops. Words whose removal hurts most are the evidence."
        ),
    },
    "rule_trace": {
        "name": "Rule trace",
        "summary": (
            "Shows the exact comparison that produced a High/Low flag: the measured value against "
            "the reference range printed in the report."
        ),
    },
}

MODELS: list[dict[str, Any]] = [
    {
        "id": "biomedical_ner",
        "name": "Biomedical NER (d4data/biomedical-ner-all)",
        "kind": KIND_DEEP,
        "architecture": "Transformer encoder (DistilBERT) fine-tuned for token classification",
        "task": "Finds symptoms, diseases, medicines, doses and lab terms in report text",
        "used_for": "Highlights clinical terms when a report is analysed",
        "live": True,
        "eval_key": "ner",
        "metric_keys": ["precision", "recall", "f1", "label_accuracy", "avg_latency_ms"],
        "primary_metric": "f1",
        "dataset": "Hand-labelled synthetic clinical sentences (app/ml/eval_data/ner_eval.json)",
        "xai": ["occlusion"],
    },
    {
        "id": "report_embedding",
        "name": "Report retrieval embeddings (Gemini gemini-embedding-001)",
        "kind": KIND_DEEP,
        "architecture": "Transformer text-embedding model (hosted by Google)",
        "task": "Finds the passages of a user's report that answer a chat question",
        "used_for": "Chat answers about a specific report. Active when Gemini is the AI provider and a Gemini key is set; otherwise a BM25 keyword search answers.",
        "live": True,
        "eval_key": "retrieval_gemini",
        "metric_keys": ["recall_at_1", "recall_at_3", "recall_at_5", "mrr", "avg_latency_ms"],
        "primary_metric": "recall_at_3",
        "dataset": "Questions over the knowledge-base paragraphs (app/ml/eval_data/retrieval_eval.json)",
        "xai": [],
    },
    {
        "id": "kb_embedding",
        "name": "Knowledge-base embeddings (ChromaDB default, all-MiniLM-L6-v2)",
        "kind": KIND_DEEP,
        "architecture": "MiniLM sentence-transformer (6 layers, 384 dimensions)",
        "task": "Finds general medical knowledge that answers a health question",
        "used_for": "General health chat (retrieve_kb_context)",
        "live": True,
        "eval_key": "retrieval_minilm",
        "metric_keys": ["recall_at_1", "recall_at_3", "recall_at_5", "mrr", "avg_latency_ms"],
        "primary_metric": "recall_at_3",
        "dataset": "Questions over the knowledge-base paragraphs (app/ml/eval_data/retrieval_eval.json)",
        "xai": [],
    },
    {
        "id": "llm_chain",
        "name": "Language-model chain (Gemini first, other hosted models as fail-over)",
        "kind": KIND_DEEP,
        "architecture": "Large decoder-only language models behind a fail-over chain",
        "task": "Explains reports, answers questions from report text, translates summaries",
        "used_for": "Summaries, chat answers and translation. Gemini answers first; another provider (Vertex AI, OpenAI, Anthropic, Mistral, Groq, Cerebras, OpenRouter, GitHub Models, Ollama) answers only if it is configured and Gemini fails.",
        "live": True,
        "eval_key": "llm",
        "metric_keys": [
            "answer_accuracy", "abstention_rate", "number_preservation",
            "sentences_with_all_numbers_kept", "chrf_hindi", "latency_p50_ms", "latency_p95_ms",
        ],
        "primary_metric": "answer_accuracy",
        "dataset": "Synthetic report with checkable questions plus English-to-Indian-language sentences",
        "xai": [],
    },
    {
        "id": "local_qwen",
        "name": "Offline model (Qwen2.5-1.5B-Instruct, GGUF)",
        "kind": KIND_DEEP,
        "architecture": "Small decoder-only language model run on the server's CPU",
        "task": "Offline translation when no hosted model is reachable",
        "used_for": "Translation fall-back. Used only when 'local' is added to TRANSLATION_PROVIDER_ORDER and the model file has been downloaded.",
        "live": True,
        "eval_key": "qwen",
        "metric_keys": ["number_preservation", "sentences_with_all_numbers_kept", "chrf_hindi", "avg_latency_ms"],
        "primary_metric": "number_preservation",
        "dataset": "English-to-Indian-language sentences (app/ml/eval_data/translation_eval.json)",
        "xai": [],
    },
    {
        "id": "whisper_stt",
        "name": "Speech recognition (Whisper large-v3 via Groq)",
        "kind": KIND_DEEP,
        "architecture": "Transformer encoder-decoder speech model",
        "task": "Turns spoken chat questions into text",
        "used_for": "Voice input in chat. Off unless VOICE_INPUT_ENABLED=true and a Groq key is set.",
        "live": True,
        "eval_key": "stt",
        "metric_keys": ["wer_en", "wer_hi", "avg_latency_ms"],
        "primary_metric": "wer_en",
        "dataset": "Spoken test sentences (computer-generated voice; optimistic) in English and Hindi",
        "xai": [],
    },
    {
        "id": "report_classifier",
        "name": "Report-type classifier (TF-IDF + Logistic Regression)",
        "kind": KIND_CLASSICAL,
        "architecture": "Bag-of-words features with a linear classifier (not a neural network)",
        "task": "Predicts whether a report is Blood, Health check or TCGA/pathology",
        "used_for": "Research model; not called by the live app",
        "live": False,
        "eval_key": "classifier",
        "metric_keys": ["accuracy", "macro_precision", "macro_recall", "macro_f1"],
        "primary_metric": "macro_f1",
        "dataset": "MRAD unified dataset, patient-level split (held-out test set)",
        "xai": ["lime", "linear_attribution"],
    },
    {
        "id": "lab_extractor",
        "name": "Lab-value extractor (rule-based parsers)",
        "kind": KIND_RULES,
        "architecture": "Hand-written table/line parsers with an LLM fall-back in production",
        "task": "Reads test name, value, unit and reference range from report text",
        "used_for": "Every report upload; High/Low flags come from comparing against the printed range",
        "live": True,
        "eval_key": "lab",
        "metric_keys": ["precision", "recall", "f1"],
        "primary_metric": "f1",
        "dataset": "Report layouts in app/ml/eval_data/lab_extraction_eval.json (rules only, no LLM fall-back)",
        "xai": ["rule_trace"],
    },
]

KIND_LABELS = {
    KIND_DEEP: "Deep learning",
    KIND_CLASSICAL: "Classical machine learning",
    KIND_RULES: "Rule-based",
}

