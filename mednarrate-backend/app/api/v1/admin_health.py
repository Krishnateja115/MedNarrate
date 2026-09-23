import os
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.config import settings
from app.core.admin_auth import AdminContext, require_permission
from app.services.llm_client import llm_client_instance
from app.services.scheduler import scheduler

router = APIRouter()

@router.get("/health")
async def get_system_health(
    admin_ctx: AdminContext = Depends(require_permission("system.health.view")),
    db: AsyncSession = Depends(get_db)
):
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }

    # 1. API (Since this code is running, API is healthy)
    health_status["services"]["api"] = {
        "status": "healthy",
        "last_checked": health_status["timestamp"],
        "latency_ms": None,
        "error_summary": None
    }

    # 2. Database
    try:
        start_time = datetime.now()
        await db.execute(text("SELECT 1"))
        latency = (datetime.now() - start_time).total_seconds() * 1000
        health_status["services"]["database"] = {
            "status": "healthy",
            "last_checked": health_status["timestamp"],
            "latency_ms": int(latency),
            "error_summary": None
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "down",
            "last_checked": health_status["timestamp"],
            "latency_ms": None,
            "error_summary": str(e)
        }
        health_status["status"] = "degraded"

    # 3. LLM Provider
    try:
        provider_name = (settings.PRIMARY_LLM_PROVIDER or "auto").lower().strip()
        provider = llm_client_instance.get_provider(provider_name)
        
        start_time = datetime.now()
        provider_health = await provider.health_check()
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        is_healthy = provider_health.get("reachable", False) or provider_health.get("configured", False)
        
        health_status["services"]["llm_provider"] = {
            "status": "healthy" if is_healthy else "down",
            "last_checked": health_status["timestamp"],
            "latency_ms": int(latency),
            "error_summary": None if is_healthy else "LLM Provider not reachable or not configured."
        }
        if not is_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["llm_provider"] = {
            "status": "down",
            "last_checked": health_status["timestamp"],
            "latency_ms": None,
            "error_summary": str(e)
        }
        health_status["status"] = "degraded"

    # 4. Storage (Check if uploads directory is writable)
    try:
        test_file = os.path.join(settings.UPLOAD_DIR, ".healthcheck")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        
        health_status["services"]["storage"] = {
            "status": "healthy",
            "last_checked": health_status["timestamp"],
            "latency_ms": None,
            "error_summary": None
        }
    except Exception as e:
        health_status["services"]["storage"] = {
            "status": "down",
            "last_checked": health_status["timestamp"],
            "latency_ms": None,
            "error_summary": str(e)
        }
        health_status["status"] = "degraded"

    # 5. Scheduler
    try:
        is_running = scheduler.running
        health_status["services"]["scheduler"] = {
            "status": "healthy" if is_running else "down",
            "last_checked": health_status["timestamp"],
            "latency_ms": None,
            "error_summary": None if is_running else "APScheduler is not running"
        }
    except Exception as e:
        health_status["services"]["scheduler"] = {
            "status": "unknown",
            "last_checked": health_status["timestamp"],
            "latency_ms": None,
            "error_summary": str(e)
        }

    return health_status
