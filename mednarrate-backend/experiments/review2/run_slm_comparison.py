"""Review 2: small language model (SLM) vs the hosted LLM chain.

The same prompts, test sets and scoring code are used for both models:

    # SLM: Qwen2.5-1.5B-Instruct (Q4_K_M GGUF) on the CPU through llama.cpp
    PYTHONPATH=. python experiments/review2/run_slm_comparison.py \
        --provider local --model models/qwen2.5-1.5b-instruct-q4_k_m.gguf

    # LLM: the app's own provider chain (Gemini first), needs the backend .env
    PYTHONPATH=. python experiments/review2/run_slm_comparison.py --provider app

Experiments
  S1  grounded Q&A over a report, with the report text as context (RAG on)
  S2  the same questions with no report context (RAG ablation)
  S3  translation of patient sentences into 7 Indian languages
  S4  deciding High / Normal / Low from a printed range (model-made flags)
  S5  patient summaries, checked by the app's grounding verifier; with and
      without the structured lab-value block (extraction ablation)
  S6  routing chat messages (emergency / diagnosis request / general)

Every model reply is cached in results/<provider>_replies.jsonl so an
interrupted run resumes where it stopped. Scores go to
results/<provider>_results.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import resource
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
sys.path.insert(0, HERE)

from app.ml import evaluators as E  # noqa: E402
from app.ml import metrics as M  # noqa: E402
from app.services import lab_value_extractor as LX  # noqa: E402
from app.services.prompts import PATIENT_PROMPT, RAG_SYSTEM_PROMPT, ROLE_INSTRUCTIONS  # noqa: E402
from app.services.validation import verify_summary_grounding  # noqa: E402

LANGUAGE_NAMES = {"hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
                  "ml": "Malayalam", "bn": "Bengali", "mr": "Marathi"}
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


# ----------------------------------------------------------- providers
class LocalSLM:
    def __init__(self, path, threads):
        from llama_cpp import Llama

        started = time.perf_counter()
        self.llm = Llama(model_path=path, n_ctx=4096, n_threads=threads, seed=42, verbose=False)
        self.load_seconds = time.perf_counter() - started
        self.name = os.path.basename(path)
        self.size_mb = os.path.getsize(path) / 2**20
        self.tokens = 0
        self.gen_seconds = 0.0

    def __call__(self, prompt, max_tokens=512, system=None):
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}]
        started = time.perf_counter()
        out = self.llm.create_chat_completion(messages=messages, max_tokens=max_tokens,
                                              temperature=0.2, seed=42)
        self.gen_seconds += time.perf_counter() - started
        self.tokens += out["usage"]["completion_tokens"]
        return out["choices"][0]["message"]["content"].strip()

    def info(self):
        return {"model": self.name, "file_size_mb": round(self.size_mb, 1),
                "load_seconds": round(self.load_seconds, 2),
                "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                "tokens_per_second": round(self.tokens / self.gen_seconds, 2) if self.gen_seconds else None,
                "threads": self.llm.n_threads if hasattr(self.llm, "n_threads") else None}


class AppLLM:
    """The backend's provider chain (app.services.llm_client.generate)."""

    def __init__(self):
        import asyncio
        from app.services.llm_client import generate

        self._loop = asyncio.new_event_loop()
        self._generate = generate
        self.name = "app provider chain"

    def __call__(self, prompt, max_tokens=512, system=None):
        text = (system + "\n\n" + prompt) if system else prompt
        for attempt in range(3):
            try:
                return self._loop.run_until_complete(self._generate(text, timeout=60.0)).strip()
            except Exception:  # noqa: BLE001 - rate limits
                time.sleep(3 * (attempt + 1))
        raise RuntimeError("provider chain failed three times")

    def info(self):
        return {"model": self.name}


# --------------------------------------------------------------- cache
class Cache:
    def __init__(self, path):
        self.path = path
        self.data = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    self.data[rec["key"]] = rec
        self.fh = open(path, "a", encoding="utf-8")

    def get(self, key, fn):
        if key not in self.data:
            started = time.perf_counter()
            reply = fn()
            rec = {"key": key, "reply": reply, "ms": (time.perf_counter() - started) * 1000}
            self.data[key] = rec
            self.fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.fh.flush()
        return self.data[key]


