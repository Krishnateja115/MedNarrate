from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import String, cast, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.models.llm_telemetry import LLMDiagnosticEvent

router = APIRouter()


def _request_key():
    """One id per user-visible request (a request can try several providers)."""
    return func.coalesce(LLMDiagnosticEvent.request_id, cast(LLMDiagnosticEvent.id, String))


@router.get("/overview")
async def get_ai_overview(
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
):
    """Request-level AI health.

    The telemetry table holds one row per *attempt*: a request that fell through three
    providers before one answered has three error rows and one success row. Counting rows
    would report a request as four and make the success rate meaningless, so every figure
    here is per request, and the provider table lists only providers that served answers.
    """
    key = _request_key()
    total_reqs = (await db.execute(select(func.count(func.distinct(key))))).scalar() or 0

    answered_keys = select(key).where(LLMDiagnosticEvent.status == "success")
    succeeded = (
        await db.execute(
            select(func.count(func.distinct(key))).where(LLMDiagnosticEvent.status == "success")
        )
    ).scalar() or 0
    timed_out = (
        await db.execute(
            select(func.count(func.distinct(key))).where(
                LLMDiagnosticEvent.status == "timeout", key.not_in(answered_keys)
            )
        )
    ).scalar() or 0
    fallback_count = (
        await db.execute(
            select(func.count(func.distinct(key))).where(
                LLMDiagnosticEvent.status == "success",
                LLMDiagnosticEvent.fallback_used.is_(True),
            )
        )
    ).scalar() or 0

    # Errors are logged with latency 0, so only answered attempts say how fast the AI is.
    avg_latency = (
        await db.execute(
            select(func.avg(LLMDiagnosticEvent.latency_ms)).where(
                LLMDiagnosticEvent.status == "success"
            )
        )
    ).scalar() or 0

    served_by = (
        await db.execute(
            select(
                LLMDiagnosticEvent.provider,
                LLMDiagnosticEvent.model_name,
                func.count(LLMDiagnosticEvent.id),
                func.avg(LLMDiagnosticEvent.latency_ms),
                func.max(LLMDiagnosticEvent.timestamp),
            )
            .where(LLMDiagnosticEvent.status == "success")
            .group_by(LLMDiagnosticEvent.provider, LLMDiagnosticEvent.model_name)
            .order_by(func.count(LLMDiagnosticEvent.id).desc())
        )
    ).all()

    unanswered = max(total_reqs - succeeded, 0)
    return {
        "status": "ok",
        "overview": {
            "total_requests": total_reqs,
            "answered_requests": succeeded,
            "success_rate": (succeeded / total_reqs * 100) if total_reqs > 0 else 0,
            "failure_rate": (unanswered / total_reqs * 100) if total_reqs > 0 else 0,
            "timeout_rate": (timed_out / total_reqs * 100) if total_reqs > 0 else 0,
            "avg_latency_ms": round(float(avg_latency), 2),
            "fallback_usage": fallback_count,
            "providers": [
                {
                    "provider": provider,
                    "model": model,
                    "requests": count,
                    "avg_latency_ms": round(float(latency or 0), 2),
                    "last_used": last_used.isoformat() if last_used else None,
                }
                for provider, model, count, latency, last_used in served_by
            ],
        },
    }


@router.get("/traces")
async def get_traces(
    search: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LLMDiagnosticEvent)
        .order_by(LLMDiagnosticEvent.timestamp.desc())
        .limit(100)
    )

    if search:
        stmt = stmt.where(
            or_(
                LLMDiagnosticEvent.request_id.ilike(f"%{search}%"),
                LLMDiagnosticEvent.feature.ilike(f"%{search}%"),
            )
        )
    if provider:
        stmt = stmt.where(LLMDiagnosticEvent.provider == provider)
    if status:
        stmt = stmt.where(LLMDiagnosticEvent.status == status)

    result = await db.execute(stmt)
    events = result.scalars().all()

    return {
        "status": "ok",
        "traces": [
            {
                "id": e.id,
                "request_id": e.request_id,
                "feature": e.feature,
                "provider": e.provider,
                "model_name": e.model_name,
                "status": e.status,
                "latency_ms": e.latency_ms,
                "fallback_used": e.fallback_used,
                "error_category": e.error_category,
                "timestamp": e.timestamp,
            }
            for e in events
        ],
    }


@router.get("/failures")
async def get_failures(
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
):
    categories = (
        await db.execute(
            select(LLMDiagnosticEvent.error_category, func.count(LLMDiagnosticEvent.id))
            .where(LLMDiagnosticEvent.error_category.is_not(None))
            .group_by(LLMDiagnosticEvent.error_category)
            .order_by(func.count(LLMDiagnosticEvent.id).desc())
        )
    ).all()

    # Failed attempts per provider: shows which provider in the chain is down or has no key,
    # without counting those attempts as failed user requests.
    by_provider = (
        await db.execute(
            select(
                LLMDiagnosticEvent.provider,
                func.count(LLMDiagnosticEvent.id),
                func.max(LLMDiagnosticEvent.timestamp),
            )
            .where(LLMDiagnosticEvent.status != "success")
            .group_by(LLMDiagnosticEvent.provider)
            .order_by(func.count(LLMDiagnosticEvent.id).desc())
        )
    ).all()

    return {
        "status": "ok",
        "failures": [{"category": c, "count": count} for c, count in categories],
        "failed_attempts_by_provider": [
            {
                "provider": provider,
                "attempts": count,
                "last_seen": last_seen.isoformat() if last_seen else None,
            }
            for provider, count, last_seen in by_provider
        ],
    }
