from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

@router.get("/health")
async def admin_health(admin_user: User = Depends(require_admin)):
    return {"status": "ok", "message": "Admin services are running"}

@router.get("/kb-stats")
async def get_kb_stats(admin_user: User = Depends(require_admin)):
    # Mock KB stats for now
    return {
        "status": "ok",
        "total_documents": 5,
        "total_chunks": 42
    }

@router.get("/llm-status")
async def get_admin_llm_status(admin_user: User = Depends(require_admin)):
    from app.services.llm_client import llm_client_instance
    from app.core.config import settings

    provider_name = (settings.LLM_PROVIDER or "auto").lower().strip()
    provider = llm_client_instance.get_provider(provider_name)
    provider_health = await provider.health_check()

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

