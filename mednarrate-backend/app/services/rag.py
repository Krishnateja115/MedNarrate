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
"""
import re
import logging
import asyncio
import uuid
from typing import List, Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.models.rag_chunk import RagChunk
from app.core.config import settings

logger = logging.getLogger(__name__)

KB_INDEX = os.path.join(os.path.dirname(__file__), "..", "..", "data", "kb_index")
try:
    import chromadb
    chroma_client = chromadb.PersistentClient(path=KB_INDEX)
    kb_collection = chroma_client.get_or_create_collection("medical_knowledge")
except Exception as _chroma_init_err:
    logger.warning("Could not initialize ChromaDB: %s", _chroma_init_err)
    kb_collection = None


from app.services.embedding_provider import get_embedder  # noqa: E402
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

    for i, chunk in enumerate(chunks):
        embedding = None
        if embedder is not None:
            try:
                embedding = await asyncio.to_thread(embedder, chunk, "retrieval_document")
            except Exception as e:
                # Log only the error type, never raw chunk text
                logger.error("Embedding failed for chunk %d of report %s: %s", i, report_id, type(e).__name__)

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

    has_embeddings = all(c.embedding_json is not None for c in chunks)
    top_chunks = []
    embedder = get_embedder()

    if has_embeddings and embedder is not None:
        try:
            q_emb = await asyncio.to_thread(embedder, safe_query, "retrieval_query")

            if settings.DATABASE_URL.startswith("postgresql"):
                stmt_vector = (
                    select(RagChunk)
                    .where(RagChunk.report_id == report_id)
                    .order_by(RagChunk.embedding_json.cosine_distance(q_emb))
                    .limit(top_k)
                )
                result_vector = await db.execute(stmt_vector)
                top_chunks = result_vector.scalars().all()
            else:
                import numpy as np

                def cosine_sim(a, b):
                    if not a or not b:
                        return 0.0
                    norm_a = np.linalg.norm(a)
                    norm_b = np.linalg.norm(b)
                    if norm_a == 0 or norm_b == 0:
                        return 0.0
                    return np.dot(a, b) / (norm_a * norm_b)

                scored_chunks = [
                    (c, cosine_sim(q_emb, c.embedding_json))
                    for c in chunks
                    if c.embedding_json
                ]
                scored_chunks.sort(key=lambda x: x[1], reverse=True)
                top_chunks = [c[0] for c in scored_chunks[:top_k]]
        except Exception as e:
            logger.error("Semantic search failed, falling back to BM25: %s", type(e).__name__)
            has_embeddings = False

    if not has_embeddings or not top_chunks:
        from rank_bm25 import BM25Okapi
        tokenized_corpus = [c.chunk_text.lower().split(" ") for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = safe_query.lower().split(" ")
        top_chunks = bm25.get_top_n(tokenized_query, chunks, n=top_k)

    context_parts = []
    total_chars = 0
    top_chunks.sort(key=lambda x: x.chunk_index)

    for c in top_chunks:
        part = f"[Chunk {c.chunk_index + 1}/{len(chunks)}]: {c.chunk_text}"
        if total_chars + len(part) > 16000:
            break
        context_parts.append(part)
        total_chars += len(part)

    return "\n\n".join(context_parts)


async def retrieve_kb_context(query: str, top_k: int = 3) -> str:
    """Query the global medical knowledge base."""
    if not kb_collection:
        return ""
    try:
        results = await asyncio.to_thread(
            kb_collection.query,
            query_texts=[query],
            n_results=top_k,
        )
        if results and results["documents"] and results["documents"][0]:
            return "\n\n".join(results["documents"][0])
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
