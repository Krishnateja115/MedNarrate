"""Tests for the model-evaluation maths, the data sets and the XAI methods.

The real models are replaced by small fakes so these run offline and fast.
"""
import os

import numpy as np
import pytest

from app.ml import evaluators as E
from app.ml import metrics as M
from app.ml import model_report as R
from app.ml import xai, xai_examples
from app.ml.catalog import MODELS, METRIC_INFO, KIND_DEEP

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge")


# ------------------------------------------------------------- metrics
def test_precision_recall_f1():
    assert M.precision_recall_f1(8, 2, 8) == pytest.approx(
        {"precision": 0.8, "recall": 0.5, "f1": 2 * 0.8 * 0.5 / 1.3}
    )
    assert M.precision_recall_f1(0, 0, 0) == {"precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_word_error_rate_and_number_preservation():
    assert M.word_error_rate("what is my sugar", "what is my sugar") == 0.0
    assert M.word_error_rate("what is my sugar", "what is sugar") == pytest.approx(0.25)
    assert M.number_preservation("Hb is 11.2 and WBC 4,000", "हीमोग्लोबिन 11.2 है") == pytest.approx(0.5)
    assert M.chrf("abc def", "abc def") == pytest.approx(100.0)


def test_retrieval_metrics():
    ranks = [1, 3, None, 6]
    assert M.recall_at_k(ranks, 3) == 0.5
    assert M.mean_reciprocal_rank(ranks) == pytest.approx((1 + 1 / 3 + 1 / 6) / 4)
    assert M.percentile([10, 20, 30, 40], 50) == pytest.approx(25.0)


# ------------------------------------------------------------ data sets
def test_ner_gold_text_is_in_every_sentence():
    items = E.load_dataset("ner_eval.json")["items"]
    assert len(items) >= 20
    for item in items:
        for ent in item["entities"]:
            assert ent["text"] in item["text"], (item["text"], ent["text"])


def test_every_retrieval_query_has_an_answer_in_the_knowledge_base():
    passages = E.read_knowledge_passages(KNOWLEDGE_DIR)
    assert len(passages) > 20
    for q in E.load_dataset("retrieval_eval.json")["queries"]:
        assert any(q["answer_contains"].lower() in p["text"].lower() for p in passages), q


def test_grounded_qa_answers_exist_in_the_context():
    data = E.load_dataset("grounded_qa_eval.json")
    for item in data["in_report"]:
        assert any(tok.lower() in data["context"].lower() for tok in item["any_of"]), item
    assert len(data["out_of_report"]) >= 3


def test_lab_gold_values_are_printed_in_the_text():
    for case in E.load_dataset("lab_extraction_eval.json")["cases"]:
        if "text" not in case:
            continue  # PDF case: text is read from the file by the script
        for gold in case["gold"]:
            shown = f"{gold['value']:g}"
            assert shown in case["text"].replace(",", ""), (case["id"], gold)


def test_translation_and_speech_sets_are_well_formed():
    tr = E.load_dataset("translation_eval.json")
    assert set(tr["languages"]) == {"hi", "ta", "te", "kn", "ml", "bn", "mr"}
    assert sum(1 for i in tr["items"] if M.numbers_in(i["source"])) >= len(tr["items"]) // 2
    stt = E.load_dataset("stt_eval.json")
    assert len(stt["english"]) >= 10 and len(stt["hindi"]) >= 5


# ----------------------------------------------------------- evaluators
def _oracle_ner(items):
    table = {i["text"]: i for i in items}

    def predict(text):
        out = []
        for ent in table[text]["entities"]:
            start = text.find(ent["text"])
            out.append({"start": start, "end": start + len(ent["text"]),
                        "entity_group": ent["label"] or "Sign_symptom", "score": 0.99})
        return out

    return predict


def test_ner_evaluator_perfect_and_degraded():
    items = E.load_dataset("ner_eval.json")["items"]
    perfect = E.evaluate_ner(_oracle_ner(items), items)
    assert perfect["metrics"]["f1"] == pytest.approx(1.0)
    assert perfect["details"]["false_negatives"] == 0

    nothing = E.evaluate_ner(lambda t: [], items)
    assert nothing["metrics"]["recall"] == 0.0 and nothing["metrics"]["f1"] == 0.0

    oracle = _oracle_ner(items)
    half = E.evaluate_ner(lambda t: oracle(t)[::2], items)
    assert 0.2 < half["metrics"]["recall"] < 0.8
    assert half["metrics"]["precision"] == pytest.approx(1.0)


def test_ner_evaluator_counts_wrong_type_and_extra_spans():
    items = [{"text": "She has chest pain today.", "entities": [{"text": "chest pain", "label": "Sign_symptom"}]}]
    preds = [
        {"start": 8, "end": 18, "entity_group": "Disease_disorder", "score": 0.9},
        {"start": 19, "end": 24, "entity_group": "Medication", "score": 0.8},
    ]
    out = E.evaluate_ner(lambda t: preds, items)
    assert out["details"]["true_positives"] == 1
    assert out["details"]["false_positives"] == 1
    assert out["metrics"]["label_accuracy"] == 0.0


def test_bm25_retrieval_finds_most_answers():
    passages = E.read_knowledge_passages(KNOWLEDGE_DIR)
    queries = E.load_dataset("retrieval_eval.json")["queries"]
    out = E.evaluate_retrieval(E.bm25_ranker(passages), passages, queries)
    assert out["n"] == len(queries)
    assert out["metrics"]["recall_at_5"] >= 0.5
    assert out["metrics"]["recall_at_1"] <= out["metrics"]["recall_at_3"] <= out["metrics"]["recall_at_5"]


def test_embedding_ranker_orders_by_similarity():
    passages = [{"text": "alpha"}, {"text": "beta"}, {"text": "gamma"}]
    vectors = {"alpha": [1, 0, 0], "beta": [0, 1, 0], "gamma": [0, 0, 1], "q": [0.1, 0.9, 0]}
    rank = E.embedding_ranker(passages, lambda texts: [vectors[t] for t in texts], lambda q: vectors[q])
    assert rank("q")[0] == 1


def test_grounded_qa_scoring():
    data = E.load_dataset("grounded_qa_eval.json")
    values = {q["question"]: q["any_of"][0] for q in data["in_report"]}

    def good(question, context):
        return f"It is {values[question]}." if question in values else "That is not in the report."

    out = E.evaluate_grounded_qa(good, data)
    assert out["metrics"]["answer_accuracy"] == 1.0
    assert out["metrics"]["abstention_rate"] == 1.0

    out = E.evaluate_grounded_qa(lambda q, c: "It is zzz.", data)
    assert out["metrics"]["answer_accuracy"] == 0.0
    assert out["metrics"]["abstention_rate"] == 0.0


def test_stt_and_translation_evaluators():
    clips = [
        {"language": "en", "reference": "what is my sugar", "audio": b"x"},
        {"language": "hi", "reference": "मेरी शुगर क्या है", "audio": b"y"},
    ]
    refs = {b"x": "what is my sugar", b"y": "मेरी शुगर है"}
    out = E.evaluate_stt(lambda audio, lang: refs[audio], clips)
    assert out["metrics"]["wer_en"] == 0.0
    assert out["metrics"]["wer_hi"] == pytest.approx(0.25)

    data = E.load_dataset("translation_eval.json")
    kept = E.evaluate_translation(lambda src, lang: src, data)
    assert kept["metrics"]["number_preservation"] == 1.0
    dropped = E.evaluate_translation(lambda src, lang: "अनुवाद", data)
    assert dropped["metrics"]["number_preservation"] == 0.0
    assert dropped["metrics"]["sentences_with_all_numbers_kept"] == 0.0


def test_lab_extraction_with_the_real_rule_parsers():
    from app.services.lab_value_extractor import extract_lab_values_rules

    cases = [c for c in E.load_dataset("lab_extraction_eval.json")["cases"] if "text" in c]
    out = E.evaluate_lab_extraction(extract_lab_values_rules, cases)
    assert out["metrics"]["f1"] >= 0.7
    assert set(out["details"]["by_layout"]) == {c["id"] for c in cases}


def test_lab_evaluator_penalises_wrong_values():
    cases = [{"id": "c", "text": "", "gold": [{"name": "Hemoglobin", "value": 12.5}]}]
    right = E.evaluate_lab_extraction(lambda t: [{"test_name": "Haemoglobin", "value": 12.5}], cases)
    wrong = E.evaluate_lab_extraction(lambda t: [{"test_name": "Haemoglobin", "value": 15}], cases)
    assert right["metrics"]["f1"] == 1.0
    assert wrong["metrics"]["f1"] == 0.0 and wrong["details"]["by_layout"]["c"]["extra"] == 1


# ----------------------------------------------------------------- XAI
@pytest.fixture(scope="module")
def classifier():
    from app.ml.medical_classifier import MedicalReportClassifier

    clf = MedicalReportClassifier()
    clf.load_artifacts()
    return clf


def test_linear_attribution_adds_up_to_the_model_score(classifier):
    text = xai_examples.CLASSIFIER_SAMPLES[1]["text"]
    X = classifier.vectorizer.transform([text])
    scores = classifier.model.decision_function(X)[0]
    for idx in range(len(scores)):
        out = xai.linear_attribution(classifier.vectorizer, classifier.model, text, idx, top_k=3)
        assert out["score"] == pytest.approx(float(scores[idx]), abs=1e-9)


def test_lime_finds_the_words_that_drive_a_toy_classifier():
    def predict_proba(texts):
        p = np.array([0.9 if "tumor" in t.split() else 0.1 for t in texts])
        return np.stack([1 - p, p], axis=1)

    out = xai.lime_explain(predict_proba, "the tumor was small and benign", 1, num_samples=300, seed=1)
    assert out["features"][0]["word"] == "tumor"
    assert out["features"][0]["weight"] > 0.5
    assert out["fidelity_r2"] > 0.9
    # deterministic for a fixed seed
    again = xai.lime_explain(predict_proba, "the tumor was small and benign", 1, num_samples=300, seed=1)
    assert again["features"] == out["features"]


def test_explain_classifier_on_pathology_text(classifier):
    out = xai_examples.explain_classifier(xai_examples.CLASSIFIER_SAMPLES[1]["text"], classifier)
    assert out["predicted"] == "TCGA"
    assert sum(out["class_probabilities"].values()) == pytest.approx(1.0)
    words = {f["word"] for f in out["linear"]["features"]}
    assert words & {"tumor", "carcinoma", "lymph", "cm", "nodes"}
    assert 0.0 <= out["lime"]["fidelity_r2"] <= 1.0


def test_occlusion_credits_the_context_word_the_model_relied_on():
    text = "patient takes metformin for diabetes"

    def fake_ner(t):
        # Detects "diabetes" only while the word "metformin" is still visible.
        if "metformin" in t and "diabetes" in t:
            start = t.index("diabetes")
            return [{"start": start, "end": start + 8, "entity_group": "Disease_disorder", "score": 0.9}]
        if "diabetes" in t:
            start = t.index("diabetes")
            return [{"start": start, "end": start + 8, "entity_group": "Disease_disorder", "score": 0.6}]
        return []

    out = xai.occlusion_ner(fake_ner, text)
    ent = out["entities"][0]
    assert ent["entity"] == "diabetes" and ent["label"] == "Disease_disorder"
    assert ent["evidence"][0]["word"] == "metformin"
    assert ent["evidence"][0]["importance"] == pytest.approx(0.3)
    assert all(e["word"] != "diabetes" for e in ent["evidence"])


def test_lab_rule_trace():
    low = xai.explain_lab_flag({"test_name": "Hb", "value": 11.2, "unit": "g/dL", "ref_low": 13, "ref_high": 17, "flag": "low"})
    assert low["rule"] == "value_below_low" and low["agrees_with_flag"]
    assert low["distance"] == pytest.approx(1.8) and low["distance_percent"] == pytest.approx(13.846, abs=0.01)
    high = xai.explain_lab_flag({"test_name": "TLC", "value": 11500, "ref_low": 4000, "ref_high": 10000, "flag": "high"})
    assert high["rule"] == "value_above_high"
    ok = xai.explain_lab_flag({"test_name": "Plt", "value": 180000, "ref_low": 150000, "ref_high": 410000, "flag": "normal"})
    assert ok["rule"] == "value_within_range" and ok["distance"] is None
    none = xai.explain_lab_flag({"test_name": "X", "value": 3, "flag": "not_classified"})
    assert none["rule"] == "no_reference_range"
    bad = xai.explain_lab_flag({"test_name": "X", "value": "n/a"})
    assert bad["rule"] == "no_numeric_value"


# --------------------------------------------------------------- report
def test_catalog_is_consistent():
    ids = [m["id"] for m in MODELS]
    assert len(ids) == len(set(ids))
    assert sum(1 for m in MODELS if m["kind"] == KIND_DEEP) >= 5
    for m in MODELS:
        assert m["primary_metric"] in m["metric_keys"]
        for key in m["metric_keys"]:
            assert key in METRIC_INFO, (m["id"], key)


def test_report_never_invents_numbers(tmp_path):
    report = R.build_report(str(tmp_path / "none.json"), str(tmp_path / "no_classifier.json"))
    assert report["summary"]["evaluated"] == 0
    assert all(m["status"] == "not_evaluated" and m["metrics"] == [] for m in report["models"])


def test_report_uses_stored_results_and_training_metrics(tmp_path):
    path = str(tmp_path / "report.json")
    store = R.load_store(path)
    R.record_result(store, "ner", {"n": 25, "metrics": {"precision": 0.9, "recall": 0.8, "f1": 0.85, "bogus": 1}, "details": {}})
    R.record_result(store, "stt", None, error="no key")
    R.save_store(store, path)

    report = R.build_report(path)
    by_id = {m["id"]: m for m in report["models"]}
    ner = by_id["biomedical_ner"]
    assert ner["status"] == "evaluated" and ner["n"] == 25
    assert [m["key"] for m in ner["metrics"]] == ["precision", "recall", "f1"]  # unknown keys dropped
    assert ner["metrics"][0]["format"] == "percent"
    assert by_id["whisper_stt"]["status"] == "failed" and by_id["whisper_stt"]["error"] == "no key"
    assert by_id["report_classifier"]["status"] == "evaluated"  # from artifacts/metrics.json
    assert report["summary"]["deep_learning_evaluated"] == 1


def test_a_failed_rerun_keeps_the_previous_good_result(tmp_path):
    path = str(tmp_path / "report.json")
    store = R.load_store(path)
    R.record_result(store, "ner", {"n": 3, "metrics": {"f1": 0.5}, "details": {}})
    R.record_result(store, "ner", None, error="model download blocked")
    assert store["results"]["ner"]["metrics"] == {"f1": 0.5}


def test_corrupt_store_file_is_ignored(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert R.load_store(str(path))["results"] == {}


def test_evaluate_script_is_importable_and_lists_parts():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "evaluate_models", os.path.join(os.path.dirname(__file__), "..", "scripts", "evaluate_models.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert {"ner", "llm", "qwen", "stt", "lab", "xai"} <= set(mod.PARTS)
    with pytest.raises(SystemExit):
        mod.main(["--only", "nonsense"])


def test_markdown_export_only_prints_measured_numbers(tmp_path):
    path = str(tmp_path / "report.json")
    store = R.load_store(path)
    R.record_result(store, "ner", {"n": 25, "metrics": {"precision": 0.9, "recall": 0.8, "f1": 0.85}, "details": {}})
    R.save_store(store, path)
    md = R.export_markdown(R.build_report(path, str(tmp_path / "none.json")))
    assert "| F1 score | 85.0% |" in md
    assert md.count("_Not evaluated yet._") == len(MODELS) - 1
    assert "Models measured: 1 of 8" in md
