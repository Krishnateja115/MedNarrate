import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.services.llm_client import generate, LLMConnectionError, LLMConfigurationError

logger = logging.getLogger(__name__)

async def generate_primary_reasoning(prompt: str, request_id: Optional[str] = None) -> str:
    """
    Primary Reasoning (Gemini 3.8 Flash).
    Used for complex analysis, patient summaries, clinician summaries.
    """
    logger.info(f"[ORCHESTRATOR] Routing to PRIMARY_LLM ({settings.PRIMARY_LLM_PROVIDER} / {settings.PRIMARY_LLM_MODEL})")
    return await generate(prompt, timeout=settings.LLM_TIMEOUT_SECONDS, request_id=request_id)

async def verify_medical_facts(prompt: str, request_id: Optional[str] = None) -> dict:
    """
    Medical Verification (MedGemma 1.5 4B).
    Returns a dict with 'is_valid' (bool), 'correction' (str), and 'verification_status' (str).
    """
    logger.info(f"[ORCHESTRATOR] Routing to MEDICAL_VERIFIER ({settings.MEDICAL_VERIFIER_PROVIDER} / {settings.MEDICAL_VERIFIER_MODEL})")
    
    if settings.MEDICAL_VERIFIER_PROVIDER.lower() != "ollama":
        logger.warning("MEDICAL_VERIFIER is not Ollama, skipping strict verification.")
        return {"is_valid": True, "correction": None, "verification_status": "unavailable"}

    ollama_url = settings.OLLAMA_URL or "http://localhost:11434"
    payload = {
        "model": settings.MEDICAL_VERIFIER_MODEL,
        "prompt": f"Verify the following medical text for accuracy. If there are dangerous errors, reply starting with [INVALID] and explain why. Otherwise, reply [VALID].\n\nText to verify: {prompt}",
        "stream": False,
        "options": {"temperature": 0.0} 
    }
    
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{ollama_url}/api/generate", json=payload)
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            
            is_valid = "[INVALID]" not in text.upper()
            return {
                "is_valid": is_valid,
                "correction": text if not is_valid else None,
                "verification_status": "verified" if is_valid else "failed"
            }
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Medical Verification failed: {e}")
        return {"is_valid": True, "correction": None, "verification_status": "unavailable"}

async def extract_structured_json(prompt: str, request_id: Optional[str] = None) -> str:
    """
    Structured Extraction (Qwen3 14B).
    If Qwen3 is unavailable, fall back to Primary LLM (Gemini).
    """
    logger.info(f"[ORCHESTRATOR] Routing to STRUCTURED_MODEL ({settings.STRUCTURED_MODEL_PROVIDER} / {settings.STRUCTURED_MODEL_MODEL})")
    
    if settings.STRUCTURED_MODEL_PROVIDER.lower() == "ollama":
        ollama_url = settings.OLLAMA_URL or "http://localhost:11434"
        payload = {
            "model": settings.STRUCTURED_MODEL_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0} 
        }
        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                resp = await client.post(f"{ollama_url}/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Qwen3 Structured Extraction failed: {e}. Falling back to Gemini.")
    
    return await generate_primary_reasoning(prompt, request_id=request_id)

async def translate_text_indic(text: str, target_lang_code: str) -> str:
    """
    Translation (IndicTrans2).
    Calls the local IndicTrans2 service.
    """
    logger.info(f"[ORCHESTRATOR] Routing to TRANSLATION_MODEL ({settings.TRANSLATION_MODEL_PROVIDER})")
    url = settings.TRANSLATION_MODEL_URL
    if not url:
        logger.warning("[ORCHESTRATOR] IndicTrans2 URL not configured. Returning original text.")
        return text

    payload = {
        "text": text,
        "source_language": "en",
        "target_language": target_lang_code
    }
    
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json().get("translated_text", text)
            else:
                logger.warning(f"[ORCHESTRATOR] Translation service returned {resp.status_code}. Returning original.")
                return text
    except httpx.ConnectError:
        logger.warning("[ORCHESTRATOR] Translation service unreachable. Returning original.")
        return text
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Translation failed: {e}. Returning original.")
        return text
