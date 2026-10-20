"""Review 2 ablation experiments for the MedNarrate pipeline.

Every number written by this script is produced by running the project's own
code (app/services/..., app/api/v1/chat.py) on the test sets in this folder
and in app/ml/eval_data. Nothing here calls a hosted language model.

Run from mednarrate-backend:
    PYTHONPATH=. python experiments/review2/run_ablation.py
Results: experiments/review2/results/ablation_results.json
"""
from __future__ import annotations

import ast
import io
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)

from app.ml import evaluators as E  # noqa: E402
from app.ml import metrics as M  # noqa: E402
from app.services import lab_value_extractor as LX  # noqa: E402
from app.services.lab_value_normalizer import comparison_name  # noqa: E402
from app.services.validation import verify_summary_grounding  # noqa: E402
from app.services.rag_safety import verify_response_against_source  # noqa: E402
from app.services import translation_validation as TV  # noqa: E402
from app.services.privacy import deidentify_prompt_text  # noqa: E402
from app.services.document_validation import validate_medical_document  # noqa: E402

DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


# ------------------------------------------------------------------ cases
def lab_cases():
    import fitz

    cases = E.load_dataset("lab_extraction_eval.json")["cases"]
    for case in cases:
        if "text" not in case and case.get("pdf"):
            pdf = os.path.join(BACKEND, "..", case["pdf"])
            with fitz.open(pdf) as doc:
                case["text"] = "\n".join(p.get_text() for p in doc)
    return cases


# Gold High/Low/Normal flags for the text cases, read by hand from the printed
# reference ranges (the PDF case is excluded because its layout does not print
# a range next to every value).
GOLD_FLAGS = {
    "inline_rows": {"Hemoglobin": "low", "White blood cells": "high", "Platelets": "normal",
                    "Glucose": "high", "Creatinine": "normal", "Urea": "normal"},
    "vertical_columns": {"ALT": "high", "AST": "normal", "Bilirubin": "normal",
                         "Alkaline phosphatase": "normal"},
    "thyroid_panel": {"T3": "normal", "T4": "normal", "TSH": "high", "Vitamin D": "low",
                      "HbA1c": "high"},
    "pipe_separated": {"Hemoglobin": "normal", "Total cholesterol": "high", "HDL": "low",
                       "LDL": "high", "Triglycerides": "high"},
}


# --------------------------------------------------- E1 parser ablation
PARSERS = {
    "column": LX._extract_column_layout_table,
    "table": LX._extract_report_table,
    "lines": LX._extract_simple_lab_lines,
}


def cascade(order):
    def run(text):
        for name in order:
            out = PARSERS[name](text)
            if out:
                return out
        return []
    return run


def e1_parsers(cases):
    configs = {
        "Full cascade (column -> table -> lines)": ["column", "table", "lines"],
        "Without column parser": ["table", "lines"],
        "Without table parser": ["column", "lines"],
        "Without line parser": ["column", "table"],
        "Column parser only": ["column"],
        "Table parser only": ["table"],
        "Line parser only": ["lines"],
    }
    rows = {}
    for label, order in configs.items():
        res = E.evaluate_lab_extraction(cascade(order), cases)
        rows[label] = {
            **{k: round(v, 4) for k, v in res["metrics"].items()},
            "found_by_layout": {k: f'{v["found"]}/{v["gold"]}' for k, v in res["details"]["by_layout"].items()},
        }
    return {"n_values": sum(len(c["gold"]) for c in cases), "n_reports": len(cases), "configs": rows}


def e1_flags(cases):
    total = correct = found = 0
    wrong = []
    for case in cases:
        gold = GOLD_FLAGS.get(case["id"])
        if not gold:
            continue
        preds = LX.extract_lab_values_rules(case["text"])
        for g in case["gold"]:
            if g["name"] not in gold:
                continue
            total += 1
            for p in preds:
                try:
                    same = E._same_value(float(p["value"]), float(g["value"]))
                except (TypeError, ValueError):
                    continue
                if same and E._names_agree(g["name"], str(p.get("test_name", ""))):
                    found += 1
                    if p.get("flag") == gold[g["name"]]:
                        correct += 1
                    else:
                        wrong.append([case["id"], g["name"], p.get("flag"), gold[g["name"]]])
                    break
    # Ablation: the same values without their printed range.
    stripped = 0
    for case in cases:
        if case["id"] not in GOLD_FLAGS:
            continue
        text = re.sub(r"(<|>)\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?", "", case["text"])
        for p in LX.extract_lab_values_rules(text):
            if p.get("flag") == "not_classified":
                stripped += 1
    return {"labelled_values": total, "extracted": found, "flag_correct": correct,
            "wrong": wrong, "not_classified_when_ranges_removed": stripped}


