import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
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
    doc_id: uuid.UUID,
    payload: DocumentStatusUpdate,
    admin_ctx: AdminContext = Depends(require_permission("rag.manage")),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = payload.status
    if payload.status == DocLifecycleStatus.approved:
        doc.approval_state = "approved"
    elif payload.status == DocLifecycleStatus.review:
        doc.approval_state = "pending_review"
    elif payload.approval_state:
        doc.approval_state = payload.approval_state

    await log_admin_action(
        db=db,
        action="RAG_DOCUMENT_LIFECYCLE_UPDATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="KnowledgeDocument",
        resource_id=str(doc.id),
        metadata={"new_status": payload.status.value},
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

    # How patient-report search is doing (extra detail; never allowed to break this page).
    report_search = None
    try:
        from app.services.embedding_provider import embedding_status

        per_report = (
            await db.execute(
                select(RagChunk.report_id, func.count(RagChunk.id)).where(
                    RagChunk.report_id.is_not(None)
                ).group_by(RagChunk.report_id)
            )
        ).all()
        report_chunks = sum(int(n) for _, n in per_report)
        has_vector = RagChunk.embedding_json.is_not(None)
        if not str(settings.DATABASE_URL).startswith("postgresql"):
            # SQLite stores "no vector" as the JSON value null, which IS NOT NULL would still count.
            has_vector = and_(has_vector, func.json_type(RagChunk.embedding_json) != "null")
        with_vectors = (
            await db.execute(
                select(func.count(RagChunk.id)).where(
                    RagChunk.report_id.is_not(None), has_vector
                )
            )
        ).scalar() or 0
        emb = embedding_status()
        report_search = {
            "embeddings_enabled": emb["enabled"],
            "embedding_provider": emb["provider"],
            "vector_size": emb["dimensions"],
            "search_mode": "embeddings_with_keyword_backup" if emb["enabled"] else "keyword_only",
            "reports_indexed": len(per_report),
            "report_chunks": report_chunks,
            "chunks_with_vectors": int(with_vectors),
            "chunks_without_vectors": max(report_chunks - int(with_vectors), 0),
        }
    except Exception:
        report_search = None

    # The general-health notes the chat adds to its prompt (ChromaDB). count() is a local call.
    health_notes = {"passages": None, "ready": False}
    try:
        from app.services import rag as _rag

        if _rag.kb_collection is not None:
            excluded_sources = await _rag.unpublished_kb_sources(db)
            if excluded_sources:
                passages = len(_rag.kb_collection.get(
                    where={"source": {"$nin": sorted(excluded_sources)}},
                    include=[],
                )["ids"])
            else:
                passages = int(_rag.kb_collection.count())
            health_notes = {"passages": passages, "ready": passages > 0}
    except Exception:
        pass

    return {
        "status": "ok",
        "overview": {
            "index_status": rag_index_status,
            "error_summary": rag_error,
            "total_chunks": total_chunks,
            "total_documents": total_docs,
            "published_documents": published_docs,
            "report_search": report_search,
            "health_notes": health_notes,
        },
    }
