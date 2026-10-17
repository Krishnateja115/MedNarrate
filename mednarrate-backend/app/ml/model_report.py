"""Builds the model-performance report shown in the admin portal and the app.

Numbers are never invented: a model with no stored evaluation is reported as
``not_evaluated`` and the UI says so. Results come from
``artifacts/model_report.json`` (written by ``scripts/evaluate_models.py``);
the report-type classifier's numbers come from its training metrics file.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from app.ml.catalog import KIND_DEEP, KIND_LABELS, METRIC_INFO, MODELS, XAI_METHODS

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
REPORT_PATH = os.path.join(ARTIFACTS_DIR, "model_report.json")
CLASSIFIER_METRICS_PATH = os.path.join(ARTIFACTS_DIR, "metrics.json")

EMPTY_STORE: dict[str, Any] = {"generated_at": None, "environment": {}, "results": {}, "xai_examples": {}}


def _read_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def load_store(path: str | None = None) -> dict:
    data = _read_json(path or REPORT_PATH)
    if not data:
        return json.loads(json.dumps(EMPTY_STORE))
    for key, default in EMPTY_STORE.items():
        data.setdefault(key, json.loads(json.dumps(default)))
    return data


def save_store(store: dict, path: str | None = None) -> None:
    target = path or REPORT_PATH
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, target)


def record_result(
    store: dict,
    eval_key: str,
    result: dict | None,
    *,
    error: str | None = None,
    note: str | None = None,
) -> None:
    """Store a successful result, or the reason an evaluation could not run."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if result is not None:
        entry = {
            "n": result.get("n", 0),
            "metrics": result.get("metrics", {}),
            "details": result.get("details", {}),
            "evaluated_at": now,
        }
        if note:
            entry["note"] = note
        store["results"][eval_key] = entry
    else:
        # Keep a previous good result; only record the failure when there is none.
        if eval_key not in store["results"] or "metrics" not in store["results"][eval_key]:
            store["results"][eval_key] = {"error": error or "not run", "attempted_at": now}
    store["generated_at"] = now


def classifier_result(path: str | None = None) -> dict | None:
    data = _read_json(path or CLASSIFIER_METRICS_PATH)
    if not data or "test_accuracy" not in data:
        return None
    info = data.get("dataset_info", {})
    return {
        "n": info.get("test_samples", 0),
        "metrics": {
            "accuracy": data.get("test_accuracy"),
            "macro_precision": data.get("test_precision_macro"),
            "macro_recall": data.get("test_recall_macro"),
            "macro_f1": data.get("test_f1_macro"),
        },
        "details": {
            "classes": info.get("class_names", []),
            "train_samples": info.get("train_samples"),
            "validation_samples": info.get("val_samples"),
            "test_samples": info.get("test_samples"),
            "validation_accuracy": data.get("validation_accuracy"),
            "confusion_matrix": data.get("confusion_matrix"),
            "per_class": {
                k: {m: v.get(m) for m in ("precision", "recall", "f1-score", "support")}
                for k, v in (data.get("per_class_report") or {}).items()
                if k in info.get("class_names", [])
            },
        },
        "evaluated_at": "at training time",
        "note": (
            "Measured on the held-out MRAD test split. A score this high suggests the classes differ "
            "in source-specific wording, so it should not be read as clinical accuracy."
        ),
    }


def _format_metrics(entry: dict, result: dict) -> list[dict]:
    values = result.get("metrics", {})
    out = []
    for key in entry["metric_keys"]:
        value = values.get(key)
        if value is None:
            continue
        info = METRIC_INFO.get(key, {"label": key, "format": "decimal", "higher_is_better": True})
        out.append({"key": key, **info, "value": float(value)})
    return out


def build_report(
    path: str | None = None, classifier_path: str | None = None
) -> dict:
    store = load_store(path)
    models = []
    for entry in MODELS:
        key = entry["eval_key"]
        result = store["results"].get(key)
        if key == "classifier" and not (result and "metrics" in result):
            result = classifier_result(classifier_path)
        item: dict[str, Any] = {
            "id": entry["id"],
            "name": entry["name"],
            "kind": entry["kind"],
            "kind_label": KIND_LABELS[entry["kind"]],
            "architecture": entry["architecture"],
            "task": entry["task"],
            "used_for": entry["used_for"],
            "live": entry["live"],
            "dataset": entry["dataset"],
            "primary_metric": entry["primary_metric"],
            "xai": entry["xai"],
            "status": "not_evaluated",
            "metrics": [],
            "n": 0,
            "details": {},
        }
        if result and "metrics" in result:
            item.update(
                status="evaluated",
                metrics=_format_metrics(entry, result),
                n=int(result.get("n") or 0),
                details=result.get("details", {}),
                evaluated_at=result.get("evaluated_at"),
            )
            if result.get("note"):
                item["note"] = result["note"]
        elif result and result.get("error"):
            item["status"] = "failed"
            item["error"] = result["error"]
        models.append(item)

    deep = [m for m in models if m["kind"] == KIND_DEEP]
    return {
        "generated_at": store.get("generated_at"),
        "environment": store.get("environment", {}),
        "summary": {
            "total": len(models),
            "evaluated": sum(1 for m in models if m["status"] == "evaluated"),
            "deep_learning_total": len(deep),
            "deep_learning_evaluated": sum(1 for m in deep if m["status"] == "evaluated"),
        },
        "models": models,
        "xai_methods": [{"id": k, **v} for k, v in XAI_METHODS.items()],
        "xai_examples": store.get("xai_examples", {}),
        "how_to_refresh": "Run `python scripts/evaluate_models.py` in mednarrate-backend and reload.",
    }


def export_markdown(report: dict) -> str:
    """The report as a Markdown document (for the project write-up).

    Only measured numbers are printed; every other model is listed as not
    evaluated, so the document can never claim more than the run produced.
    """
    lines = [
        "# Model performance results",
        "",
        "Generated by `scripts/evaluate_models.py`. "
        f"Last run: {report.get('generated_at') or 'never'}.",
        "",
    ]
    summary = report["summary"]
    lines += [
        f"Models measured: {summary['evaluated']} of {summary['total']} "
        f"({summary['deep_learning_evaluated']} of {summary['deep_learning_total']} deep-learning).",
        "",
    ]
    for kind in (KIND_DEEP, "classical_ml", "rule_based"):
        group = [m for m in report["models"] if m["kind"] == kind]
        if not group:
            continue
        lines += [f"## {group[0]['kind_label']}", ""]
        for m in group:
            lines += [f"### {m['name']}", "", f"- Task: {m['task']}",
                      f"- Used in the app: {'yes' if m['live'] else 'no (offline / research)'}",
                      f"- Test data: {m['dataset']}"]
            if m["status"] == "evaluated":
                lines += [f"- Test items: {m['n']}", "", "| Metric | Value |", "|---|---|"]
                for metric in m["metrics"]:
                    fmt = metric["format"]
                    v = metric["value"]
                    shown = (
                        f"{v * 100:.1f}%" if fmt == "percent"
                        else f"{v:.0f} ms" if fmt == "ms"
                        else f"{v:.1f} / 100" if fmt == "points"
                        else f"{v:.3f}"
                    )
                    lines.append(f"| {metric['label']} | {shown} |")
                if m.get("note"):
                    lines += ["", f"_Note: {m['note']}_"]
            elif m["status"] == "failed":
                lines += ["", f"_Not measured: {m.get('error', 'the evaluation could not run')}_"]
            else:
                lines += ["", "_Not evaluated yet._"]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
