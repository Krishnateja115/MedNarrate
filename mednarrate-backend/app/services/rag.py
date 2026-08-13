from sqlalchemy.future import select
from app.models.knowledge_chunk import KnowledgeChunk
from app.core.database import AsyncSessionLocal
from app.services.model_registry import get_embedding_model

async def retrieve_chunks(query: str, top_k: int = 5, min_similarity: float = 0.3) -> list[KnowledgeChunk]:
    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()
    
    async with AsyncSessionLocal() as db:
        # Distance calculation
        stmt = select(KnowledgeChunk).order_by(
            KnowledgeChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k)
        
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        return chunks
