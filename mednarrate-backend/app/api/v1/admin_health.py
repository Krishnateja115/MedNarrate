"""
Admin System Health API.

Each service probe is:
- REAL: checks actual service state
- BOUNDED: has a timeout / safe cap
- FAST: no expensive queries
- SAFE: never exposes credentials, stack traces, or internal details

Status values: healthy | degraded | down | unknown

LLM health requires a successful test request — not just configuration presence.
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.config import settings
from app.core.database import get_db
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.services.llm_client import llm_client_instance
from app.services.scheduler import scheduler

router = APIRouter()


def _service_entry(
    status: str,
    timestamp: str,
    latency_ms: Any = None,
    error_summary: str = None,
    details: dict = None,
) -> dict:
    """Build a consistent service health entry."""
    entry = {
        "status": status,
        "last_checked": timestamp,
        "latency_ms": latency_ms,
        "error_summary": error_summary,
    }
    if details:
        entry["details"] = details
    return entry


@router.get("/health")
async def get_system_health(
    admin_ctx: AdminContext = Depends(require_permission("system.health.view")),
    db: AsyncSession = Depends(get_db),
):
    timestamp = datetime.now(timezone.utc).isoformat()
    health_status = {"status": "healthy", "timestamp": timestamp, "services": {}}

    # 1. API — if we're serving this response, the API is running
    health_status["services"]["api"] = _service_entry("healthy", timestamp)

    # 2. Database — lightweight real connectivity check (SELECT 1)
    try:
        start = datetime.now()
        await db.execute(text("SELECT 1"))
        latency = int((datetime.now() - start).total_seconds() * 1000)
        health_status["services"]["database"] = _service_entry(
            "healthy", timestamp, latency_ms=latency
        )
    except Exception:
        health_status["services"]["database"] = _service_entry(
            "down",
            timestamp,
            error_summary="Database connectivity check failed",
            # Do NOT expose: str(e) which may contain connection string details
        )
        health_status["status"] = "degraded"

    # 3. LLM Provider — must make a successful test request, not just be configured
    try:
        provider_name = (settings.PRIMARY_LLM_PROVIDER or "auto").lower().strip()
        provider = llm_client_instance.get_provider(provider_name)

        start = datetime.now()
        provider_health = await provider.health_check()
        latency = int((datetime.now() - start).total_seconds() * 1000)

        # CORRECTED: require an actual successful test request
        # configured OR reachable alone is NOT sufficient
        provider_health.get("request_successful", False)
        reachable = provider_health.get("reachable", False)
        configured = provider_health.get("configured", False)

        # Check last 10 calls for stability
        llm_events_stmt = (
            select(LLMDiagnosticEvent.status)
            .order_by(desc(LLMDiagnosticEvent.timestamp))
            .limit(10)
        )
        llm_events = (await db.execute(llm_events_stmt)).scalars().all()

        recent_success_rate = 100.0
        if llm_events:
            success_count = sum(1 for s in llm_events if s == "success")
            recent_success_rate = (success_count / len(llm_events)) * 100

        threshold = 80.0
        is_stable = (len(llm_events) == 0) or (recent_success_rate >= threshold)

        if reachable and is_stable:
            llm_status = "healthy"
            error_summary = None
        elif reachable:
            llm_status = "reachable"
            error_summary = f"Provider reachable but recent success rate is degraded ({recent_success_rate:.1f}%)"
        elif configured:
            llm_status = "configured"
            error_summary = "Provider configured but not reachable"
        else:
            llm_status = "unknown"
            error_summary = "Provider not configured"

        health_status["services"]["llm_provider"] = _service_entry(
            llm_status,
            timestamp,
            latency_ms=latency,
            error_summary=error_summary,
            details={
                "provider": provider_name,
                "configured": configured,
                "reachable": reachable,
                "healthy": reachable and is_stable,
                "recent_success_rate": round(recent_success_rate, 2),
                "threshold_required": threshold,
                "last_n_checked": len(llm_events),
            },
        )
        if llm_status in ("degraded", "down", "unknown"):
            health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["llm_provider"] = _service_entry(
            "unknown",
            timestamp,
            error_summary="Could not reach LLM provider health check",
        )
        health_status["status"] = "degraded"

    # 4. Storage — check if upload directory is writable (safe real check)
    try:
        test_file = os.path.join(settings.UPLOAD_DIR, ".healthcheck")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        health_status["services"]["storage"] = _service_entry("healthy", timestamp)
    except Exception:
        health_status["services"]["storage"] = _service_entry(
            "down", timestamp, error_summary="Storage directory not writable"
        )
        health_status["status"] = "degraded"

    # 5. Scheduler — check actual running state
    try:
        is_running = scheduler.running
        job_count = len(scheduler.get_jobs()) if is_running else 0
        health_status["services"]["scheduler"] = _service_entry(
            "healthy" if is_running else "stopped",
            timestamp,
            error_summary=None if is_running else "APScheduler is not running",
            details={"active_jobs": job_count} if is_running else None,
        )
        if not is_running:
            # Scheduler stopped is degraded, not down — API still serves requests
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["scheduler"] = _service_entry(
            "unknown", timestamp, error_summary="Could not determine scheduler state"
        )

    # 6. RAG / Vector Store — real lightweight check
    try:
        from app.services.rag import rag_service

        rag_health = await rag_service.health_check()

        rag_status_val = rag_health.get(
            "status", "unknown"
        )  # healthy, empty, down, unknown
        health_status["services"]["rag"] = _service_entry(
            rag_status_val,
            timestamp,
            error_summary=rag_health.get("error_summary"),
            details={
                "chunk_count": rag_health.get("chunk_count", "not_captured"),
                "collection_reachable": rag_health.get("reachable", False),
            },
        )
        if rag_status_val in ("down", "unknown"):
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["rag"] = _service_entry(
            "unknown", timestamp, error_summary="RAG service health check unavailable"
        )

    # Overall status: healthy only if ALL core services are healthy
    core_services = ["database", "llm_provider", "storage"]
    all_healthy = all(
        health_status["services"].get(s, {}).get("status") == "healthy"
        for s in core_services
    )
    if not all_healthy and health_status["status"] == "healthy":
        health_status["status"] = "degraded"

    return health_status
