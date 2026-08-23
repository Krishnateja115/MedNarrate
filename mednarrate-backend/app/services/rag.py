import re
import json
import logging
from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai

from app.models.rag_chunk import RagChunk
from app.core.config import settings
import chromadb
import os

logger = logging.getLogger(__name__)

KB_INDEX = os.path.join(os.path.dirname(__file__), "..", "..", "data", "kb_index")
try:
    chroma_client = chromadb.PersistentClient(path=KB_INDEX)
    kb_collection = chroma_client.get_or_create_collection("medical_knowledge")
except Exception as e:
    logger.warning(f"Could not initialize ChromaDB: {e}")
    kb_collection = None

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    # Very rough estimate: 4 chars per token
    char_chunk_size = chunk_size * 4
    char_overlap = overlap * 4
    
    # Try to identify headers (all caps followed by colon)
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
            # Start new chunk with overlap and current header if any
            overlap_text = current_chunk[-char_overlap:] if len(current_chunk) > char_overlap else current_chunk
            current_chunk = current_header + "\n" + overlap_text + "\n" + line if current_header else overlap_text + "\n" + line
        else:
            current_chunk += line + "\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

import uuid

async def process_report_for_rag(report_id: uuid.UUID, report_text: str, db: AsyncSession):
    chunks = chunk_text(report_text)
    
    # Generate embeddings using Gemini if available
    for i, chunk in enumerate(chunks):
        embedding = None
        if settings.GEMINI_API_KEY:
            try:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=chunk,
                    task_type="retrieval_document"
                )
                embedding = result['embedding']
            except Exception as e:
                logger.error(f"Embedding failed: {e}")
                
        # Use simple list for JSON column if Postgres pgvector is not fully compatible or if we fallback
        db_chunk = RagChunk(
            report_id=report_id,
            chunk_index=i,
            chunk_text=chunk,
            embedding_json=embedding
        )
        db.add(db_chunk)
        
    await db.commit()

async def retrieve_chunks(query: str, report_id: uuid.UUID, db: AsyncSession, top_k: int = 5) -> str:
    # 1. Fetch chunks for the report
    stmt = select(RagChunk).where(RagChunk.report_id == report_id).order_by(RagChunk.chunk_index)
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    
    if not chunks:
        return ""
        
    # 2. Check if we have embeddings
    has_embeddings = all(c.embedding_json for c in chunks)
    top_chunks = []
    
    if has_embeddings and settings.GEMINI_API_KEY:
        try:
            # Get query embedding
            q_res = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            q_emb = q_res['embedding']
            
            if settings.DATABASE_URL.startswith("postgresql"):
                stmt_vector = select(RagChunk).where(RagChunk.report_id == report_id).order_by(RagChunk.embedding_json.cosine_distance(q_emb)).limit(top_k)
                result_vector = await db.execute(stmt_vector)
                top_chunks = result_vector.scalars().all()
            else:
                import numpy as np
                def cosine_sim(a, b):
                    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                    
                scored_chunks = [(c, cosine_sim(q_emb, c.embedding_json)) for c in chunks]
                scored_chunks.sort(key=lambda x: x[1], reverse=True)
                top_chunks = [c[0] for c in scored_chunks[:top_k]]
        except Exception as e:
            logger.error(f"Semantic search failed, falling back to BM25: {e}")
            has_embeddings = False
            
    if not has_embeddings or not top_chunks:
        # BM25 Fallback
        from rank_bm25 import BM25Okapi
        tokenized_corpus = [c.chunk_text.lower().split(" ") for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.lower().split(" ")
        top_chunks = bm25.get_top_n(tokenized_query, chunks, n=top_k)
        
    # 3. Context assembly
    context_parts = []
    total_chars = 0
    # Sort top chunks by original index to maintain chronological sense
    top_chunks.sort(key=lambda x: x.chunk_index)
    
    for c in top_chunks:
        part = f"[Chunk {c.chunk_index + 1}/{len(chunks)}]: {c.chunk_text}"
        if total_chars + len(part) > 16000: # ~4000 tokens
            break
        context_parts.append(part)
        total_chars += len(part)
        
    return "\n\n".join(context_parts)

async def retrieve_kb_context(query: str, top_k: int = 3) -> str:
    """Query the global medical knowledge base."""
    if not kb_collection:
        return ""
    try:
        results = kb_collection.query(
            query_texts=[query],
            n_results=top_k
        )
        if results and results['documents'] and results['documents'][0]:
            return "\n\n".join(results['documents'][0])
    except Exception as e:
        logger.error(f"Error querying KB: {e}")
    return ""
