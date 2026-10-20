"""RAG service — embedding and retrieval.

PRIVACY ARCHITECTURE:
  - All report text is de-identified with `deidentify_prompt_text` BEFORE
    being chunked or embedded.
  - De-identification is pinned to "deidentified" mode regardless of the
    LLM_SEND_MODE setting.
  - Embeddings come from `app.services.embedding_provider.get_embedder()`.
  - External transmission: when GEMINI_API_KEY is configured, de-identified
    chunk text is sent to the Google Gemini Embedding API.  No raw PII/PHI is
    ever transmitted; only de-identified chunk text and anonymized query text.
  - Telemetry never logs raw report text (only chunk index / error type).
  - Failures fall back safely to BM25 keyword retrieval without raising.
  - No direct `genai.configure()` or `genai.embed_content()` calls outside
    this module or `get_embedder()`.

HOW RETRIEVAL WORKS:
  1. Ingestion (once per report, `process_report_for_rag`): de-identify, split into
     overlapping chunks, embed each chunk, store text + vector in `rag_chunks`.
  2. Retrieval (`retrieve_chunks`): embed the question, rank the report's chunks by
     cosine similarity, return the best `top_k` in document order.
  3. Reports indexed while embeddings were off (or while the provider was down) get their
     missing vectors filled in on the first question, within a small time budget.
  4. If vectors are unavailable for any reason the same chunks are ranked with BM25.
"""
import re
import logging
import asyncio
import threading
import time
import uuid
from typing import List, Optional

import numpy as np
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.models.rag_chunk import RagChunk
from app.core.config import settings

logger = logging.getLogger(__name__)

KB_INDEX = os.path.join(os.path.dirname(__file__), "..", "..", "data", "kb_index")
try:
    import chromadb
    chroma_client = chromadb.PersistentClient(
        path=KB_INDEX,
        settings=chromadb.Settings(anonymized_telemetry=False),
    )
    kb_collection = chroma_client.get_or_create_collection("medical_knowledge")
except Exception as _chroma_init_err:
    logger.warning("Could not initialize ChromaDB: %s", _chroma_init_err)
    kb_collection = None


from app.services.embedding_provider import EMBEDDING_DIM, get_embedder  # noqa: E402
from app.services.privacy import deidentify_prompt_text as _deidentify  # noqa: E402


def _rag_deidentify(text: str) -> str:
    """De-identify for RAG. The mode is pinned: RAG text goes to an external
    embedding API, so LLM_SEND_MODE=full (a chat/LLM preference) must never
    disable this boundary."""
    return _deidentify(text, mode="deidentified")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    # Very rough estimate: 4 chars per token
    char_chunk_size = chunk_size * 4
    char_overlap = overlap * 4

    header_pattern = re.compile(r'^([A-Z\s]+):', re.MULTILINE)

    chunks = []
    lines = text.split('\n')
    current_chunk = ""
    current_header = ""

    for line in lines:
        header_match = header_pattern.match(line)
        if header_match:
            current_header = line

        if len(current_chunk) + len(line) > char_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-char_overlap:] if len(current_chunk) > char_overlap else current_chunk
            current_chunk = (
                current_header + "\n" + overlap_text + "\n" + line
                if current_header
                else overlap_text + "\n" + line
            )
        else:
            current_chunk += line + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------

def _is_postgres() -> bool:
    return settings.DATABASE_URL.startswith("postgresql")


def _as_vector(value) -> Optional[np.ndarray]:
    """A stored or freshly embedded vector as a 1-D float array, or None if it is unusable.

    Handles lists (SQLite JSON) and numpy arrays (pgvector) alike."""
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return None
    if arr.ndim != 1 or arr.size == 0 or not np.all(np.isfinite(arr)):
        return None
    return arr


def _storable_embedding(value) -> Optional[List[float]]:
    """The vector as a plain list ready to store, or None.

    On PostgreSQL the column is Vector(EMBEDDING_DIM); a vector of any other length would make the
    whole commit fail and lose every chunk of the report, so it is dropped instead."""
    arr = _as_vector(value)
    if arr is None:
        return None
    if _is_postgres() and arr.size != EMBEDDING_DIM:
        logger.error("Embedding has %d numbers but the index expects %d; ignoring it.", arr.size, EMBEDDING_DIM)
        return None
    return arr.tolist()


