from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.admin_auth import AdminContext, get_admin_context, require_permission, require_any_permission
from app.services.audit import log_admin_action

router = APIRouter()

@router.get("/health")
async def admin_health(
    request: Request,
    admin_ctx: AdminContext = Depends(get_admin_context),
    db: AsyncSession = Depends(get_db)
):
    # This is accessible by any valid admin, but we log the action
    await log_admin_action(
        db=db,
        action="ADMIN_HEALTH_CHECK",
        actor_admin_id=admin_ctx.user.id,
        request=request,
        metadata={"permissions": list(admin_ctx.permissions)}
    )
    await db.commit()
    return {"status": "ok", "message": "Admin services are running"}

@router.get("/kb-stats")
async def get_kb_stats(
    request: Request,
    admin_ctx: AdminContext = Depends(require_permission("knowledge_base.view")),
    db: AsyncSession = Depends(get_db)
):
    await log_admin_action(
        db=db,
        action="VIEW_KB_STATS",
        actor_admin_id=admin_ctx.user.id,
        permission_used="knowledge_base.view",
        request=request
    )
    await db.commit()
    # Mock KB stats for now
    return {
        "status": "ok",
        "total_documents": 5,
        "total_chunks": 42
    }

@router.get("/llm-status")
async def get_admin_llm_status(
    request: Request,
    admin_ctx: AdminContext = Depends(require_any_permission(["ai.view", "ai.manage"])),
    db: AsyncSession = Depends(get_db)
):
    from app.services.llm_client import llm_client_instance
    from app.core.config import settings

    provider_name = (settings.PRIMARY_LLM_PROVIDER or "auto").lower().strip()
    provider = llm_client_instance.get_provider(provider_name)
    provider_health = await provider.health_check()
    
    await log_admin_action(
        db=db,
        action="VIEW_LLM_STATUS",
        actor_admin_id=admin_ctx.user.id,
        permission_used="ai.view",
        request=request,
        metadata={"provider": provider_name}
    )
    await db.commit()

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "selected_provider": provider_name,
        "active_provider_health": provider_health,
        "privacy_mode": settings.LLM_SEND_MODE,
        "rag_enabled": True,
        "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        "max_retries": settings.MAX_RETRIES,
        "cost_guardrails": {
            "max_input_tokens": settings.MAX_INPUT_TOKENS,
            "max_output_tokens": settings.MAX_OUTPUT_TOKENS,
            "max_rag_chunks": settings.MAX_RAG_CHUNKS,
        }
    }

from app.api.v1.admin_dashboard import router as dashboard_router
from app.api.v1.admin_health import router as health_router
from app.api.v1.admin_jobs import router as jobs_router
from app.api.v1.admin_diagnostics import router as diagnostics_router
from app.api.v1.admin_incidents import router as incidents_router

router.include_router(dashboard_router, prefix="/dashboard", tags=["Admin Dashboard"])
router.include_router(health_router, prefix="/system", tags=["Admin System"])
router.include_router(jobs_router, prefix="/jobs", tags=["Admin Jobs"])
router.include_router(diagnostics_router, prefix="/diagnostics", tags=["Admin Diagnostics"])
router.include_router(incidents_router, prefix="/incidents", tags=["Admin Incidents"])