# ------------------------------------------------- E2 name normalisation
def e2_names():
    data = load("name_pairs.json")

    def raw(a, b):
        return a == b

    def lower(a, b):
        f = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        return f(a) == f(b)

    def canon(a, b):
        return comparison_name(a) == comparison_name(b)

    out = {}
    for label, fn in (("Exact string match", raw), ("Lower-case, punctuation removed", lower),
                      ("MedNarrate normaliser (comparison_name)", canon)):
        same_ok = [p for p in data["same"] if fn(*p)]
        diff_bad = [p for p in data["different"] if fn(*p)]
        out[label] = {
            "same_pairs_matched": f"{len(same_ok)}/{len(data['same'])}",
            "same_recall": round(len(same_ok) / len(data["same"]), 4),
            "different_pairs_wrongly_merged": f"{len(diff_bad)}/{len(data['different'])}",
        }
    out["missed_by_normaliser"] = [p for p in data["same"] if not canon(*p)]
    return out


# ---------------------------------------------- E3 grounding verifier
LISTED = ["diabetes", "kidney failure", "leukemia", "cancer", "heart failure", "stroke"]
UNLISTED = ["anaemia", "hypothyroidism", "fatty liver disease", "a liver infection",
            "prediabetes", "chronic kidney disease"]


def _summary(labs):
    parts = []
    for lab in labs:
        s = f'Your {lab["test_name"]} is {fmt(lab["value"])} {lab.get("unit") or ""}'.strip()
        if lab.get("ref_low") is not None and lab.get("ref_high") is not None:
            s += f' (reference {fmt(lab["ref_low"])} to {fmt(lab["ref_high"])})'
        parts.append(s + ".")
    return parts


def _perturb_value(v):
    s = fmt(v)
    out = {}
    out["value +10%"] = fmt(round(v * 1.1, len(s.split(".")[1]) if "." in s else 0))
    digits = s.replace(".", "")
    if len(digits) >= 2 and digits[0] != digits[1]:
        sw = digits[1] + digits[0] + digits[2:]
        if "." in s:
            pos = s.index(".")
            sw = sw[:pos] + "." + sw[pos:]
        out["two digits swapped"] = sw
    out["decimal point moved (x10)"] = fmt(round(v * 10, 6))
    return out


def e3_grounding(cases):
    reports = [(c["id"], c["text"]) for c in cases]
    qa = E.load_dataset("grounded_qa_eval.json")
    reports.append(("qa_context", qa["context"]))
    tallies = {}
    coincidental = []
    faithful_flagged = 0
    faithful_total = 0

    def bump(kind, detected, detected_chat):
        t = tallies.setdefault(kind, {"n": 0, "summary_verifier": 0, "chat_verifier": 0})
        t["n"] += 1
        t["summary_verifier"] += int(detected)
        t["chat_verifier"] += int(detected_chat)

    for rid, text in reports:
        labs = LX.extract_lab_values_rules(text)
        if not labs:
            continue
        sentences = _summary(labs)
        faithful = " ".join(sentences)
        faithful_total += 1
        if not verify_summary_grounding(faithful, text, labs)["is_valid"]:
            faithful_flagged += 1
        for i, lab in enumerate(labs):
            for kind, new in _perturb_value(float(lab["value"])).items():
                changed = list(sentences)
                changed[i] = changed[i].replace(f'is {fmt(lab["value"])}', f"is {new}", 1)
                summ = " ".join(changed)
                det = not verify_summary_grounding(summ, text, labs)["is_valid"]
                det_chat = not verify_response_against_source(summ, text)[1]
                bump(kind, det, det_chat)
                if not det:
                    coincidental.append([rid, lab["test_name"], fmt(lab["value"]), new])
            if lab.get("ref_high") is not None and lab.get("ref_low") is not None:
                new_high = fmt(round(float(lab["ref_high"]) * 1.25, 1))
                changed = list(sentences)
                changed[i] = changed[i].replace(f'to {fmt(lab["ref_high"])})', f"to {new_high})", 1)
                summ = " ".join(changed)
                bump("reference range altered", not verify_summary_grounding(summ, text, labs)["is_valid"],
                     not verify_response_against_source(summ, text)[1])
        for group, names in (("diagnosis on watch-list added", LISTED),
                             ("diagnosis not on watch-list added", UNLISTED)):
            for d in names:
                summ = faithful + f" These results show that you have {d}."
                bump(group, not verify_summary_grounding(summ, text, labs)["is_valid"],
                     not verify_response_against_source(summ, text)[1])
    for t in tallies.values():
        t["summary_verifier_rate"] = round(t["summary_verifier"] / t["n"], 4)
        t["chat_verifier_rate"] = round(t["chat_verifier"] / t["n"], 4)
        t["without_verifier"] = 0
    return {"reports": faithful_total, "faithful_summaries_flagged": faithful_flagged,
            "perturbations": tallies, "undetected_number_changes": coincidental}