async def _embed(embedder, text: str, task_type: str):
    """Call the (blocking) embedder in a thread; one retry after a short pause, because the
    free embedding tiers rate-limit bursts."""
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            return await asyncio.to_thread(embedder, text, task_type)
        except Exception as e:  # noqa: BLE001 - provider errors vary
            last_error = e
            if attempt == 0:
                await asyncio.sleep(1.0)
    assert last_error is not None
    raise last_error


# ---------------------------------------------------------------------------
# Report ingestion
# ---------------------------------------------------------------------------

async def process_report_for_rag(report_id: uuid.UUID, report_text: str, db: AsyncSession):
    """Chunk, de-identify, and embed a report for RAG retrieval.

    Privacy: report_text is de-identified before any external transmission.
    """
    # Remove stale chunks first
    stmt = select(RagChunk).where(RagChunk.report_id == report_id)
    existing_chunks = (await db.execute(stmt)).scalars().all()
    for chunk in existing_chunks:
        await db.delete(chunk)
    await db.commit()

    # De-identify BEFORE chunking and BEFORE any external call
    clean_text = _rag_deidentify(report_text)
    chunks = chunk_text(clean_text)

    embedder = get_embedder()
    embedding_available = embedder is not None

    for i, chunk in enumerate(chunks):
        embedding = None
        if embedding_available:
            try:
                embedding = _storable_embedding(await _embed(embedder, chunk, "retrieval_document"))
            except Exception as e:
                # Log only the error type, never raw chunk text. If the provider is failing, stop
                # calling it for the rest of this report; the missing vectors are filled in later.
                logger.error("Embedding failed for chunk %d of report %s: %s", i, report_id, type(e).__name__)
                embedding_available = False

        db_chunk = RagChunk(
            report_id=report_id,
            chunk_index=i,
            chunk_text=chunk,
            embedding_json=embedding,
        )
        db.add(db_chunk)

    await db.commit()


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

_BACKFILL_MAX_CHUNKS = 60
_BACKFILL_BUDGET_SECONDS = 12.0

# Punctuation that separates words. "." is deliberately not here so "12.5" stays one token, and
# combining marks of Indian scripts are not here so Hindi/Telugu words are not cut in the middle.
_WORD_BREAKS = re.compile(r"[,;:!?()\[\]{}\"'“”‘’/\\|<>=*_#+~`@^&%$\-–—]")


def _tokens(text: str) -> List[str]:
    words = _WORD_BREAKS.sub(" ", (text or "").lower()).split()
    return [w for w in (word.strip(".") for word in words) if w]


async def _backfill_missing_embeddings(chunks: List[RagChunk], embedder, db: AsyncSession) -> None:
    """Embed chunks that were stored without a vector (embeddings were off, or the provider
    failed during upload). Stops at a time budget; the next question continues where this one
    stopped. The stored chunk text is already de-identified."""
    missing = [c for c in chunks if _as_vector(c.embedding_json) is None]
    if not missing:
        return
    started = time.monotonic()
    filled = 0
    for chunk in missing[:_BACKFILL_MAX_CHUNKS]:
        if time.monotonic() - started > _BACKFILL_BUDGET_SECONDS:
            break
        try:
            embedding = _storable_embedding(await _embed(embedder, chunk.chunk_text, "retrieval_document"))
        except Exception as e:
            logger.error("Backfill embedding failed: %s", type(e).__name__)
            break
        if embedding is None:
            break
        chunk.embedding_json = embedding
        filled += 1
    if filled:
        try:
            await db.commit()
        except Exception as e:
            logger.error("Could not save backfilled embeddings: %s", type(e).__name__)
            await db.rollback()


def _dense_top(rows, query_vec: np.ndarray, top_k: int) -> list:
    """Rank rows (index, text, vector) by cosine similarity to the query. Returns [] if any vector
    is missing or the sizes disagree, so the caller falls back to keyword search."""
    scored = []
    q_norm = float(np.linalg.norm(query_vec))
    for row in rows:
        vec = row[2]
        if vec is None or vec.shape != query_vec.shape:
            return []
        denom = q_norm * float(np.linalg.norm(vec))
        sim = float(np.dot(query_vec, vec) / denom) if denom else 0.0
        scored.append((sim, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:top_k]]


