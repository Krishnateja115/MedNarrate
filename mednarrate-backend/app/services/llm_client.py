import logging
import httpx
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate(prompt: str, timeout: float = 30.0) -> str:
    """
    Generates text using the configured LLM provider.
    Priority:
    1. Google Gemini (if GEMINI_API_KEY is set)
    2. Ollama (if OLLAMA_URL or local Ollama is active)
    
    If no LLM service is available, raises RuntimeError.
    Does NOT return fake or hardcoded runtime medical analysis.
    """
    # 1. Check Gemini configuration
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY.strip())
            model_name = getattr(settings, "GEMINI_MODEL_NAME", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            if response and response.text:
                return response.text.strip()
            raise ValueError("Empty response received from Gemini API.")
        except Exception as e:
            logger.error(f"Gemini API generation failed: {e}")
            raise RuntimeError(f"Gemini LLM service error: {e}")

    # 2. Check Ollama
    ollama_base_url = settings.OLLAMA_URL or "http://localhost:11434"
    ollama_url = f"{ollama_base_url.rstrip('/')}/api/generate"
    try:
        async with httpx.AsyncClient(timeout=min(timeout, 15.0)) as client:
            resp = await client.post(
                ollama_url,
                json={
                    "model": getattr(settings, "OLLAMA_MODEL", "llama3:8b"),
                    "prompt": prompt,
                    "stream": False,
                }
            )
            resp.raise_for_status()
            res_data = resp.json()
            if "response" in res_data:
                return res_data["response"].strip()
            raise ValueError("Invalid response format from Ollama API.")
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        raise RuntimeError("AI analysis is currently unavailable. Please verify the LLM service configuration (GEMINI_API_KEY or OLLAMA_URL) and try again.")

