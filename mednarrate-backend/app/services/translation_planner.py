import json
import logging
from typing import List, Dict, Any, Callable
from app.services.prompts import TRANSLATION_PROMPT, CHUNK_TRANSLATION_PROMPT, LOCAL_TRANSLATION_PROMPT
from app.services.llm_client import generate_translation_with_provider
from app.services.translation_validation import parse_translation
from app.exceptions import TranslationServiceError

logger = logging.getLogger(__name__)

# Conservative budget to safely fit within typical provider limits (e.g., Groq's 8000 TPM limit).
# Using 1500 characters prevents JSON truncation issues on languages with high token-per-character ratios like Hindi
CHUNK_MAX_CHARS = 5000

def get_static_ui_labels(lang_code: str) -> dict:
    import os, json
    labels_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'report_ui_labels.json')
    if os.path.exists(labels_file):
        with open(labels_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(lang_code, data.get('en', {}))
    return {}


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
    required_ui_label_keys: set,
    request_id: str,
    generate_func: Callable = generate_translation_with_provider,
) -> Dict[str, Any]:
    """
    Provider-independent translation planner. Splits the structured medical data into 
    token-aware bounded chunks, translates each independently via provider fallback, 
    and reassembles the final translation matching the original schema.
    """
    
    chunks = _build_chunks(
        clinician_summary=clinician_summary,
        patient_summary=patient_summary,
        abnormal_findings_source=abnormal_findings_source,
        meds_list=meds_list,
        unique_params=unique_params,
        max_chars=CHUNK_MAX_CHARS
    )
    
    logger.info(f"[TRANSLATION_PLANNER {request_id}] Input split into {len(chunks)} bounded translation units.")
    
    final_merged = {
        "clinician_summary": "",
        "patient_summary": "",
        "abnormal_findings": [],
        "medications": [],
        "translated_parameters": {},
        "doctor_discussion_points": [],
        "ui_labels": {}
    }
    
    for i, chunk in enumerate(chunks):
        logger.info(f"[TRANSLATION_PLANNER {request_id}] Executing translation unit {i+1}/{len(chunks)}")
        
        prompt_template = TRANSLATION_PROMPT if i == 0 else CHUNK_TRANSLATION_PROMPT
        
        prompt = prompt_template.format(
            target_language=target_lang_name,
            clinician_summary=chunk["clinician_summary"],
            patient_summary=chunk["patient_summary"],
            abnormal_findings_json=json.dumps(chunk["abnormal_findings"], ensure_ascii=False),
            medications_json=json.dumps(chunk["medications"], ensure_ascii=False),
            unique_parameters_json=json.dumps(chunk["unique_params"], ensure_ascii=False),
        )
        
        local_prompt_template = LOCAL_TRANSLATION_PROMPT if i == 0 else CHUNK_TRANSLATION_PROMPT
        local_prompt = local_prompt_template.format(
            target_language=target_lang_name,
            clinician_summary=chunk["clinician_summary"],
            patient_summary=chunk["patient_summary"],
            abnormal_findings_json=json.dumps(chunk["abnormal_findings"], ensure_ascii=False),
            medications_json=json.dumps(chunk["medications"], ensure_ascii=False),
            unique_parameters_json=json.dumps(chunk["unique_params"], ensure_ascii=False),
        )
        
        parsed_chunk = await _execute_with_fallback(
            prompt, providers, validate_func, lang_code,
            chunk, required_ui_label_keys if i == 0 else set(), request_id,
            generate_func,
            local_prompt=local_prompt
        )
        
        
        # Merge prose
        if parsed_chunk.get("clinician_summary"):
            final_merged["clinician_summary"] += ("\n\n" if final_merged["clinician_summary"] else "") + str(parsed_chunk["clinician_summary"]).strip()
        if parsed_chunk.get("patient_summary"):
            final_merged["patient_summary"] += ("\n\n" if final_merged["patient_summary"] else "") + str(parsed_chunk["patient_summary"]).strip()
            
        if i == 0:
            final_merged["ui_labels"] = parsed_chunk.get("ui_labels", {})
            
        final_merged["abnormal_findings"].extend(parsed_chunk.get("abnormal_findings") or [])
        final_merged["medications"].extend(parsed_chunk.get("medications") or [])
        final_merged["doctor_discussion_points"].extend(parsed_chunk.get("doctor_discussion_points") or [])
        
        tp = parsed_chunk.get("translated_parameters") or {}
        if isinstance(tp, dict):
            final_merged["translated_parameters"].update(tp)
            
    if len(final_merged["doctor_discussion_points"]) > 5:
        final_merged["doctor_discussion_points"] = final_merged["doctor_discussion_points"][:5]
        
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
):
    import asyncio
    last_exc = None
    for provider_name in providers:
        logger.info(f"[TRANSLATION_PLANNER {request_id}] Trying provider: {provider_name}")
        # One bounded attempt per provider keeps an unavailable provider from
        # blocking all later providers and the mobile request for minutes.
        for attempt in range(1):
            try:
                active_prompt = local_prompt if (provider_name == "local" and local_prompt) else prompt
                llm_res = await generate_func(active_prompt, provider_name)
                # (Removed check blocking fallback provider)
                    
                raw_text = llm_res.get("content", "") if isinstance(llm_res, dict) else llm_res
                if isinstance(raw_text, dict):
                    parsed_candidate = raw_text
                else:
                    parsed_candidate = parse_translation(str(raw_text))

                # Some providers wrap the requested object in a `translation`
                # field when structured output is enabled. Decode that wrapper
                # before validation instead of treating it as a malformed report.
                if (
                    isinstance(parsed_candidate, dict)
                    and set(parsed_candidate) == {"translation"}
                    and isinstance(parsed_candidate.get("translation"), str)
                ):
                    parsed_candidate = parse_translation(parsed_candidate["translation"])

                if required_ui_label_keys:
                    static_labels = get_static_ui_labels(lang_code)
                    if static_labels:
                        provider_labels = parsed_candidate.get("ui_labels") or {}
                        parsed_candidate["ui_labels"] = {
                            **static_labels,
                            **{
                                key: value
                                for key, value in provider_labels.items()
                                if isinstance(value, str) and value.strip()
                            },
                        }

                # Accept the API's persisted field names as well as the prompt
                # field names when a provider mirrors the response schema.
                parsed_candidate.setdefault(
                    "abnormal_findings", parsed_candidate.pop("findings_json", [])
                )
                parsed_candidate.setdefault(
                    "medications", parsed_candidate.pop("medications_json", [])
                )
                parsed_candidate.setdefault(
                    "doctor_discussion_points",
                    parsed_candidate.pop("discussion_points", []),
                )

                if not chunk_data["abnormal_findings"]:
                    parsed_candidate["abnormal_findings"] = []
                if not chunk_data["medications"]:
                    parsed_candidate["medications"] = []
                if not chunk_data["clinician_summary"]:
                    parsed_candidate["clinician_summary"] = ""
                if not chunk_data["patient_summary"]:
                    parsed_candidate["patient_summary"] = ""
                if not required_ui_label_keys:
                    parsed_candidate.setdefault("ui_labels", {})
                
                if provider_name != "fallback":
                    validate_func(
                        parsed_candidate,
                        lang_code,
                        chunk_data["clinician_summary"],
                        chunk_data["patient_summary"],
                        chunk_data["abnormal_findings"],
                        chunk_data["medications"],
                        required_ui_label_keys
                    )
                
                logger.info(f"[TRANSLATION_PLANNER {request_id}] Validation PASS on {provider_name}")
                return parsed_candidate
                
            except (ValueError, TypeError, KeyError) as exc:
                abnormal_len = len(parsed_candidate.get("abnormal_findings") or []) if "parsed_candidate" in locals() and isinstance(parsed_candidate, dict) else -1
                med_len = len(parsed_candidate.get("medications") or []) if "parsed_candidate" in locals() and isinstance(parsed_candidate, dict) else -1
                logger.warning(
                    "[TRANSLATION_PLANNER %s] %s validation failed error_type=%s "
                    "src_find_len=%d out_find_len=%d src_med_len=%d out_med_len=%d. details: %s",
                    request_id, provider_name, type(exc).__name__,
                    len(chunk_data["abnormal_findings"]), abnormal_len,
                    len(chunk_data["medications"]), med_len, str(exc)
                )
                last_exc = exc
                break # Permanent: validation failure, move to next provider
                
            except Exception as exc:
                last_exc = exc
                status_code = getattr(exc, "status_code", 500)
                is_safety = getattr(exc, "is_safety_block", False)
                # Retry on 429, 500+
                if is_safety or (400 <= status_code < 500 and status_code != 429):
                    logger.warning(f"[TRANSLATION_PLANNER {request_id}] Provider {provider_name} permanent error: {status_code} {type(exc).__name__}. Moving to next provider.")
                    break # Permanent API error, move to next provider
                
                logger.warning(f"[TRANSLATION_PLANNER {request_id}] Provider {provider_name} attempt {attempt+1} failed: {type(exc).__name__}")
                if attempt < 1:
                    await asyncio.sleep(2.0)
            
    raise TranslationServiceError(f"All providers failed for this translation unit. Last error: {type(last_exc).__name__}")
