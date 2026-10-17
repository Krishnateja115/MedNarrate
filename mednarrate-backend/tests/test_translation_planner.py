"""Translation planner behaviour with synthetic provider responses (no network)."""

import asyncio
import json
import time

import pytest

from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
from app.core.config import settings
from app.exceptions import TranslationServiceError
from app.services import llm_client
from app.services.provider_health import provider_health
from app.services.translation_labels import get_ui_labels
from app.services.translation_planner import execute_translation_plan
from app.services.translation_validation import _align_to_source, validate_translation

LANGUAGES = {
    "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "bn": "Bengali", "mr": "Marathi",
}


def _native(lang: str) -> str:
    return get_ui_labels(lang)["label_key_finding_expansion_patient"]


def _section(prompt: str, title: str):
    return json.loads(prompt.split(title + "\n", 1)[1].split("\n", 1)[0])


def _text_block(prompt: str, start: str, end: str) -> str:
    return prompt.split(start + "\n", 1)[1].split("\n" + end, 1)[0].strip()


def make_generate(lang: str, calls: list | None = None, delay: float = 0.0):
    """A fake provider that answers any unit correctly, in the target script."""
    text = _native(lang)

    async def generate(prompt: str, provider: str):
        if calls is not None:
            calls.append(provider)
        if delay:
            await asyncio.sleep(delay)
        findings = _section(prompt, "Findings (JSON; translate only the explanation text):")
        meds = _section(prompt, "Medications (JSON):")
        params = _section(prompt, "Test or parameter names to translate (JSON list):")
        clin = _text_block(prompt, "Clinician summary:", "Patient summary:")
        pat = _text_block(prompt, "Patient summary:", "Findings (JSON")
        payload = {
            "clinician_summary": text if clin else "",
            "patient_summary": text if pat else "",
            "abnormal_findings": [
                {
                    "test_name": f["test_name"],
                    "translated_test_name": text.split()[0],
                    "translated_explanation": text,
                }
                for f in findings
            ],
            "medications": [
                {
                    "medication_name": m["medication_name"],
                    "translated_medication_name": text.split()[0],
                    "translated_dosage": m.get("dosage") or "",
                    "translated_frequency": text,
                    "translated_times_of_day": [
                        t if ":" in t else text for t in (m.get("times_of_day") or [])
                    ],
                    "translated_instructions": text if m.get("instructions") else "",
                }
                for m in meds
            ],
            "translated_parameters": [
                {"name": p, "translated": text.split()[0]} for p in params
            ],
        }
        return {"provider": provider, "content": json.dumps(payload, ensure_ascii=False)}

    return generate


def report(n_findings: int = 6):
    findings = [
        {
            "test_name": f"Test {i}",
            "value": 10 + i,
            "unit": "g/dL",
            "flag": "low" if i % 2 else "high",
            "explanation": "This value is outside the reference range. " * 6,
        }
        for i in range(n_findings)
    ]
    meds = [
        {
            "medication_name": "Iron",
            "dosage": "65 mg",
            "frequency": "twice daily",
            "times_of_day": ["08:00", "morning"],
            "instructions": "Take after food",
        }
    ]
    return findings, meds


async def run_plan(lang, generate, providers=("gemini",), findings=None, meds=None, **kw):
    findings, meds_default = (findings, meds) if findings is not None else report()
    meds = meds if meds is not None else meds_default
    return await execute_translation_plan(
        target_lang_name=LANGUAGES[lang],
        lang_code=lang,
        clinician_summary="Clinician summary text " * 8,
        patient_summary="Patient summary text " * 8,
        abnormal_findings_source=findings,
        meds_list=meds,
        unique_params=[f["test_name"] for f in findings],
        providers=list(providers),
        validate_func=validate_translation,
        required_ui_label_keys=REQUIRED_UI_LABEL_KEYS,
        request_id="t",
        generate_func=generate,
        **kw,
    )


class QuotaError(Exception):
    status_code = 429


