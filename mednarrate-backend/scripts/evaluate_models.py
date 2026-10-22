"""Measure every model MedNarrate uses and store the results for the UI.

Run from the ``mednarrate-backend`` folder, with the same ``.env`` the backend
uses (API keys for the hosted models, ``VOICE_INPUT_ENABLED=true`` for speech):

    python scripts/evaluate_models.py                 # everything that can run
    python scripts/evaluate_models.py --only ner,lab  # selected parts
    python scripts/evaluate_models.py --quick         # fewer translation languages

Results go to ``app/ml/artifacts/model_report.json``, which the admin portal and
the mobile app read. A part that cannot run here (no key, no model download) is
recorded as failed with the reason; nothing is ever filled in by hand.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml import evaluators as E  # noqa: E402
from app.ml import metrics as M  # noqa: E402
from app.ml import model_report as R  # noqa: E402
from app.ml import xai_examples as X  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(BACKEND_DIR, "data", "knowledge")
LANGUAGE_NAMES = {
    "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "bn": "Bengali", "mr": "Marathi",
}

_loop = asyncio.new_event_loop()


def run(coro):
    return _loop.run_until_complete(coro)


def _with_retry(fn, tries=3, delay=2.0):
    last = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - rate limits etc.
            last = exc
            time.sleep(delay * (attempt + 1))
    raise last


# --------------------------------------------------------------- parts
def part_ner(store, args):
    from app.services.model_registry import get_ner_pipeline

    pipe = get_ner_pipeline()

    def predict(text):
        return [
            {"start": int(e["start"]), "end": int(e["end"]),
             "entity_group": str(e["entity_group"]), "score": float(e["score"])}
            for e in pipe(text)
        ]

    data = E.load_dataset("ner_eval.json")
    R.record_result(store, "ner", E.evaluate_ner(predict, data["items"]))
    store["xai_examples"]["ner"] = X.ner_examples(predict)


def _retrieval(store, key, embed_docs, embed_query=None):
    passages = E.read_knowledge_passages(KNOWLEDGE_DIR)
    queries = E.load_dataset("retrieval_eval.json")["queries"]
    result = E.evaluate_retrieval(
        E.embedding_ranker(passages, embed_docs, embed_query), passages, queries
    )
    baseline = E.evaluate_retrieval(E.bm25_ranker(passages), passages, queries)
    result["details"]["baseline_bm25"] = {
        k: v for k, v in baseline["metrics"].items() if k != "avg_latency_ms"
    }
    R.record_result(store, key, result)


def part_retrieval_gemini(store, args):
    # Use the Gemini embedder directly: get_embedder() follows PRIMARY_LLM_PROVIDER,
    # which is "dev_gemini" on a development setup and has no embedder of its own.
    from app.services.embedding_provider import _gemini_embedder

    embed = _gemini_embedder()
    if embed is None:
        raise RuntimeError("No usable GEMINI_API_KEY in .env (needed for Gemini embeddings).")
    _retrieval(
        store, "retrieval_gemini",
        lambda texts: [_with_retry(lambda t=t: embed(t, "retrieval_document")) for t in texts],
        lambda q: _with_retry(lambda: embed(q, "retrieval_query")),
    )


def part_retrieval_minilm(store, args):
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    fn = DefaultEmbeddingFunction()
    _retrieval(store, "retrieval_minilm", lambda texts: [list(map(float, v)) for v in fn(texts)])


def _llm_translate(provider):
    def translate(source, lang):
        prompt = (
            f"Translate this medical sentence into {LANGUAGE_NAMES.get(lang, lang)} "
            f"(native script). Keep every number and unit exactly as written. "
            f"Return only the translation.\n\n{source}"
        )
        return provider(prompt)
    return translate


def _translation_data(args):
    data = E.load_dataset("translation_eval.json")
    if args.quick:
        data["languages"] = ["hi", "ta"]
    return data


def part_llm(store, args):
    from app.services.llm_client import generate
    from app.services.prompts import RAG_SYSTEM_PROMPT

    def answer(question, context):
        prompt = RAG_SYSTEM_PROMPT.format(context=context, history="", question=question)
        return _with_retry(lambda: run(generate(prompt, timeout=60.0, thinking_level="LOW")))

    qa = E.evaluate_grounded_qa(answer, E.load_dataset("grounded_qa_eval.json"))
    tr = E.evaluate_translation(
        _llm_translate(lambda p: _with_retry(lambda: run(generate(p, timeout=60.0)))),
        _translation_data(args),
    )
    metrics = {**qa["metrics"]}
    for key in ("number_preservation", "sentences_with_all_numbers_kept", "chrf_hindi"):
        if key in tr["metrics"]:
            metrics[key] = tr["metrics"][key]
    R.record_result(store, "llm", {
        "n": qa["n"] + tr["n"],
        "metrics": metrics,
        "details": {"grounded_qa": qa["details"], "translation": {
            **tr["details"], "avg_latency_ms": tr["metrics"]["avg_latency_ms"]}},
    })


def part_qwen(store, args):
    from app.services.llm_client import LocalProvider

    provider = LocalProvider()

    def call(prompt):
        # A test sentence needs a short translation, not the provider's default
        # 2,048-token chat budget. Bound generation so a rambling answer cannot
        # consume the entire 180-second evaluation timeout.
        return run(provider.generate(prompt, timeout=180.0, config={"max_output_tokens": 192}))["content"]

    result = E.evaluate_translation(_llm_translate(call), _translation_data(args))
    R.record_result(store, "qwen", result)


def _speak(text, voice, workdir, name):
    aiff = os.path.join(workdir, name + ".aiff")
    wav = os.path.join(workdir, name + ".wav")
    subprocess.run(["say", "-v", voice, "-o", aiff, text], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", aiff, wav], check=True)
    with open(wav, "rb") as fh:
        return fh.read()


def part_stt(store, args):
    from app.services import speech_service

    if not speech_service.is_enabled():
        raise RuntimeError("Voice input is off: set VOICE_INPUT_ENABLED=true and GROQ_API_KEY in .env.")
    if not (shutil.which("say") and shutil.which("afconvert")):
        raise RuntimeError("Needs macOS 'say' and 'afconvert' to create the test audio.")
    data = E.load_dataset("stt_eval.json")
    clips = []
    with tempfile.TemporaryDirectory() as tmp:
        for lang, voice in (("en", "Samantha"), ("hi", "Lekha")):
            key = "english" if lang == "en" else "hindi"
            for i, sentence in enumerate(data[key]):
                clips.append({"language": lang, "reference": sentence,
                              "audio": _speak(sentence, voice, tmp, f"{lang}{i}")})
    def transcribe(audio, lang):
        return _with_retry(lambda: run(speech_service.transcribe(audio, lang)).text)
    R.record_result(store, "stt", E.evaluate_stt(transcribe, clips),
                    note="Test audio is computer-generated speech, so these error rates are optimistic.")


def part_lab(store, args):
    from app.services.lab_value_extractor import extract_lab_values_rules
    import fitz  # PyMuPDF, already a backend dependency

    cases = E.load_dataset("lab_extraction_eval.json")["cases"]
    for case in cases:
        pdf = os.path.join(BACKEND_DIR, "..", case.get("pdf", "")) if case.get("pdf") else None
        if "text" not in case and pdf and os.path.exists(pdf):
            with fitz.open(pdf) as doc:
                case["text"] = "\n".join(page.get_text() for page in doc)
    cases = [c for c in cases if c.get("text")]
    R.record_result(store, "lab", E.evaluate_lab_extraction(extract_lab_values_rules, cases),
                    note="Rule parsers only; production adds an LLM fall-back for layouts they miss.")


def part_xai(store, args):
    from app.ml.medical_classifier import MedicalReportClassifier

    store["xai_examples"]["classifier"] = X.classifier_examples(MedicalReportClassifier())
    store["xai_examples"]["lab"] = X.lab_examples()


PARTS = {
    "ner": part_ner,
    "retrieval_gemini": part_retrieval_gemini,
    "retrieval_minilm": part_retrieval_minilm,
    "llm": part_llm,
    "qwen": part_qwen,
    "stt": part_stt,
    "lab": part_lab,
    "xai": part_xai,
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma list of: " + ", ".join(PARTS))
    ap.add_argument("--quick", action="store_true", help="translate into Hindi and Tamil only")
    ap.add_argument("--out", help="write results here instead of the default file")
    ap.add_argument("--markdown", help="also write the results as Markdown (default: ../docs/MODEL_RESULTS.md)")
    ap.add_argument("--no-markdown", action="store_true", help="do not write the Markdown results file")
    args = ap.parse_args(argv)

    wanted = [p.strip() for p in args.only.split(",")] if args.only else list(PARTS)
    unknown = [p for p in wanted if p not in PARTS]
    if unknown:
        ap.error("unknown part(s): " + ", ".join(unknown))

    # Development mode makes SQLAlchemy print every query; keep the progress output readable.
    import logging
    logging.getLogger("sqlalchemy.engine.Engine").disabled = True

    store = R.load_store(args.out)
    store["environment"] = {"python": platform.python_version(), "platform": platform.platform()}
    failures = 0
    for name in wanted:
        print(f"==> {name} ...", flush=True)
        started = time.perf_counter()
        try:
            PARTS[name](store, args)
            print(f"    done in {time.perf_counter() - started:.1f}s")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            reason = f"{type(exc).__name__}: {exc}"
            print(f"    FAILED - {reason}")
            if os.environ.get("EVAL_DEBUG"):
                traceback.print_exc()
            if name != "xai":
                R.record_result(store, name, None, error=reason)
        R.save_store(store, args.out)  # save after every part so a crash loses nothing

    report = R.build_report(args.out)
    if not args.no_markdown:
        md_path = args.markdown or os.path.join(BACKEND_DIR, "..", "docs", "MODEL_RESULTS.md")
        os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(R.export_markdown(report))
        print(f"Wrote {os.path.abspath(md_path)}")
    s = report["summary"]
    print(f"\nEvaluated {s['evaluated']}/{s['total']} models "
          f"({s['deep_learning_evaluated']}/{s['deep_learning_total']} deep-learning).")
    for m in report["models"]:
        line = ", ".join(f"{x['label']}={x['value']:.3f}" for x in m["metrics"][:3])
        print(f"  {m['status']:<14} {m['name'][:55]:<55} {line}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
