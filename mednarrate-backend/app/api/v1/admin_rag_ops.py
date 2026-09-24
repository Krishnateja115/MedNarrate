from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset
from app.models.knowledge_document import DocLifecycleStatus, KnowledgeDocument
from app.models.rag_chunk import RagChunk
from app.services.audit import log_admin_action

router = APIRouter()


class DocumentStatusUpdate(BaseModel):
    status: DocLifecycleStatus
    approval_state: Optional[str] = None


@router.get("/documents")
async def list_documents(
    status: Optional[DocLifecycleStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("rag.view")),
    db: AsyncSession = Depends(get_db),
):
    limit = clamp_limit(limit)
    stmt = select(KnowledgeDocument)
    if status:
        stmt = stmt.where(KnowledgeDocument.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        stmt.order_by(desc(KnowledgeDocument.updated_at))
        .offset(page_to_offset(page, limit))
        .limit(limit)
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    items = [
        {
            "id": str(d.id),
            "name": d.name,
            "version": d.version,
            "status": d.status,
            "approval_state": d.approval_state,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
        }
        for d in docs
    ]

    return build_pagination_response(items, total, page, limit)


@router.patch("/documents/{doc_id}/status")
async def update_document_status(
    doc_id: str,
    payload: DocumentStatusUpdate,
    admin_ctx: AdminContext = Depends(require_permission("rag.manage")),
    db: AsyncSession = Depends(get_db),
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
        metadata={"new_status": payload.status},
    )

    await db.commit()
    return {"status": "ok"}


@router.get("/status")
async def get_rag_status(
    admin_ctx: AdminContext = Depends(require_permission("rag.view")),
    db: AsyncSession = Depends(get_db),
):
    """RAG index status. Distinguishes: healthy, empty, down, unknown."""
    total_chunks = (await db.execute(select(func.count(RagChunk.id)))).scalar() or 0
    total_docs = (
        await db.execute(select(func.count(KnowledgeDocument.id)))
    ).scalar() or 0
    published_docs = (
        await db.execute(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.status == DocLifecycleStatus.published
            )
        )
    ).scalar() or 0
    failed_docs = (
        await db.execute(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.status == DocLifecycleStatus.failed
            )
        )
    ).scalar() or 0

    # Real RAG health probe
    rag_index_status = "unknown"
    rag_error = None
    try:
        from app.services.rag import rag_service

        rag_health = await rag_service.health_check()
        if rag_health.get("reachable"):
            # Use the real probe status which confirms vector store responsiveness
            rag_index_status = rag_health.get("status", "healthy")
        else:
            rag_index_status = "down"
            rag_error = rag_health.get("error_summary", "Vector store not reachable")
    except Exception as e:
        rag_index_status = "unknown"
        rag_error = f"RAG service health check unavailable: {str(e)}"

    return {
        "status": "ok",
        "overview": {
            "index_status": rag_index_status,
            "error_summary": rag_error,
            "total_chunks": total_chunks,
            "total_documents": total_docs,
            "published_documents": published_docs,
            "failed_documents": failed_docs,
        },
    }
