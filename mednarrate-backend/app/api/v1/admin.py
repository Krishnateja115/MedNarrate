from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.admin_auth import AdminContext, get_admin_context, require_permission, require_any_permission
from app.services.audit import log_admin_action
from app.schemas.user import AdminIdentityOut

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

@router.get("/me", response_model=AdminIdentityOut)
async def get_admin_me(
    admin_ctx: AdminContext = Depends(get_admin_context)
):
    user_data = admin_ctx.user.__dict__.copy()
    user_data["permissions"] = list(admin_ctx.permissions)
    return user_data

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
from app.api.v1.admin_users import router as users_router
from app.api.v1.admin_reports import router as reports_router
from app.api.v1.admin_support import router as support_router
from app.api.v1.admin_help_center import router as help_center_router
from app.api.v1.admin_ai_ops import router as ai_ops_router
from app.api.v1.admin_chat_ops import router as chat_ops_router
from app.api.v1.admin_rag_ops import router as rag_ops_router
from app.api.v1.admin_automation_ops import router as automation_ops_router

# Release Governance & Operations Routers
from app.api.v1.admin_analytics import router as analytics_router
from app.api.v1.admin_search import router as search_router
from app.api.v1.admin_alerts import router as alerts_router

# Privileged Governance Layer Routers
from app.api.v1.admin_security import router as security_router
from app.api.v1.admin_admins import router as admins_router
from app.api.v1.admin_roles import router as roles_router
from app.api.v1.admin_audit import router as audit_router
from app.api.v1.admin_breakglass import router as breakglass_router
from app.api.v1.admin_privacy import router as privacy_router
from app.api.v1.admin_feature_flags import router as feature_flags_router
from app.api.v1.admin_ai_config import router as ai_config_router
from app.api.v1.admin_settings import router as settings_router
from app.api.v1.admin_announcements import router as announcements_router

router.include_router(dashboard_router, prefix="/dashboard", tags=["Admin Dashboard"])
router.include_router(analytics_router, prefix="/analytics", tags=["Admin Analytics"])
router.include_router(search_router, prefix="/search", tags=["Admin Search"])
router.include_router(alerts_router, prefix="/alerts", tags=["Admin Alerts"])
router.include_router(health_router, prefix="/system", tags=["Admin System"])
router.include_router(jobs_router, prefix="/jobs", tags=["Admin Jobs"])
router.include_router(diagnostics_router, prefix="/diagnostics", tags=["Admin Diagnostics"])
router.include_router(incidents_router, prefix="/incidents", tags=["Admin Incidents"])
router.include_router(users_router, prefix="/users", tags=["Admin Users"])
router.include_router(reports_router, prefix="/reports", tags=["Admin Reports"])
router.include_router(support_router, prefix="/support", tags=["Admin Support"])
router.include_router(help_center_router, prefix="/help-center", tags=["Admin Help Center"])
router.include_router(ai_ops_router, prefix="/ai-ops", tags=["Admin AI Ops"])
router.include_router(chat_ops_router, prefix="/chat-ops", tags=["Admin Chat Ops"])
router.include_router(rag_ops_router, prefix="/rag-ops", tags=["Admin RAG Ops"])
router.include_router(automation_ops_router, prefix="/automation-ops", tags=["Admin Automation Ops"])

# Register Privileged Governance Routers
router.include_router(security_router, prefix="/security", tags=["Admin Security Center"])
router.include_router(admins_router, prefix="/admins", tags=["Admin Accounts"])
router.include_router(roles_router, prefix="/roles", tags=["Admin RBAC Roles & Permissions"])
router.include_router(audit_router, prefix="", tags=["Admin Audit Logs"])
router.include_router(breakglass_router, prefix="", tags=["Admin Break-Glass Temporary Access"])
router.include_router(privacy_router, prefix="", tags=["Admin Privacy Center"])
router.include_router(feature_flags_router, prefix="", tags=["Admin Feature Flags"])
router.include_router(ai_config_router, prefix="", tags=["Admin AI Configuration"])
router.include_router(settings_router, prefix="", tags=["Admin Settings & Maintenance"])
router.include_router(announcements_router, prefix="", tags=["Admin Announcements"])


