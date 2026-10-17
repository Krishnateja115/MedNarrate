"""Translate a synthetic report with the REAL providers and say what happens.

    cd mednarrate-backend && .venv/bin/python -m app.translation_check hi
    .venv/bin/python -m app.translation_check all
    (or, in Docker: docker compose exec backend python -m app.translation_check hi)

For every language it prints PASS or FAIL, how long it took, the provider chain
used and, on failure, the exact reason (invalid key, quota, unknown model,
timeout, answer rejected by the safety validator...). No patient data and no API
keys are involved or printed. Run `python -m app.llm_check` first if every
language fails.
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid

from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS, SUPPORTED_TRANSLATION_LANGUAGES
from app.core.config import settings
from app.exceptions import TranslationServiceError
from app.services.llm_client import generate_translation_with_provider
from app.services.provider_health import hint_for, provider_health
from app.services.translation_planner import execute_translation_plan, resolve_translation_providers
from app.services.translation_validation import validate_translation

CLINICIAN = (
    "Complete blood count shows mild microcytic anaemia. Haemoglobin 10.2 g/dL (13.0 - 17.0 g/dL) is low; "
    "MCHC 36.1 g/dL (31.5 - 34.5 g/dL) is high. Other indices are within the reference range."
)
PATIENT = (
    "Your blood count shows that your haemoglobin is lower than usual, which can cause tiredness. "
    "Please discuss these results with your doctor."
)
FINDINGS = [
    {"test_name": "Haemoglobin", "value": 10.2, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "flag": "low",
     "explanation": "Haemoglobin carries oxygen in the blood. A value of 10.2 g/dL is below the reference range of 13.0 - 17.0 g/dL."},
    {"test_name": "MCHC", "value": 36.1, "unit": "g/dL", "ref_low": 31.5, "ref_high": 34.5, "flag": "high",
     "explanation": "MCHC describes how concentrated haemoglobin is inside red cells. 36.1 g/dL is above the reference range."},
]
MEDS = [
    {"medication_name": "Ferrous sulfate", "dosage": "200 mg", "frequency": "once daily",
     "times_of_day": ["08:00", "morning"], "instructions": "Take after food."},
]


async def check_language(code: str) -> bool:
    name = SUPPORTED_TRANSLATION_LANGUAGES[code]
    providers = resolve_translation_providers()
    started = time.monotonic()
    try:
        parsed = await execute_translation_plan(
            target_lang_name=name,
            lang_code=code,
            clinician_summary=CLINICIAN,
            patient_summary=PATIENT,
            abnormal_findings_source=FINDINGS,
            meds_list=MEDS,
            unique_params=[f["test_name"] for f in FINDINGS],
            providers=providers,
            validate_func=validate_translation,
            required_ui_label_keys=REQUIRED_UI_LABEL_KEYS,
            request_id=f"check-{uuid.uuid4().hex[:8]}",
            generate_func=generate_translation_with_provider,
        )
        validate_translation(parsed, code, CLINICIAN, PATIENT, FINDINGS, MEDS, REQUIRED_UI_LABEL_KEYS)
    except TranslationServiceError as exc:
        reason = exc.reason or "unknown_error"
        print(f"  {code} {name:<10} FAIL  {time.monotonic() - started:5.1f}s  {reason}: {hint_for(reason)}")
        return False
    except Exception as exc:  # noqa: BLE001 - diagnostics must never crash
        print(f"  {code} {name:<10} FAIL  {time.monotonic() - started:5.1f}s  {type(exc).__name__}: {str(exc)[:140]}")
        return False
    sample = (parsed["patient_summary"] or "")[:60].replace("\n", " ")
    print(f"  {code} {name:<10} PASS  {time.monotonic() - started:5.1f}s  {sample}...")
    return True


async def main(argv: list[str]) -> int:
    wanted = [a for a in argv if a != "all"]
    codes = (
        [c for c in SUPPORTED_TRANSLATION_LANGUAGES if c != "en"]
        if "all" in argv
        else [c for c in wanted if c in SUPPORTED_TRANSLATION_LANGUAGES and c != "en"] or ["hi"]
    )
    print(f"ENVIRONMENT={settings.ENVIRONMENT}  providers={','.join(resolve_translation_providers())}")
    try:
        from app.services.llm_client import get_resolved_ai_config

        cfg = await get_resolved_ai_config()
        key = str(cfg.get("api_key") or "")
        tail = f"...{key[-4:]}" if len(key) >= 8 else "(none)"
        print(
            f"Admin/DB AI config: primary={cfg.get('primary_provider')} model={cfg.get('model_name')} "
            f"gemini key from {cfg.get('api_key_source')} ({tail})"
        )
        from app.services.llm_client import DevGeminiProvider

        print(f"Direct Gemini model actually used: {DevGeminiProvider().get_model_name(cfg)}")
    except Exception as exc:  # diagnostics only
        print(f"(could not read AI config: {type(exc).__name__})")
    print()
    results = []
    for code in codes:
        results.append(await check_language(code))
    cooling = provider_health.snapshot()
    if cooling:
        print("\nProviders on cool-down after this run:")
        for provider, info in cooling.items():
            print(f"  {provider}: {info['kind']} (retry in {info['retry_in_seconds']}s)")
            if info.get("last_error"):
                print(f"      {info['last_error']}")
    ok = all(results)
    print("\nTranslation is working." if ok else "\nTranslation FAILED - fix the reasons above (see also: python -m app.llm_check).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
