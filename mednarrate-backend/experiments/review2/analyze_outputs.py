"""Second-pass checks on the saved model replies (no model is called).

1. Flag contradictions in patient summaries: a sentence that quotes a lab
   value and calls it normal / high / low against the rule-based flag.
2. Condition words in a summary that the report itself never mentions.
3. The summary grounding verifier, as shipped and with the exemption for the
   phrase "not provided" removed (the patient prompt asks for a section titled
   "Information Not Provided", which switches the diagnosis check off).
4. Degenerate translations (a word repeated five or more times in a row).

    PYTHONPATH=. python experiments/review2/analyze_outputs.py [slm|llm]
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
sys.path.insert(0, HERE)

from app.services import lab_value_extractor as LX  # noqa: E402
from app.services import validation as V  # noqa: E402
from run_slm_comparison import lab_cases  # noqa: E402

CONDITIONS = ["diabetes", "prediabetes", "anemia", "anaemia", "infection", "inflammation",
              "hypothyroidism", "hyperthyroidism", "kidney disease", "liver disease",
              "fatty liver", "leukemia", "cancer", "heart disease", "bleeding disorder",
              "clotting disorder", "vitamin deficiency", "dehydration", "malnutrition"]
WORDS = {"normal": r"\b(normal|within|healthy range|in range)\b",
         "high": r"\b(high|higher|above|elevated|raised|increased)\b",
         "low": r"\b(low|lower|below|decreased|reduced|deficien\w*)\b"}


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def contradictions(summary, labs):
    found = []
    for lab in labs:
        flag = lab.get("flag")
        if flag not in {"normal", "high", "low"}:
            continue
        val = "%g" % float(lab["value"])
        for s in sentences(summary):
            if not re.search(r"(?<![\d.])" + re.escape(val) + r"(?![\d])", s):
                continue
            low = s.lower()
            said = {k for k, rx in WORDS.items() if re.search(rx, low)}
            # "lower than the normal range" mentions both; the direction word wins.
            if {"high", "low"} & said:
                said.discard("normal")
            if said and flag not in said:
                found.append({"test": lab["test_name"], "value": val, "flag": flag,
                              "sentence": s[:160]})
            break
    return found


def verifier_without_exemption(summary, source, labs):
    s, src = summary.lower(), source.lower()
    hits = [d for d in ["diabetes", "type 2 diabetes", "heart failure", "congestive heart failure",
                        "cancer", "leukemia", "lymphoma", "stroke", "kidney failure", "renal failure"]
            if d in s and d not in src and f"no {d}" not in s]
    return hits


def main(tag):
    path = os.path.join(HERE, "results", f"{tag}_replies.jsonl")
    replies = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            replies[rec["key"]] = rec["reply"]
    out = {"summaries": {}, "translation": {}}
    for case in lab_cases():
        labs = LX.extract_lab_values_rules(case["text"])
        for variant in ("with_structured_values", "text_only"):
            key = f"S5|{variant}|{case['id']}"
            if key not in replies:
                continue
            summ = replies[key]
            low_src = case["text"].lower()
            low_sum = summ.lower()
            shipped = V.verify_summary_grounding(summ, case["text"], labs)
            out["summaries"].setdefault(variant, []).append({
                "report": case["id"],
                "flag_contradictions": contradictions(summ, labs),
                "conditions_not_in_report": [c for c in CONDITIONS if c in low_sum and c not in low_src],
                "shipped_verifier_valid": shipped["is_valid"],
                "diagnoses_caught_without_exemption": verifier_without_exemption(summ, case["text"], labs),
                "mentions_information_not_provided": "not provided" in low_sum,
            })
    agg = {}
    for variant, rows in out["summaries"].items():
        agg[variant] = {
            "summaries": len(rows),
            "flag_contradictions": sum(len(r["flag_contradictions"]) for r in rows),
            "summaries_with_contradiction": sum(bool(r["flag_contradictions"]) for r in rows),
            "summaries_naming_condition_not_in_report": sum(bool(r["conditions_not_in_report"]) for r in rows),
            "shipped_verifier_passed": sum(r["shipped_verifier_valid"] for r in rows),
            "summaries_flagged_if_exemption_removed": sum(bool(r["diagnoses_caught_without_exemption"]) for r in rows),
            "summaries_containing_not_provided": sum(r["mentions_information_not_provided"] for r in rows),
        }
    out["summary_aggregate"] = agg
    tr = [(k, v) for k, v in replies.items() if k.startswith("S3|")]
    degenerate = [k for k, v in tr if re.search(r"(\b\S+\b)(?:\s+\1){4,}", v)
                  or re.search(r"(.{2,12})\1{4,}", v)]
    by_lang = {}
    for k, _ in tr:
        lang = k.split("|")[1]
        by_lang.setdefault(lang, [0, 0])
        by_lang[lang][1] += 1
        by_lang[lang][0] += int(k in degenerate)
    out["translation"] = {"outputs": len(tr), "degenerate_repetition": len(degenerate),
                          "by_language": {k: f"{a}/{b}" for k, (a, b) in by_lang.items()}}
    with open(os.path.join(HERE, "results", f"{tag}_analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps({"summary_aggregate": agg, "translation": out["translation"]}, indent=1))
    for variant, rows in out["summaries"].items():
        for r in rows:
            print(variant, r["report"], [ (c["test"], c["flag"]) for c in r["flag_contradictions"]], r["conditions_not_in_report"], r["diagnoses_caught_without_exemption"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "slm")
