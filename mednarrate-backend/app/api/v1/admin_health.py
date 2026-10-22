"""
Admin System Health API.

Each service probe is:
- REAL: checks actual service state
- BOUNDED: has a timeout / safe cap
- FAST: no expensive queries
- SAFE: never exposes credentials, stack traces, or internal details

Status values: healthy | degraded | down | unknown

LLM health uses provider reachability and recent completed request outcomes.
"""

import os
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

import redis.asyncio as redis
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


def _elapsed_ms(start: float) -> float:
    """Measure a probe with a monotonic clock, retaining sub-millisecond detail."""
    return round((perf_counter() - start) * 1000, 2)


def _service_entry(
    status: str,
    timestamp: str,
    latency_ms: float | None = None,
    error_summary: str = None,
    details: dict | None = None,
) -> dict[str, Any]:
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
) -> dict[str, Any]:
    request_start = perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    health_status = {"status": "healthy", "timestamp": timestamp, "services": {}}

    # 1. API — this response confirms the API is running; processing time is set below.
    health_status["services"]["api"] = _service_entry("healthy", timestamp)

    # 2. Database — lightweight real connectivity check (SELECT 1)
    start = perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = _service_entry(
            "healthy", timestamp, latency_ms=_elapsed_ms(start)
        )
    except Exception:
        health_status["services"]["database"] = _service_entry(
            "down",
            timestamp,
            latency_ms=_elapsed_ms(start),
            error_summary="Database connectivity check failed",
            # Do NOT expose: str(e) which may contain connection string details
        )
        health_status["status"] = "degraded"

    # 3. LLM Provider — must make a successful test request, not just be configured
    start = perf_counter()
    try:
        from app.services.llm_client import get_resolved_ai_config
        config = await get_resolved_ai_config()
        provider_name = config.get("primary_provider", "auto").lower().strip()
        provider = llm_client_instance.get_provider(provider_name)

        provider_health = await provider.health_check(config=config)
        latency = _elapsed_ms(start)

        # health_check() reports configuration, authentication and reachability only;
        # it does not send a generation request, so recent call history (below) decides
        # between Healthy and Degraded.
        reachable = provider_health.get("reachable", False)
        configured = provider_health.get("configured", False)

        # Group provider attempts by request. A failed primary followed by a
        # successful external fallback is a successful user request. Ignore
        # stale attempts and keep the internal canned fallback separate.
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        llm_events_stmt = (
            select(
                LLMDiagnosticEvent.id,
                LLMDiagnosticEvent.request_id,
                LLMDiagnosticEvent.status,
                LLMDiagnosticEvent.provider,
            )
            .where(LLMDiagnosticEvent.timestamp >= recent_cutoff)
            .order_by(desc(LLMDiagnosticEvent.timestamp))
            .limit(200)
        )
        llm_events = (await db.execute(llm_events_stmt)).all()

        outcomes: dict[str, bool] = {}
        for event_id, request_id, event_status, event_provider in llm_events:
            key = request_id or str(event_id)
            if key not in outcomes and len(outcomes) >= 10:
                continue
            outcomes[key] = outcomes.get(key, False) or (
                event_status == "success" and event_provider != "fallback"
            )

        recent_success_rate = 100.0
        if outcomes:
            recent_success_rate = sum(outcomes.values()) / len(outcomes) * 100

        threshold = 80.0
        is_stable = not outcomes or recent_success_rate >= threshold

        if reachable and is_stable:
            llm_status = "healthy"
            error_summary = None
        elif reachable:
            llm_status = "degraded"
            error_summary = f"Provider reachable but recent success rate is degraded ({recent_success_rate:.1f}%)"
        elif configured:
            llm_status = "down"
            error_summary = "Provider configured but not reachable or failing"
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
                "last_n_checked": len(outcomes),
                "recent_attempt_failures": sum(
                    event_status != "success" for _, _, event_status, _ in llm_events
                ),
            },
        )
        if llm_status in ("degraded", "down", "unknown"):
            health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["llm_provider"] = _service_entry(
            "unknown",
            timestamp,
            latency_ms=_elapsed_ms(start),
            error_summary="Could not complete LLM provider health check",
        )
        health_status["status"] = "degraded"

    # 4. Storage — check if upload directory is writable (safe real check)
    start = perf_counter()
    try:
        test_file = os.path.join(settings.UPLOAD_DIR, ".healthcheck")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        health_status["services"]["storage"] = _service_entry(
            "healthy", timestamp, latency_ms=_elapsed_ms(start)
        )
    except Exception:
        health_status["services"]["storage"] = _service_entry(
            "down", timestamp, latency_ms=_elapsed_ms(start),
            error_summary="Storage directory not writable"
        )
        health_status["status"] = "degraded"

    # 5. Medication reminders — phone-local in production; only probe APScheduler
    # when server push has explicitly been enabled.
    start = perf_counter()
    try:
        is_running = scheduler.running
        job_count = len(scheduler.get_jobs()) if is_running else 0
        enabled = settings.SERVER_MEDICATION_PUSH_ENABLED
        health_status["services"]["scheduler"] = _service_entry(
            "healthy" if is_running else ("on_device" if not enabled else "stopped"),
            timestamp,
            latency_ms=_elapsed_ms(start) if enabled else None,
            error_summary=None if is_running or not enabled else "APScheduler is not running",
            details={
                "active_jobs": job_count,
                "enabled": enabled,
                "delivery_mode": "server_push" if enabled else "phone_local",
                "device_delivery_observable": False,
            },
        )
        if enabled and not is_running:
            # Scheduler stopped is degraded, not down — API still serves requests
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["scheduler"] = _service_entry(
            "unknown", timestamp, latency_ms=_elapsed_ms(start),
            error_summary="Could not determine scheduler state"
        )

    # 6. Report worker — its Redis heartbeat expires if the worker stops polling.
    if settings.ANALYSIS_EXECUTION_MODE == "worker":
        redis_url = os.environ.get("RATE_LIMIT_STORAGE_URI")
        if redis_url and redis_url.startswith("redis://"):
            start = perf_counter()
            try:
                async with redis.from_url(
                    redis_url, socket_connect_timeout=1, socket_timeout=1
                ) as client:
                    heartbeat = await client.get("mednarrate:analysis-worker:heartbeat")
                latency = _elapsed_ms(start)
                worker_status = "healthy" if heartbeat else "down"
                worker_error = None if heartbeat else "No recent report worker heartbeat"
            except Exception:
                worker_status = "unknown"
                worker_error = "Worker heartbeat unavailable"
                latency = _elapsed_ms(start)
        else:
            worker_status, worker_error, latency = (
                "unknown", "Worker monitoring is not configured", None
            )
        if worker_status != "healthy":
            health_status["status"] = "degraded"
    else:
        worker_status, worker_error, latency = "disabled", None, None
    health_status["services"]["report_worker"] = _service_entry(
        worker_status, timestamp, latency_ms=latency,
        error_summary=worker_error,
        details={"mode": settings.ANALYSIS_EXECUTION_MODE},
    )

    # 7. RAG / Vector Store — real lightweight check
    start = perf_counter()
    try:
        from app.services.rag import rag_service

        rag_health = await rag_service.health_check()

        rag_status_val = rag_health.get(
            "status", "unknown"
        )  # healthy, empty, down, unknown
        health_status["services"]["rag"] = _service_entry(
            rag_status_val,
            timestamp,
            latency_ms=_elapsed_ms(start),
            error_summary=rag_health.get("error_summary"),
            details={
                "chunk_count": rag_health.get("chunk_count", "not_captured"),
                "collection_reachable": rag_health.get("reachable", False),
            },
        )
        if rag_status_val in ("down", "unknown", "empty", "degraded"):
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    except Exception:
        health_status["services"]["rag"] = _service_entry(
            "unknown", timestamp, latency_ms=_elapsed_ms(start),
            error_summary="RAG service health check unavailable"
        )

    # Overall status: healthy only if ALL core services are healthy
    core_services = ["database", "llm_provider", "storage"]
    all_healthy = all(
        health_status["services"].get(s, {}).get("status") == "healthy"
        for s in core_services
    )
    if not all_healthy and health_status["status"] == "healthy":
        health_status["status"] = "degraded"

    health_status["services"]["api"]["latency_ms"] = _elapsed_ms(request_start)
    health_status["services"]["api"]["details"] = {
        "probe": "health endpoint processing"
    }
    return health_status
