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

# Must equal the size of the pgvector column (rag_chunks.embedding_json is Vector(768)).
# gemini-embedding-001 returns 3072 numbers unless it is asked for fewer, and a
# 3072-number vector cannot be stored in a 768 column.
EMBEDDING_DIM = 768


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
                output_dimensionality=EMBEDDING_DIM,
            )
            return result["embedding"]

        return embed
    except Exception as exc:  # init failure must degrade to BM25, not crash
        logger.warning("Failed to initialize Gemini embedder: %s", type(exc).__name__)
        return None


# "dev_gemini" is the same Gemini API key under its development name. Without this alias a
# backend whose AI provider is dev_gemini silently ran with embeddings switched off.
_PROVIDERS = {"gemini": _gemini_embedder, "dev_gemini": _gemini_embedder}


def _gemini_key_allowed() -> bool:
    """A direct Gemini key is refused in production unless explicitly allowed (same rule as llm_client)."""
    if (getattr(settings, "ENVIRONMENT", "development") or "").lower() != "production":
        return True
    return bool(getattr(settings, "ALLOW_GEMINI_API_KEY_IN_PRODUCTION", False))


def _provider_name() -> str:
    explicit = (getattr(settings, "EMBEDDING_PROVIDER", None) or "").strip().lower()
    if explicit:
        return explicit
    primary = (settings.PRIMARY_LLM_PROVIDER or "").strip().lower()
    if primary in _PROVIDERS:
        return primary
    # The answering model (for example Groq) has no embedding service here. If a Gemini key is
    # configured and allowed, use it for embeddings instead of silently dropping to keyword search.
    if (settings.GEMINI_API_KEY or "").strip() and _gemini_key_allowed():
        return "gemini"
    return primary or "gemini"


def get_embedder() -> Optional[EmbedFn]:
    """Return the configured embedding callable, or None if unavailable."""
    provider = _provider_name()
    factory = _PROVIDERS.get(provider)
    if factory is None:
        logger.warning("RAG: no embedding provider for '%s'; embeddings disabled.", provider)
        return None
    return factory()


def embedding_status() -> dict:
    """What the admin portal shows: whether report search can use embeddings, and which provider."""
    try:
        enabled = get_embedder() is not None
    except Exception:
        enabled = False
    return {
        "enabled": enabled,
        "provider": _provider_name() if enabled else None,
        "dimensions": EMBEDDING_DIM,
    }