@pytest.mark.parametrize("lang", list(LANGUAGES))
async def test_every_language_translates_and_passes_final_validation(lang):
    findings, meds = report()
    out = await run_plan(lang, make_generate(lang), findings=findings, meds=meds)
    assert len(out["abnormal_findings"]) == len(findings)
    assert [f["test_name"] for f in out["abnormal_findings"]] == [f["test_name"] for f in findings]
    assert out["medications"][0]["translated_dosage"] == "65 mg"
    assert out["medications"][0]["translated_times_of_day"][0] == "08:00"
    assert set(REQUIRED_UI_LABEL_KEYS) <= set(out["ui_labels"])
    assert out["translated_parameters"]["Test 0"]
    assert 2 <= len(out["doctor_discussion_points"]) <= 5
    validate_translation(
        out, lang, "Clinician summary text " * 8, "Patient summary text " * 8,
        findings, meds, REQUIRED_UI_LABEL_KEYS,
    )


async def test_no_label_or_discussion_text_is_requested_from_the_model():
    seen = []

    async def spy(prompt, provider):
        seen.append(prompt)
        return await make_generate("hi")(prompt, provider)

    await run_plan("hi", spy)
    assert seen
    for prompt in seen:
        assert "ui_labels" not in prompt
        assert "doctor_discussion_points" not in prompt


async def test_dead_provider_is_tried_once_then_skipped_and_next_one_used():
    calls: list[str] = []
    good = make_generate("hi", calls)

    async def generate(prompt, provider):
        if provider == "gemini":
            calls.append(provider)
            raise QuotaError("daily quota exceeded")
        return await good(prompt, provider)

    out = await run_plan("hi", generate, providers=("gemini", "openai"))
    assert out["abnormal_findings"]
    assert calls.count("gemini") == 1, "quota error must not be retried or re-hit by later units"
    assert calls.count("openai") >= 2  # several units, all served by the fallback


async def test_all_providers_exhausted_reports_quota_and_does_not_retry():
    calls: list[str] = []

    async def generate(prompt, provider):
        calls.append(provider)
        raise QuotaError("quota")

    with pytest.raises(TranslationServiceError) as err:
        await run_plan("hi", generate, providers=("gemini", "openai", "mistral"))
    assert err.value.reason == "quota_or_rate_limit"
    assert sorted(calls) == ["gemini", "mistral", "openai"]  # one attempt each


async def test_english_instead_of_target_script_is_rejected_with_invalid_output():
    async def generate(prompt, provider):
        return {"content": json.dumps({
            "clinician_summary": "english only", "patient_summary": "english only",
            "abnormal_findings": [], "medications": [], "translated_parameters": [],
        })}

    with pytest.raises(TranslationServiceError) as err:
        await run_plan("te", generate, findings=[], meds=[])
    assert err.value.reason == "invalid_output"


