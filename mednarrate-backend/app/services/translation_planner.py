import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List

from app.core.config import settings
from app.exceptions import TranslationServiceError
from app.services import provider_health as ph
from app.services.llm_client import OPENAI_COMPATIBLE, generate_translation_with_provider
from app.services.model_activity import record_successful_model_call
from app.services.prompts import TRANSLATION_UNIT_PROMPT
from app.services.provider_health import classify_error, provider_health
from app.services.translation_labels import build_discussion_points, get_ui_labels
from app.services.translation_validation import parse_translation

logger = logging.getLogger(__name__)

# Keep each model request small enough that every finding comes back complete,
# including languages whose Unicode text needs many output tokens.
CHUNK_MAX_CHARS = 700

# Failure reasons reported to the caller, most useful first.
INVALID_OUTPUT = "invalid_output"
TIMEOUT = "timeout"
_REASON_PRIORITY = [
    ph.AUTH,
    ph.QUOTA,
    ph.MODEL,
    ph.NETWORK,
    ph.TRANSIENT,
    INVALID_OUTPUT,
    TIMEOUT,
    ph.NOT_CONFIGURED,
    ph.UNKNOWN,
]


def resolve_translation_providers() -> List[str]:
    """Provider order for translation: TRANSLATION_PROVIDER_ORDER first, then
    (when fallback is enabled) every other provider that has credentials."""
    order = str(getattr(settings, "TRANSLATION_PROVIDER_ORDER", "") or "")
    providers = [p.strip() for p in order.split(",") if p.strip()] or [
        "vertex_ai", "gemini", "openai", "mistral",
    ]
    # Same Gemini key, other models: separate quota pools, and a stronger model
    # for scripts the lighter one gets wrong. Only when Gemini is in the chain.
    if "gemini" in providers or "dev_gemini" in providers:
        primary_model = _configured_gemini_model()
        position = max(
            (providers.index(n) for n in ("gemini", "dev_gemini") if n in providers)
        )
        extras = [
            f"gemini:{m.strip()}"
            for m in str(getattr(settings, "GEMINI_FALLBACK_MODELS", "") or "").split(",")
            if m.strip() and m.strip() != primary_model
        ]
        providers[position + 1:position + 1] = [e for e in extras if e not in providers]
    if getattr(settings, "ENABLE_LLM_FALLBACK", True):
        configured = {
            "vertex_ai": bool(getattr(settings, "VERTEX_PROJECT_ID", None)),
            "openai": bool(getattr(settings, "OPENAI_API_KEY", None)),
            "anthropic": bool(getattr(settings, "ANTHROPIC_API_KEY", None)),
            "mistral": bool(getattr(settings, "MISTRAL_API_KEY", None)),
            **{
                name: bool(getattr(settings, key_setting, None))
                for name, (_url, key_setting, _model) in OPENAI_COMPATIBLE.items()
            },
            # Small local models are poor at Indic scripts and slow, so Ollama is
            # only used for translation when named in TRANSLATION_PROVIDER_ORDER.
        }
        for name, is_configured in configured.items():
            if is_configured and name not in providers:
                providers.append(name)
    return providers


def _configured_gemini_model() -> str:
    try:
        from app.services.llm_client import DevGeminiProvider

        return DevGeminiProvider().get_model_name(None)
    except Exception:  # pragma: no cover - defensive
        return str(getattr(settings, "GEMINI_MODEL", ""))


def pick_failure_reason(kinds: List[str]) -> str:
    """Most informative reason among everything that went wrong."""
    present = set(kinds)
    for reason in _REASON_PRIORITY:
        if reason in present:
            return reason
    return ph.UNKNOWN


