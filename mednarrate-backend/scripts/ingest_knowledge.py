import asyncio
import hashlib
import json
import os
import glob
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.knowledge_chunk import KnowledgeChunk
from app.services.model_registry import get_embedding_model

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge")

async def ingest():
    model = get_embedding_model()
    
    # 1. Gather all files
    files = glob.glob(os.path.join(KNOWLEDGE_DIR, "**", "*.md"), recursive=True) + \
            glob.glob(os.path.join(KNOWLEDGE_DIR, "**", "*.txt"), recursive=True)
            
    count = 0
    
    async with AsyncSessionLocal() as db:
        for file_path in files:
            source = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
            # Chunking strategy: split by double newline
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            
            for p in paragraphs:
                if p.startswith("#") and len(p.split("\n")) == 1:
                    continue # Skip pure header lines as independent chunks
                    
                content_hash = hashlib.sha256(p.encode('utf-8')).hexdigest()
                
                stmt = select(KnowledgeChunk).where(KnowledgeChunk.content_hash == content_hash)
                result = await db.execute(stmt)
                existing = result.scalars().first()
                
                if not existing:
                    embedding = model.encode(p).tolist()
                    chunk = KnowledgeChunk(
                        source=source,
                        content=p,
                        content_hash=content_hash,
                        embedding=embedding,
                        metadata_json={"chunk_type": "paragraph"}
                    )
                    db.add(chunk)
                    count += 1
                    
        await db.commit()
        print(f"Ingested {count} new knowledge chunks.")

if __name__ == "__main__":
    asyncio.run(ingest())