# ------------------------------------------- E4 translation number check
_DEV = str.maketrans("0123456789", "०१२३४५६७८९")


def _numbers_no_normalise(text):
    return sorted(re.findall(r"(?<![\w.])[+-]?\d+(?:[.,]\d+)*(?![\w.])", text))


def e4_translation():
    items = E.load_dataset("translation_eval.json")["items"]
    variants = {k: [] for k in ("faithful (Latin digits)", "faithful (Devanagari digits)",
                                "one number changed", "one number dropped",
                                "decimal point moved", "extra number added")}
    for it in items:
        src, hi = it["source"], it.get("reference_hi")
        if not hi or not M.numbers_in(src):
            continue
        nums = re.findall(r"\d+(?:\.\d+)?", hi)
        first = nums[0]
        variants["faithful (Latin digits)"].append((src, hi, True))
        variants["faithful (Devanagari digits)"].append((src, hi.translate(_DEV), True))
        bumped = first[:-1] + str((int(first[-1]) + 1) % 10)
        variants["one number changed"].append((src, hi.replace(first, bumped, 1), False))
        variants["one number dropped"].append((src, hi.replace(first, "", 1), False))
        moved = first.replace(".", "") if "." in first else first[:-1] + "." + first[-1]
        variants["decimal point moved"].append((src, hi.replace(first, moved, 1), False))
        variants["extra number added"].append((src, hi + " दिन में 2 बार।", False))

    def full(src, out):
        try:
            TV.preserve_numbers(src, out)
            return True
        except ValueError:
            return False

    def no_norm(src, out):
        return _numbers_no_normalise(src) == _numbers_no_normalise(out)

    res = {}
    for kind, rows in variants.items():
        should_pass = rows[0][2] if rows else True
        r = {"n": len(rows), "expected": "accept" if should_pass else "reject"}
        for label, fn in (("full_check", full), ("without_digit_normalisation", no_norm)):
            ok = sum(1 for s, o, exp in rows if fn(s, o) == exp)
            r[label] = f"{ok}/{len(rows)}"
        r["no_check"] = f"{len(rows) if should_pass else 0}/{len(rows)}"
        res[kind] = r
    return {"sentences_with_numbers": len(variants["faithful (Latin digits)"]), "variants": res}


# --------------------------------------------------- E5 de-identification
def e5_deid():
    cases = load("deid_cases.json")["cases"]
    ids = leaked = clinical = kept = 0
    leaks = []
    for c in cases:
        out = deidentify_prompt_text(c["text"], mode="deidentified")
        for ident in c["identifiers"]:
            ids += 1
            if ident.lower() in out.lower():
                leaked += 1
                leaks.append(ident)
        for cl in c["clinical"]:
            clinical += 1
            kept += int(cl in out)
    return {"headers": len(cases), "identifiers": ids,
            "leaked_with_deidentification": leaked, "leaked_without": ids,
            "leaked_items": leaks, "clinical_strings": clinical, "clinical_kept": kept}


# ------------------------------------------------------ E6 safety router
def _load_router():
    path = os.path.join(BACKEND, "app", "api", "v1", "chat.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    keep = [n for n in tree.body if (isinstance(n, ast.Assign) and any(
        getattr(t, "id", "") == "_EMERGENCY_RE" for t in n.targets))
        or (isinstance(n, ast.FunctionDef) and n.name == "local_classify_intent")]
    ns = {"re": re}
    exec(compile(ast.Module(body=keep, type_ignores=[]), path, "exec"), ns)
    return ns["local_classify_intent"]


def e6_safety():
    classify = _load_router()
    data = load("safety_messages.json")
    out = {}
    misses = {}
    for group, expected in (("emergency", "emergency"), ("diagnosis", "diagnosis"), ("general", "general")):
        preds = [classify(m) for m in data[group]]
        out[group] = {"n": len(preds), "routed_correctly": sum(p == expected for p in preds),
                      "predicted": {k: preds.count(k) for k in set(preds)}}
        misses[group] = [m for m, p in zip(data[group], preds) if p != expected]
    return {"results": out, "misrouted": misses}