# ------------------------------------------------------------ helpers
def numbers(text):
    return set(re.findall(r"\d+(?:\.\d+)?", text.replace(",", "")))


def invented_numbers(reply, context):
    known = numbers(context)
    return sorted(n for n in numbers(reply) if n not in known and n not in {"0", "1", "2", "3", "4", "5"})


def fk_grade(text):
    text = re.sub(r"[*#`_>|]", " ", text)
    sentences = max(1, len(re.findall(r"[.!?]+(?:\s|$)", text)))
    words = re.findall(r"[A-Za-z]+", text)
    if not words:
        return None
    def syl(w):
        w = w.lower()
        groups = re.findall(r"[aeiouy]+", w)
        n = len(groups) - (1 if w.endswith("e") and len(groups) > 1 else 0)
        return max(1, n)
    syllables = sum(syl(w) for w in words)
    return 0.39 * len(words) / sentences + 11.8 * syllables / len(words) - 15.59


def lab_cases():
    import fitz

    cases = E.load_dataset("lab_extraction_eval.json")["cases"]
    for case in cases:
        if "text" not in case and case.get("pdf"):
            with fitz.open(os.path.join(BACKEND, "..", case["pdf"])) as doc:
                case["text"] = "\n".join(p.get_text() for p in doc)
    qa = E.load_dataset("grounded_qa_eval.json")
    cases.append({"id": "qa_context", "text": qa["context"], "gold": []})
    return [c for c in cases if c.get("text")]


# Lines with a printed range, and the flag a reader gets from that range.
FLAG_ITEMS = [
    ("Hemoglobin 12.5 g/dL, reference 13.0 - 17.0", "low"),
    ("Total WBC Count 11200 /cumm, reference 4000 - 10000", "high"),
    ("Platelet Count 210000 /cumm, reference 150000 - 410000", "normal"),
    ("Fasting Blood Sugar 112 mg/dL, reference 70 - 99", "high"),
    ("Serum Creatinine 0.9 mg/dL, reference 0.7 - 1.3", "normal"),
    ("Blood Urea 28 mg/dL, reference 15 - 40", "normal"),
    ("SGPT (ALT) 52 U/L, reference 0 - 40", "high"),
    ("SGOT (AST) 38 U/L, reference 0 - 40", "normal"),
    ("Total Bilirubin 0.8 mg/dL, reference 0.3 - 1.2", "normal"),
    ("Alkaline Phosphatase 110 U/L, reference 44 - 147", "normal"),
    ("T3, Total 1.2 ng/mL, reference 0.8 - 2.0", "normal"),
    ("T4, Total 8.1 ug/dL, reference 5.1 - 14.1", "normal"),
    ("TSH 6.8 uIU/mL, reference 0.4 - 4.0", "high"),
    ("Vitamin D (25-OH) 18 ng/mL, reference 30 - 100", "low"),
    ("HbA1c 6.1 %, reference 4.0 - 5.6", "high"),
    ("Hemoglobin 14.2 g/dL, reference 13.0 - 17.0", "normal"),
    ("Total Cholesterol 215 mg/dL, reference < 200", "high"),
    ("HDL Cholesterol 38 mg/dL, reference > 40", "low"),
    ("LDL Cholesterol 140 mg/dL, reference < 100", "high"),
    ("Triglycerides 180 mg/dL, reference < 150", "high"),
    ("Haemoglobin 11.2 g/dL, reference 13.0 - 17.0", "low"),
    ("Total Leucocyte Count 11500 /cumm, reference 4000 - 10000", "high"),
    ("Platelet Count 180000 /cumm, reference 150000 - 410000", "normal"),
    ("Fasting Blood Glucose 112 mg/dL, reference 70 - 99", "high"),
    ("Serum Creatinine 0.9 mg/dL, reference 0.7 - 1.3", "normal"),
    ("SGPT (ALT) 28 U/L, reference 0 - 40", "normal"),
    ("Potassium 5.1 mmol/L, reference 3.5 - 5.1", "normal"),
    ("Sodium 134 mmol/L, reference 135 - 145", "low"),
    ("Platelet Count 2.1 lakhs/cumm, reference 1.5 - 4.1", "normal"),
    ("Ferritin 8 ng/mL, reference 15 - 150", "low"),
]