def _bm25_top(rows, query: str, top_k: int) -> list:
    """Keyword ranking over the same rows. Chunks that share no word with the question are only
    used to fill up to top_k, in document order."""
    from rank_bm25 import BM25Okapi

    corpus = [_tokens(r[1]) for r in rows]
    query_tokens = _tokens(query)
    if not query_tokens or not any(corpus):
        return list(rows[:top_k])
    scores = BM25Okapi(corpus).get_scores(query_tokens)
    order = sorted(range(len(rows)), key=lambda i: (-scores[i], i))
    return [rows[i] for i in order[:top_k]]


async def retrieve_chunks(query: str, report_id: uuid.UUID, db: AsyncSession, top_k: int = 5) -> str:
    """Retrieve relevant chunks for a query against a specific report.

    Privacy: query is de-identified before any embedding call.
    """
    safe_query = _rag_deidentify(query)

    stmt = select(RagChunk).where(RagChunk.report_id == report_id).order_by(RagChunk.chunk_index)
    result = await db.execute(stmt)
    chunks = result.scalars().all()

    if not chunks:
        return ""

    embedder = get_embedder()
    if embedder is not None:
        try:
            await _backfill_missing_embeddings(chunks, embedder, db)
        except Exception as e:
            logger.error("Embedding backfill failed: %s", type(e).__name__)

    # Plain values from here on: nothing below touches the ORM objects again.
    rows = [(c.chunk_index, c.chunk_text, _as_vector(c.embedding_json)) for c in chunks]
    total = len(rows)

    top_rows: list = []
    if embedder is not None and all(r[2] is not None for r in rows):
        try:
            q_vec = _as_vector(await _embed(embedder, safe_query, "retrieval_query"))
            if q_vec is not None:
                top_rows = _dense_top(rows, q_vec, top_k)
        except Exception as e:
            logger.error("Semantic search failed, falling back to BM25: %s", type(e).__name__)

    if not top_rows:
        top_rows = _bm25_top(rows, safe_query, top_k)

    context_parts = []
    total_chars = 0
    top_rows = sorted(top_rows, key=lambda r: r[0])

    for index, text, _vec in top_rows:
        part = f"[Chunk {index + 1}/{total}]: {text}"
        if total_chars + len(part) > 16000:
            break
        context_parts.append(part)
        total_chars += len(part)

    return "\n\n".join(context_parts)


_kb_lock = threading.Lock()


def _query_kb(text: str, top_k: int) -> List[str]:
    """Blocking knowledge-base search. One at a time: the first call downloads the embedding model,
    and two threads must not download (and write) the same file together."""
    with _kb_lock:
        available = kb_collection.count()
        if not available:
            return []
        results = kb_collection.query(query_texts=[text], n_results=min(top_k, available))
    if results and results["documents"] and results["documents"][0]:
        return list(results["documents"][0])
    return []


async def retrieve_kb_context(query: str, top_k: int = 3) -> str:
    """Query the global medical knowledge base."""
    if not kb_collection:
        return ""
    try:
        documents = await asyncio.to_thread(_query_kb, _rag_deidentify(query), top_k)
        return "\n\n".join(documents)
    except Exception as e:
        logger.error("Error querying KB: %s", type(e).__name__)
    return ""


class RagService:
    async def health_check(self):
        """
        Runs a lightweight test query against the vector index (ChromaDB or Postgres fallback)
        to confirm it's actually alive and can return results within a reasonable timeout.
        """
        timeout_seconds = 15.0

        try:
            await asyncio.wait_for(
                retrieve_kb_context("test health ping", top_k=1),
                timeout=timeout_seconds,
            )
            return {
                "reachable": True,
                "status": "healthy",
                "error_summary": None,
            }
        except asyncio.TimeoutError:
            return {
                "reachable": False,
                "status": "down",
                "error_summary": f"Vector search timed out after {timeout_seconds}s",
            }
        except Exception as e:
            return {
                "reachable": False,
                "status": "down",
                "error_summary": f"Vector search failed: {type(e).__name__}",
            }


rag_service = RagService()