# ---------------------------------------------------- E7 document gate
def e7_gate(cases):
    data = load("gate_documents.json")
    med = list(data["medical"]) + [c["text"] for c in cases]
    def ok(t):
        try:
            validate_medical_document(t)
            return True
        except Exception:
            return False
    med_pass = [ok(t) for t in med]
    non_rej = [not ok(t) for t in data["non_medical"]]
    return {"medical_docs": len(med), "medical_accepted": sum(med_pass),
            "medical_wrongly_rejected": [t.splitlines()[0] for t, p in zip(med, med_pass) if not p],
            "non_medical_docs": len(non_rej), "non_medical_rejected": sum(non_rej),
            "non_medical_let_through": [t.splitlines()[0] for t, r in zip(data["non_medical"], non_rej) if not r],
            "without_gate_non_medical_sent_to_llm": len(non_rej)}


# ---------------------------------------------------- E8 OCR robustness
def e8_ocr(cases):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    import pytesseract

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    text_cases = [c for c in cases if c.get("layout", "").find("PDF") < 0]

    def render(text):
        lines = text.splitlines()
        img = Image.new("L", (1400, 60 + 40 * len(lines)), 255)
        d = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            d.text((50, 30 + 40 * i), line, fill=0, font=font)
        return img

    def jpeg(img, q):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q)
        buf.seek(0)
        return Image.open(buf).convert("L")

    conditions = {
        "Clean render": lambda im: im,
        "Gaussian blur r=1.5": lambda im: im.filter(ImageFilter.GaussianBlur(1.5)),
        "Gaussian blur r=2.5": lambda im: im.filter(ImageFilter.GaussianBlur(2.5)),
        "Half resolution": lambda im: im.resize((im.width // 2, im.height // 2)),
        "JPEG quality 10": lambda im: jpeg(im, 10),
        "Rotated 3 degrees": lambda im: im.rotate(3, expand=True, fillcolor=255),
    }
    out = {}
    for label, fn in conditions.items():
        started = time.perf_counter()
        ocr_cases = []
        for c in text_cases:
            txt = pytesseract.image_to_string(fn(render(c["text"])), config="--psm 6")
            ocr_cases.append({**c, "text": txt})
        res = E.evaluate_lab_extraction(LX.extract_lab_values_rules, ocr_cases)
        out[label] = {**{k: round(v, 4) for k, v in res["metrics"].items()},
                      "found": sum(v["found"] for v in res["details"]["by_layout"].values()),
                      "gold": res["n"],
                      "by_layout": {k: f'{v["found"]}/{v["gold"]}' for k, v in res["details"]["by_layout"].items()},
                      "seconds": round(time.perf_counter() - started, 1)}
    return {"reports": len(text_cases), "conditions": out}


# ------------------------------------------------------- E9 retrieval
def e9_retrieval():
    passages = E.read_knowledge_passages(os.path.join(BACKEND, "data", "knowledge"))
    queries = E.load_dataset("retrieval_eval.json")["queries"]
    rng = random.Random(42)
    rand_orders = {}

    def random_rank(q):
        if q not in rand_orders:
            order = list(range(len(passages)))
            rng.shuffle(order)
            rand_orders[q] = order
        return rand_orders[q]

    out = {}
    for label, ranker in (("No retrieval (first passages in file order)", lambda q: list(range(len(passages)))),
                          ("Random passages (seed 42)", random_rank),
                          ("BM25 keyword retrieval", E.bm25_ranker(passages))):
        r = E.evaluate_retrieval(ranker, passages, queries)
        out[label] = {k: round(v, 4) for k, v in r["metrics"].items()}
    return {"queries": len(queries), "passages": len(passages), "rankers": out}


def main():
    cases = lab_cases()
    started = time.time()
    results = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "E1_parser_ablation": e1_parsers(cases),
        "E1b_rule_flags": e1_flags(cases),
        "E2_name_normalisation": e2_names(),
        "E3_grounding_verifier": e3_grounding(cases),
        "E4_translation_number_check": e4_translation(),
        "E5_deidentification": e5_deid(),
        "E6_safety_router": e6_safety(),
        "E7_document_gate": e7_gate(cases),
        "E9_retrieval": e9_retrieval(),
    }
    if "--no-ocr" not in sys.argv:
        results["E8_ocr_robustness"] = e8_ocr(cases)
    results["runtime_seconds"] = round(time.time() - started, 1)
    path = os.path.join(OUT, "ablation_results.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(json.dumps(results, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
