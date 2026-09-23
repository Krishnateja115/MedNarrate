from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.knowledge_document import KnowledgeDocument, DocLifecycleStatus
from app.models.rag_chunk import RagChunk
from app.services.audit import log_admin_action

router = APIRouter()

class DocumentStatusUpdate(BaseModel):
    status: DocLifecycleStatus
    approval_state: Optional[str] = None

@router.get("/documents")
async def list_documents(
    status: Optional[DocLifecycleStatus] = None,
    admin_ctx: AdminContext = Depends(require_permission("rag.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(KnowledgeDocument).order_by(desc(KnowledgeDocument.updated_at))
    if status:
        stmt = stmt.where(KnowledgeDocument.status == status)
        
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    return {
        "status": "ok",
        "documents": [
            {
                "id": d.id,
                "name": d.name,
                "version": d.version,
                "status": d.status,
                "approval_state": d.approval_state,
                "created_at": d.created_at,
                "updated_at": d.updated_at
            } for d in docs
        ]
    }

@router.patch("/documents/{doc_id}/status")
async def update_document_status(
    doc_id: str,
    payload: DocumentStatusUpdate,
    admin_ctx: AdminContext = Depends(require_permission("rag.manage")),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.status = payload.status
    if payload.approval_state:
        doc.approval_state = payload.approval_state
        
    await log_admin_action(
        db=db,
        action="RAG_DOCUMENT_LIFECYCLE_UPDATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="KnowledgeDocument",
        resource_id=doc.id,
        metadata={"new_status": payload.status}
    )
    
    await db.commit()
    return {"status": "ok"}

@router.get("/status")
async def get_rag_status(
    admin_ctx: AdminContext = Depends(require_permission("rag.view")),
    db: AsyncSession = Depends(get_db)
):
    total_chunks = (await db.execute(select(func.count(RagChunk.id)))).scalar() or 0
    total_docs = (await db.execute(select(func.count(KnowledgeDocument.id)))).scalar() or 0
    published_docs = (await db.execute(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.status == DocLifecycleStatus.published))).scalar() or 0
    
    # In a real system, we'd query the vector DB for true index health
    index_health = "healthy" if total_chunks > 0 else "empty"
    
    return {
        "status": "ok",
        "overview": {
            "index_status": index_health,
            "total_chunks": total_chunks,
            "total_documents": total_docs,
            "published_documents": published_docs
        }
    }