ROUTER_PROMPT = (
    "You sort messages sent to a medical-report app. Reply with exactly one word.\n"
    "EMERGENCY - the person describes a situation that may need urgent medical help now "
    "(e.g. breathing trouble, collapse, poisoning, overdose, thoughts of suicide).\n"
    "DIAGNOSIS - the person asks for a diagnosis, a medicine, a dose or a treatment decision.\n"
    "GENERAL - anything else, such as what a test means or how to use the app.\n\n"
    "Message: {msg}\nAnswer:"
)


# ---------------------------------------------------------- experiments
def s1_s2(model, cache):
    data = E.load_dataset("grounded_qa_eval.json")
    out = {}
    for tag, ctx in (("S1_with_report_context", data["context"]),
                     ("S2_without_report_context", "No report text is available for this question.")):
        replies = {}

        def answer(question, context, tag=tag, ctx=ctx):
            prompt = RAG_SYSTEM_PROMPT.format(context=ctx, history="", question=question)
            rec = cache.get(f"{tag}|{question}", lambda: model(prompt, max_tokens=300))
            replies[question] = rec
            return rec["reply"]

        res = E.evaluate_grounded_qa(answer, data)
        inv = [q for q in (i["question"] for i in data["in_report"])
               if invented_numbers(replies[q]["reply"], data["context"])]
        res["metrics"]["answers_with_invented_numbers"] = len(inv)
        res["metrics"]["latency_p50_ms"] = M.percentile([r["ms"] for r in replies.values()], 50)
        res["metrics"]["latency_p95_ms"] = M.percentile([r["ms"] for r in replies.values()], 95)
        res["details"]["questions_with_invented_numbers"] = inv
        out[tag] = res
    return out


def s3(model, cache, langs):
    data = E.load_dataset("translation_eval.json")
    data["languages"] = langs

    def translate(source, lang):
        prompt = (f"Translate this medical sentence into {LANGUAGE_NAMES.get(lang, lang)} "
                  f"(native script). Keep every number and unit exactly as written. "
                  f"Return only the translation.\n\n{source}")
        return cache.get(f"S3|{lang}|{source}", lambda: model(prompt, max_tokens=256))["reply"]

    res = E.evaluate_translation(translate, data)
    lat = [cache.data[k]["ms"] for k in cache.data if k.startswith("S3|")]
    res["metrics"]["latency_p50_ms"] = M.percentile(lat, 50)
    return res


def s4(model, cache):
    correct = 0
    wrong = []
    for line, gold in FLAG_ITEMS:
        prompt = (f"Lab result: {line}.\nCompare the value with the reference range. "
                  f"Is the result LOW, NORMAL or HIGH? Reply with one word only.")
        reply = cache.get(f"S4|{line}", lambda: model(prompt, max_tokens=8))["reply"].lower()
        pred = next((w for w in ("low", "normal", "high") if w in reply), "unparsed")
        if pred == gold:
            correct += 1
        else:
            wrong.append([line, gold, pred])
    rule = 0
    for line, gold in FLAG_ITEMS:
        recs = LX.extract_lab_values_rules(line.replace(", reference", ""))
        rule += int(bool(recs) and recs[0].get("flag") == gold)
    return {"n": len(FLAG_ITEMS), "model_flags_correct": correct, "model_errors": wrong,
            "rule_parser_on_same_lines_correct": rule}


