import os

file_path = r"C:\Users\manas\Downloads\MedNarrate-main\mednarrate-backend\app\services\translation_planner.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

OLD_EXECUTE = """async def _execute_with_fallback(
    prompt,
    providers,
    validate_func,
    lang_code,
    chunk_data,
    required_ui_label_keys,
    request_id,
    generate_func: Callable,
):
    last_exc = None
    for provider_name in providers:
        logger.info(f"[TRANSLATION_PLANNER {request_id}] Trying provider: {provider_name}")
        try:
            llm_res = await generate_func(prompt, provider_name)
            if llm_res.get("provider") == "fallback":
                last_exc = TranslationServiceError("Fallback provider reached without valid schema generation.")
                continue
                
            raw_text = llm_res.get("content", "")
            parsed_candidate = parse_translation(raw_text)

            # A chunk is allowed to contain only prose or parameter names. Do
            # not let a model invent clinical entries or repeat summaries for
            # fields that were intentionally absent from that chunk. These
            # normalizations preserve the source-of-truth boundary before the
            # strict verifier runs.
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
            
            # Unit-level integrity validation!
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
            
        except Exception as exc:
            logger.warning(f"[TRANSLATION_PLANNER {request_id}] Provider {provider_name} failed: {type(exc).__name__}")
            last_exc = exc
            
    raise TranslationServiceError(f"All providers failed for this translation unit. Last error: {type(last_exc).__name__}")"""

NEW_EXECUTE = """async def _execute_with_fallback(
    prompt,
    providers,
    validate_func,
    lang_code,
    chunk_data,
    required_ui_label_keys,
    request_id,
    generate_func: Callable,
):
    import asyncio
    last_exc = None
    for provider_name in providers:
        logger.info(f"[TRANSLATION_PLANNER {request_id}] Trying provider: {provider_name}")
        for attempt in range(2):
            try:
                llm_res = await generate_func(prompt, provider_name)
                if llm_res.get("provider") == "fallback":
                    last_exc = TranslationServiceError("Fallback provider reached without valid schema generation.")
                    break
                    
                raw_text = llm_res.get("content", "")
                parsed_candidate = parse_translation(raw_text)

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
                    await asyncio.sleep(1.0)
            
    raise TranslationServiceError(f"All providers failed for this translation unit. Last error: {type(last_exc).__name__}")"""

new_content = content.replace(OLD_EXECUTE, NEW_EXECUTE)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated translation_planner.py")