async def execute_translation_plan(
    target_lang_name: str,
    lang_code: str,
    clinician_summary: str,
    patient_summary: str,
    abnormal_findings_source: List[Dict[str, Any]],
    meds_list: List[Dict[str, Any]],
    unique_params: List[str],
    providers: List[str],
    validate_func: Callable,
    required_ui_label_keys: Any,
    request_id: str,
    generate_func: Callable = generate_translation_with_provider,
    deadline_seconds: float | None = None,
    concurrency: int | None = None,
) -> Dict[str, Any]:
    """Translate one report.

    Only the report's own content goes to a model: it is split into bounded
    units, translated through the provider chain (skipping providers that are
    cooling down), and each unit is validated before it is accepted. Screen
    labels and the "discuss with your doctor" bullets are filled in from the
    fixed, reviewed tables in translation_labels.py. ``required_ui_label_keys``
    is accepted for backward compatibility; labels are no longer model output.
    """

    chunks = _build_chunks(
        clinician_summary=clinician_summary,
        patient_summary=patient_summary,
        abnormal_findings_source=abnormal_findings_source,
        meds_list=meds_list,
        unique_params=unique_params,
        max_chars=CHUNK_MAX_CHARS,
    )
    logger.info(f"[TRANSLATION_PLANNER {request_id}] Input split into {len(chunks)} bounded translation units.")

    budget = float(
        deadline_seconds
        if deadline_seconds is not None
        else getattr(settings, "TRANSLATION_DEADLINE_SECONDS", 150.0)
    )
    deadline = time.monotonic() + budget
    limit = max(1, int(concurrency or getattr(settings, "TRANSLATION_CONCURRENCY", 3)))
    failure_kinds: List[str] = []

    def prompt_for(chunk: Dict[str, Any]) -> str:
        return TRANSLATION_UNIT_PROMPT.format(
            target_language=target_lang_name,
            clinician_summary=chunk["clinician_summary"],
            patient_summary=chunk["patient_summary"],
            abnormal_findings_json=json.dumps(chunk["abnormal_findings"], ensure_ascii=False),
            medications_json=json.dumps(chunk["medications"], ensure_ascii=False),
            unique_parameters_json=json.dumps(chunk["unique_params"], ensure_ascii=False),
        )

    semaphore = asyncio.Semaphore(limit)

    async def run_unit(index: int, chunk: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            logger.info(f"[TRANSLATION_PLANNER {request_id}] Executing translation unit {index + 1}/{len(chunks)}")
            return await _execute_with_fallback(
                prompt_for(chunk),
                providers,
                validate_func,
                lang_code,
                chunk,
                set(),
                request_id,
                generate_func,
                deadline=deadline,
                target_lang_name=target_lang_name,
                failure_kinds=failure_kinds,
            )

    results: List[Dict[str, Any]] = []
    # The first unit runs alone: if a provider is dead (bad key, no quota) it is
    # discovered once and put on cool-down instead of being hit by every
    # parallel unit. The remaining units then run concurrently.
    results.append(await run_unit(0, chunks[0]))
    if len(chunks) > 1:
        tasks = [asyncio.ensure_future(run_unit(i, c)) for i, c in enumerate(chunks) if i > 0]
        try:
            results.extend(await asyncio.gather(*tasks))
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    final_merged: Dict[str, Any] = {
        "clinician_summary": "",
        "patient_summary": "",
        "abnormal_findings": [],
        "medications": [],
        "translated_parameters": {},
        "doctor_discussion_points": [],
        "ui_labels": {},
    }
    for parsed_chunk in results:
        if parsed_chunk.get("clinician_summary"):
            final_merged["clinician_summary"] += ("\n\n" if final_merged["clinician_summary"] else "") + str(parsed_chunk["clinician_summary"]).strip()
        if parsed_chunk.get("patient_summary"):
            final_merged["patient_summary"] += ("\n\n" if final_merged["patient_summary"] else "") + str(parsed_chunk["patient_summary"]).strip()
        final_merged["abnormal_findings"].extend(parsed_chunk.get("abnormal_findings") or [])
        final_merged["medications"].extend(parsed_chunk.get("medications") or [])
        final_merged["translated_parameters"].update(parsed_chunk.get("translated_parameters") or {})

    # Fixed, reviewed text: no model call, so it can never be missing or in the wrong script.
    final_merged["ui_labels"] = get_ui_labels(lang_code)
    translated_names = {
        str(f.get("test_name")): str(f.get("translated_test_name")).strip()
        for f in final_merged["abnormal_findings"]
        if isinstance(f, dict) and f.get("test_name") and str(f.get("translated_test_name") or "").strip()
    }
    for original, translated in final_merged["translated_parameters"].items():
        translated_names.setdefault(str(original), str(translated))
    final_merged["doctor_discussion_points"] = build_discussion_points(
        lang_code,
        abnormal_findings_source,
        translated_names,
        has_medications=bool(meds_list),
    )
    return final_merged


def _chunk_prose(text: str, max_len: int) -> List[str]:
    if not text:
        return []
    if len(text) <= max_len:
        return [text]
        
    chunks = []
    paragraphs = text.split('\n\n')
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 > max_len:
            if current:
                chunks.append(current.strip())
                current = ""
            if len(p) > max_len:
                lines = p.split('\n')
                for l in lines:
                    if len(current) + len(l) + 1 > max_len:
                        if current:
                            chunks.append(current.strip())
                            current = ""
                        if len(l) > max_len:
                            for i in range(0, len(l), max_len):
                                chunks.append(l[i:i+max_len])
                        else:
                            current = l + '\n'
                    else:
                        current += l + '\n'
            else:
                current = p + '\n\n'
        else:
            current += p + '\n\n'
            
    if current.strip():
        chunks.append(current.strip())
        
    return chunks

def _build_chunks(clinician_summary, patient_summary, abnormal_findings_source, meds_list, unique_params, max_chars):
    chunks = []
    
    def new_chunk():
        return {
            "clinician_summary": "",
            "patient_summary": "",
            "abnormal_findings": [],
            "medications": [],
            "unique_params": [],
            "char_count": 0
        }
        
    current_chunk = new_chunk()
    
    clinician_chunks = _chunk_prose(clinician_summary or "", max_chars)
    patient_chunks = _chunk_prose(patient_summary or "", max_chars)
    
    # Process clinician_summary pieces
    for p_chunk in clinician_chunks:
        if current_chunk["char_count"] + len(p_chunk) > max_chars and current_chunk["char_count"] > 0:
            chunks.append(current_chunk)
            current_chunk = new_chunk()
        current_chunk["clinician_summary"] += ("\n\n" if current_chunk["clinician_summary"] else "") + p_chunk
        current_chunk["char_count"] += len(p_chunk)
        
    # Process patient_summary pieces
    for p_chunk in patient_chunks:
        if current_chunk["char_count"] + len(p_chunk) > max_chars and current_chunk["char_count"] > 0:
            chunks.append(current_chunk)
            current_chunk = new_chunk()
        current_chunk["patient_summary"] += ("\n\n" if current_chunk["patient_summary"] else "") + p_chunk
        current_chunk["char_count"] += len(p_chunk)
    
    # Distribute findings
    for finding in abnormal_findings_source:
        f_len = len(json.dumps(finding, ensure_ascii=False))
        if current_chunk["char_count"] + f_len > max_chars and current_chunk["char_count"] > 0:
            chunks.append(current_chunk)
            current_chunk = new_chunk()
        current_chunk["abnormal_findings"].append(finding)
        current_chunk["char_count"] += f_len
        
    # Distribute medications
    for med in meds_list:
        m_len = len(json.dumps(med, ensure_ascii=False))
        if current_chunk["char_count"] + m_len > max_chars and current_chunk["char_count"] > 0:
            chunks.append(current_chunk)
            current_chunk = new_chunk()
        current_chunk["medications"].append(med)
        current_chunk["char_count"] += m_len
        
    # Distribute unique parameters
    for p in unique_params:
        p_len = len(p) + 5
        if current_chunk["char_count"] + p_len > max_chars and current_chunk["char_count"] > 0:
            chunks.append(current_chunk)
            current_chunk = new_chunk()
        current_chunk["unique_params"].append(p)
        current_chunk["char_count"] += p_len
        
    if current_chunk["char_count"] > 0 or len(chunks) == 0:
        chunks.append(current_chunk)
        
    return chunks

def _as_parameter_map(value: Any) -> Dict[str, str]:
    """Accept a {name: translation} dict or a [{name, translated}, ...] list."""
    out: Dict[str, str] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, str) and v.strip():
                out[str(k)] = v.strip()
    elif isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("original") or item.get("parameter")
            translated = item.get("translated") or item.get("translation")
            if name and isinstance(translated, str) and translated.strip():
                out[str(name)] = translated.strip()
    return out