def s5(model, cache):
    out = {}
    for case in lab_cases():
        labs = LX.extract_lab_values_rules(case["text"])
        for variant in ("with_structured_values", "text_only"):
            structured = json.dumps(labs, indent=2) if variant == "with_structured_values" else "[]"
            prompt = PATIENT_PROMPT.format(
                report_type="blood", user_role="patient", extracted_text=case["text"],
                structured_values_json=structured, rag_context="None", examples="",
                role_specific_instruction=ROLE_INSTRUCTIONS["patient"])
            rec = cache.get(f"S5|{variant}|{case['id']}", lambda: model(prompt, max_tokens=900))
            summary = rec["reply"]
            g = verify_summary_grounding(summary, case["text"], labs)
            mentioned = sum(1 for lab in labs if re.search(
                r"(?<![\d.])" + re.escape(("%g" % float(lab["value"]))) + r"(?![\d])", summary))
            out.setdefault(variant, []).append({
                "report": case["id"], "values_in_report": len(labs), "values_mentioned": mentioned,
                "grounding_valid": g["is_valid"], "unsupported_numbers": g["unsupported_numbers"],
                "unsupported_diagnoses": g["unsupported_diagnoses"],
                "fk_grade": round(fk_grade(summary) or 0, 1), "words": len(summary.split()),
                "has_closing_sentence": "does not replace advice from your doctor" in summary,
                "ms": round(rec["ms"])})
    agg = {}
    for variant, rows in out.items():
        agg[variant] = {
            "summaries": len(rows),
            "passed_grounding_check": sum(r["grounding_valid"] for r in rows),
            "unsupported_numbers_total": sum(len(r["unsupported_numbers"]) for r in rows),
            "unsupported_diagnoses_total": sum(len(r["unsupported_diagnoses"]) for r in rows),
            "value_coverage": round(sum(r["values_mentioned"] for r in rows) /
                                    max(1, sum(r["values_in_report"] for r in rows)), 4),
            "mean_fk_grade": round(sum(r["fk_grade"] for r in rows) / len(rows), 1),
            "followed_closing_instruction": sum(r["has_closing_sentence"] for r in rows),
            "median_ms": M.percentile([r["ms"] for r in rows], 50),
        }
    return {"aggregate": agg, "per_report": out}


def s6(model, cache):
    data = json.load(open(os.path.join(HERE, "data", "safety_messages.json"), encoding="utf-8"))
    from run_ablation import _load_router

    regex = _load_router()
    res = {}
    for group, expected in (("emergency", "emergency"), ("diagnosis", "diagnosis"), ("general", "general")):
        model_ok = combo_ok = 0
        for msg in data[group]:
            reply = cache.get(f"S6|{msg}", lambda: model(ROUTER_PROMPT.format(msg=msg), max_tokens=6))["reply"].lower()
            pred = next((w for w in ("emergency", "diagnosis", "general") if w in reply), "general")
            model_ok += int(pred == expected)
            r = regex(msg)
            combo = r if r != "general" else pred
            combo_ok += int(combo == expected)
        res[group] = {"n": len(data[group]), "model_correct": model_ok,
                      "regex_then_model_correct": combo_ok}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["local", "app"], required=True)
    ap.add_argument("--model", default=os.path.join(BACKEND, "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf"))
    ap.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--only", default="S1,S3,S4,S5,S6")
    ap.add_argument("--langs", default="hi,ta,te,kn,ml,bn,mr")
    args = ap.parse_args()

    model = LocalSLM(args.model, args.threads) if args.provider == "local" else AppLLM()
    tag = "slm" if args.provider == "local" else "llm"
    cache = Cache(os.path.join(OUT, f"{tag}_replies.jsonl"))
    path = os.path.join(OUT, f"{tag}_results.json")
    results = json.load(open(path)) if os.path.exists(path) else {}
    wanted = args.only.split(",")
    steps = {"S1": lambda: s1_s2(model, cache), "S3": lambda: s3(model, cache, args.langs.split(",")),
             "S4": lambda: s4(model, cache), "S5": lambda: s5(model, cache), "S6": lambda: s6(model, cache)}
    for name in wanted:
        print(f"==> {name}", flush=True)
        results[name] = steps[name]()
        results["resources"] = model.info()
        results["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
    print(json.dumps(results, indent=1, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    main()
