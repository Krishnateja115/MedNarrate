"""Embedding provider abstraction for RAG.

PRIVACY CONTRACT: callers must pass text that has ALREADY been de-identified
(see ``app.services.rag``).  This module is the only place that talks to an
external embedding API; no raw PHI should ever reach it.
"""
import logging
from typing import Callable, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

EmbedFn = Callable[..., Optional[List[float]]]


def _gemini_embedder() -> Optional[EmbedFn]:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        import google.generativeai as genai  # local import, not top-level

        genai.configure(api_key=api_key)

        def embed(text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type=task_type,
            )
            return result["embedding"]

        return embed
    except Exception as exc:  # init failure must degrade to BM25, not crash
        logger.warning("Failed to initialize Gemini embedder: %s", type(exc).__name__)
        return None


_PROVIDERS = {"gemini": _gemini_embedder}


def get_embedder() -> Optional[EmbedFn]:
    """Return the configured embedding callable, or None if unavailable."""
    provider = (getattr(settings, "EMBEDDING_PROVIDER", None) or settings.PRIMARY_LLM_PROVIDER or "gemini").lower()
    factory = _PROVIDERS.get(provider)
    if factory is None:
        logger.warning("RAG: no embedding provider for '%s'; embeddings disabled.", provider)
        return None
    return factory()