def _normalise_candidate(parsed_candidate: Any, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(parsed_candidate, dict):
        raise ValueError("Translation response was not an object")
    # Some providers wrap the object as {"translation": "<json string>"}.
    if (
        set(parsed_candidate) == {"translation"}
        and isinstance(parsed_candidate.get("translation"), str)
    ):
        parsed_candidate = parse_translation(parsed_candidate["translation"])
    # Accept the API's persisted field names as well as the prompt's.
    parsed_candidate.setdefault("abnormal_findings", parsed_candidate.pop("findings_json", []))
    parsed_candidate.setdefault("medications", parsed_candidate.pop("medications_json", []))
    parsed_candidate["translated_parameters"] = _as_parameter_map(
        parsed_candidate.get("translated_parameters")
    )
    # Never let a model invent content for an empty section.
    if not chunk_data["abnormal_findings"]:
        parsed_candidate["abnormal_findings"] = []
    if not chunk_data["medications"]:
        parsed_candidate["medications"] = []
    if not chunk_data["clinician_summary"]:
        parsed_candidate["clinician_summary"] = ""
    if not chunk_data["patient_summary"]:
        parsed_candidate["patient_summary"] = ""
    # Discussion bullets and labels come from fixed tables, never from the model.
    parsed_candidate.pop("doctor_discussion_points", None)
    parsed_candidate.pop("ui_labels", None)
    return parsed_candidate


async def _execute_with_fallback(
    prompt,
    providers,
    validate_func,
    lang_code,
    chunk_data,
    required_ui_label_keys,
    request_id,
    generate_func: Callable,
    local_prompt=None,
    deadline: float | None = None,
    target_lang_name: str = "",
    failure_kinds: List[str] | None = None,
):
    """Translate one unit via the provider chain.

    Persistent failures (bad key, exhausted quota, unknown model) move on to the
    next provider immediately and put the provider on cool-down; only a genuine
    transient outage or an invalid-but-parseable answer gets one retry.
    """
    kinds = failure_kinds if failure_kinds is not None else []
    last_exc = None
    per_call = float(getattr(settings, "TRANSLATION_TIMEOUT_SECONDS", 45.0)) + 10.0
    for provider_name in providers:
        if deadline is not None and time.monotonic() >= deadline:
            kinds.append(TIMEOUT)
            break
        if provider_name != "fallback" and not provider_health.is_available(provider_name):
            cooling = provider_health.last_kind(provider_name)
            if cooling:
                kinds.append(cooling)
            logger.info(
                f"[TRANSLATION_PLANNER {request_id}] Skipping {provider_name}: cooling down "
                f"for {provider_health.seconds_until_retry(provider_name):.0f}s ({cooling or 'earlier failure'})"
            )
            continue
        logger.info(f"[TRANSLATION_PLANNER {request_id}] Trying provider: {provider_name}")
        for attempt in range(2):
            parsed_candidate = None
            try:
                active_prompt = local_prompt if (provider_name == "local" and local_prompt) else prompt
                if attempt:
                    active_prompt += (
                        f"\nRETRY: The previous response was invalid. Translate ONLY into "
                        f"{target_lang_name} using its native Unicode script; do not use "
                        "Russian, English, transliteration, or any other language. "
                        "Return every input item in the required arrays, preserving "
                        "their original order."
                    )
                remaining = (deadline - time.monotonic()) if deadline is not None else per_call
                if remaining <= 0:
                    kinds.append(TIMEOUT)
                    break
                call_started = time.monotonic()
                llm_res = await asyncio.wait_for(
                    generate_func(active_prompt, provider_name),
                    timeout=min(per_call, remaining),
                )
                raw_text = llm_res.get("content", "") if isinstance(llm_res, dict) else llm_res
                parsed_candidate = raw_text if isinstance(raw_text, dict) else parse_translation(str(raw_text))
                parsed_candidate = _normalise_candidate(parsed_candidate, chunk_data)

                if provider_name != "fallback":
                    validate_func(
                        parsed_candidate,
                        lang_code,
                        chunk_data["clinician_summary"],
                        chunk_data["patient_summary"],
                        chunk_data["abnormal_findings"],
                        chunk_data["medications"],
                        [],
                    )

                logger.info(f"[TRANSLATION_PLANNER {request_id}] Validation PASS on {provider_name}")
                # The main LLM chain already records its own events. Direct
                # translation providers otherwise bypass that telemetry path.
                if generate_func is generate_translation_with_provider and provider_name != "existing":
                    metadata = llm_res if isinstance(llm_res, dict) else {}
                    await record_successful_model_call(
                        request_id=request_id,
                        provider=str(metadata.get("provider") or provider_name.split(":", 1)[0]),
                        model=metadata.get("model"),
                        feature="translation",
                        latency_ms=float(metadata.get("latency_ms") or (time.monotonic() - call_started) * 1000),
                        fallback_used=provider_name != providers[0],
                    )
                return parsed_candidate

            except (ValueError, TypeError, KeyError) as exc:
                abnormal_len = len(parsed_candidate.get("abnormal_findings") or []) if isinstance(parsed_candidate, dict) else -1
                med_len = len(parsed_candidate.get("medications") or []) if isinstance(parsed_candidate, dict) else -1
                logger.warning(
                    "[TRANSLATION_PLANNER %s] %s validation failed error_type=%s "
                    "src_find_len=%d out_find_len=%d src_med_len=%d out_med_len=%d. details: %s",
                    request_id, provider_name, type(exc).__name__,
                    len(chunk_data["abnormal_findings"]), abnormal_len,
                    len(chunk_data["medications"]), med_len, str(exc)
                )
                last_exc = exc
                kinds.append(INVALID_OUTPUT)
                if attempt == 0:
                    continue
                break  # Still invalid after the bounded retry; try the next provider

            except Exception as exc:
                last_exc = exc
                status_code = getattr(exc, "status_code", None)
                is_safety = getattr(exc, "is_safety_block", False)
                kind = getattr(exc, "failure_kind", None) or classify_error(exc)[0]
                if getattr(exc, "failure_kind", None) is None:
                    # generate_translation_with_provider already records its own
                    # failures; anything else (a timeout raised here, a custom
                    # generate function) is recorded now so the provider cools down.
                    provider_health.record_failure(provider_name, exc)
                kinds.append(kind)
                # Quota / auth / bad-model / not-configured failures are persistent:
                # retrying only burns more allowance, so move on immediately.
                if is_safety or kind not in (ph.TRANSIENT, ph.UNKNOWN):
                    logger.warning(
                        f"[TRANSLATION_PLANNER {request_id}] Provider {provider_name} persistent error: "
                        f"kind={kind} status={status_code}. Moving to next provider."
                    )
                    break
                logger.warning(
                    f"[TRANSLATION_PLANNER {request_id}] Provider {provider_name} attempt {attempt + 1} "
                    f"failed: {type(exc).__name__} kind={kind}"
                )
                if attempt < 1:
                    await asyncio.sleep(2.0)

    reason = pick_failure_reason(kinds)
    raise TranslationServiceError(
        f"All providers failed for this translation unit ({reason}). "
        f"Last error: {type(last_exc).__name__ if last_exc else 'none'}",
        reason=reason,
    )
