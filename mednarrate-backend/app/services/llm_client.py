import asyncio
import logging
import time
from app.core.config import settings

logger = logging.getLogger(__name__)

_gemini_model = None

def _get_model():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    if not settings.GEMINI_API_KEY:
        return None
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
    safety_settings = [
        {"category": c, "threshold": "BLOCK_NONE"}
        for c in [
            "HARM_CATEGORY_HARASSMENT",
            "HARM_CATEGORY_HATE_SPEECH",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "HARM_CATEGORY_DANGEROUS_CONTENT",
        ]
    ]
    _gemini_model = genai.GenerativeModel(
        model_name=model_name,
        safety_settings=safety_settings,
    )
    return _gemini_model

def _sync_generate(prompt: str) -> str:
    model = _get_model()
    if model is None:
        logger.warning("GEMINI_API_KEY not set. Returning mock response.")
        return (
            "This is a mocked summary of the medical report analysis. "
            "It outlines the key findings, including normal and abnormal values. "
            "Set GEMINI_API_KEY in .env to enable real AI analysis."
        )
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_str = str(e)
            if "ResourceExhausted" in err_str or "429" in err_str:
                wait = 2 ** attempt
                logger.warning(f"Gemini quota hit, retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                logger.error(f"Gemini generation failed: {e}")
                raise
    raise RuntimeError("Gemini API quota exhausted after retries.")

async def generate(prompt: str, timeout: float = 60.0) -> str:
    return await asyncio.wait_for(
        asyncio.to_thread(_sync_generate, prompt),
        timeout=timeout
    )