async def test_units_run_in_parallel_but_within_the_limit():
    in_flight = 0
    peak = 0
    base = make_generate("ta")

    async def generate(prompt, provider):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        try:
            await asyncio.sleep(0.05)
            return await base(prompt, provider)
        finally:
            in_flight -= 1

    findings, meds = report(10)
    started = time.monotonic()
    await run_plan("ta", generate, findings=findings, meds=meds, concurrency=3)
    elapsed = time.monotonic() - started
    assert 2 <= peak <= 3
    units = 1 + (len(findings) // 2)  # rough lower bound of units
    assert elapsed < 0.05 * units  # faster than strictly sequential


async def test_deadline_stops_a_hung_provider():
    async def generate(prompt, provider):
        await asyncio.sleep(5)

    started = time.monotonic()
    with pytest.raises(TranslationServiceError):
        await run_plan("hi", generate, providers=("gemini", "openai"), deadline_seconds=0.3)
    assert time.monotonic() - started < 3


async def test_cooling_down_provider_is_skipped_via_real_wrapper(monkeypatch):
    """generate_translation_with_provider records the failure kind and status."""

    class Boom(llm_client.LLMConnectionError):
        pass

    err = Boom("HTTP 401")
    err.status_code = 401

    class FakeProvider:
        async def generate(self, *a, **k):
            raise err

    monkeypatch.setattr(llm_client.llm_client_instance, "get_provider", lambda name: FakeProvider())

    async def fake_config():
        return {}

    monkeypatch.setattr(llm_client, "get_resolved_ai_config", fake_config)
    with pytest.raises(TranslationServiceError) as first:
        await llm_client.generate_translation_with_provider("p", "openai")
    assert first.value.failure_kind == "invalid_or_unauthorised_key"
    assert not provider_health.is_available("openai")


def test_identifiers_are_realigned_or_restored_not_trusted():
    source = [{"test_name": "A"}, {"test_name": "B"}]
    # reordered
    out = [{"test_name": "B", "x": 2}, {"test_name": "A", "x": 1}]
    _align_to_source(source, out, "test_name")
    assert [o["x"] for o in out] == [1, 2]
    # fully translated identifiers: order trusted, identifiers restored
    out = [{"test_name": "ए"}, {"test_name": "बी"}]
    _align_to_source(source, out, "test_name")
    assert [o["test_name"] for o in out] == ["A", "B"]
    # partial mismatch is ambiguous and rejected
    with pytest.raises(ValueError):
        _align_to_source(source, [{"test_name": "A"}, {"test_name": "zzz"}], "test_name")


def test_gemini_schema_has_no_empty_objects():
    schema = llm_client._translation_response_schema()

    def walk(node, path="root"):
        if isinstance(node, dict):
            if node.get("type") == "OBJECT":
                assert node.get("properties"), f"empty OBJECT at {path}"
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")

    walk(schema)


def test_direct_gemini_key_policy(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ALLOW_GEMINI_API_KEY_IN_PRODUCTION", False)
    assert llm_client._gemini_key_blocked_by_environment() is True
    monkeypatch.setattr(settings, "ALLOW_GEMINI_API_KEY_IN_PRODUCTION", True)
    assert llm_client._gemini_key_blocked_by_environment() is False
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ALLOW_GEMINI_API_KEY_IN_PRODUCTION", False)
    assert llm_client._gemini_key_blocked_by_environment() is False


def test_network_and_timeout_failures_are_classified_not_unknown():
    import httpx
    from app.services import provider_health as ph

    def wrapped(inner):
        try:
            try:
                raise inner
            except Exception as e:
                raise llm_client.LLMConnectionError("Gemini developer API request failed.") from e
        except llm_client.LLMConnectionError as outer:
            return outer

    assert ph.classify_error(wrapped(httpx.ReadTimeout("")))[0] == ph.TRANSIENT
    assert ph.classify_error(wrapped(httpx.ConnectError("")))[0] == ph.NETWORK
    assert ph.classify_error(wrapped(httpx.ConnectTimeout("")))[0] == ph.TRANSIENT
    described = ph.describe_error(wrapped(httpx.ConnectError("name resolution failed")))
    assert "ConnectError" in described and "AIza" not in described


async def test_dev_environment_message_shows_the_real_cause(monkeypatch):
    from app.api.v1 import analysis

    provider_health.reset()
    provider_health.record_failure("gemini", QuotaError("daily quota exceeded"))
    text = analysis._provider_diagnostics(["gemini", "openai"])
    assert "gemini=quota_or_rate_limit" in text and "openai" not in text


async def test_gemini_model_variants_are_separate_providers(monkeypatch):
    from app.services.translation_planner import resolve_translation_providers

    monkeypatch.setattr(settings, "TRANSLATION_PROVIDER_ORDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.1-flash-lite")
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash-lite")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test-key-value")
    monkeypatch.setattr(settings, "MISTRAL_API_KEY", None)
    providers = resolve_translation_providers()
    assert providers[:3] == ["gemini", "gemini:gemini-2.5-flash", "gemini:gemini-2.5-flash-lite"]
    assert "openai" in providers

    seen = []

    class FakeGemini(llm_client.DevGeminiProvider):
        async def generate(self, prompt, timeout=30.0, request_id=None, system_instruction=None,
                           thinking_level="LOW", config=None):
            seen.append(self.get_model_name(config))
            return {"provider": "dev_gemini", "content": "{}"}

    async def fake_config():
        return {"primary_provider": "dev_gemini", "model_name": "gemini-3.1-flash-lite"}

    monkeypatch.setattr(llm_client.llm_client_instance, "get_provider", lambda name: FakeGemini())
    monkeypatch.setattr(llm_client, "get_resolved_ai_config", fake_config)
    await llm_client.generate_translation_with_provider("p", "gemini")
    await llm_client.generate_translation_with_provider("p", "gemini:gemini-2.5-flash")
    assert seen == ["gemini-3.1-flash-lite", "gemini-2.5-flash"]


async def test_wrong_script_on_the_first_model_is_rescued_by_the_next_model():
    good = make_generate("ta")

    async def generate(prompt, provider):
        if provider == "gemini":
            return {"content": json.dumps({
                "clinician_summary": "english text", "patient_summary": "english text",
                "abnormal_findings": [], "medications": [], "translated_parameters": [],
            })}
        return await good(prompt, provider)

    out = await run_plan("ta", generate, providers=("gemini", "gemini:gemini-2.5-flash"),
                         findings=[], meds=[])
    assert out["patient_summary"]


def test_tamil_summary_with_latin_test_names_passes_the_script_check():
    from app.services.translation_validation import require_script, script_letter_stats

    tamil = (
        "உங்கள் அறிக்கையில் 20 ஆய்வக முடிவுகள் உள்ளன. MCV: 80.0 குறைவாகக் குறிக்கப்பட்டுள்ளது "
        "(குறிப்பு வரம்பு 81.0 - 101.0). MCHC: 37.5 அதிகமாகக் குறிக்கப்பட்டுள்ளது. "
        "hemoglobin: 15.0 g/dL இயல்பானது. Total Leucocyte Count: 5000.0 இயல்பானது."
    )
    native, total = script_letter_stats(tamil, "ta")
    assert native / total > 0.6
    require_script(tamil, "ta")


def test_untranslated_english_is_still_rejected_for_every_language():
    from app.services.translation_validation import require_script

    english = "Your report contains 20 extracted laboratory test results. Please discuss them with your doctor."
    mixed = "Your hemoglobin result is below the normal range and you should rest. தயவு"
    for lang in LANGUAGES:
        with pytest.raises(ValueError):
            require_script(english, lang)
    with pytest.raises(ValueError):
        require_script(mixed, "ta")


async def test_openai_compatible_providers_join_the_chain_and_send_the_right_request(monkeypatch):
    from app.services.translation_planner import resolve_translation_providers

    monkeypatch.setattr(settings, "TRANSLATION_PROVIDER_ORDER", "gemini")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "MISTRAL_API_KEY", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_value_123456")
    monkeypatch.setattr(settings, "GROQ_MODEL", "llama-test")
    assert "groq" in resolve_translation_providers()
    assert "cerebras" not in resolve_translation_providers()

    sent = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": " {\"ok\": true} "}}]}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            sent.update(url=url, json=json, headers=headers)
            return FakeResponse()

    monkeypatch.setattr(llm_client.httpx, "AsyncClient", FakeClient)

    async def fake_config():
        return {}

    monkeypatch.setattr(llm_client, "get_resolved_ai_config", fake_config)
    out = await llm_client.generate_translation_with_provider("hello", "groq")
    assert out["content"] == '{"ok": true}' and out["provider"] == "groq"
    assert sent["url"].startswith("https://api.groq.com/") and sent["json"]["model"] == "llama-test"
    assert sent["json"]["response_format"] == {"type": "json_object"}
    assert sent["headers"]["Authorization"] == "Bearer gsk_test_value_123456"
