from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.models.llm_telemetry import LLMDiagnosticEvent

router = APIRouter()


@router.get("/overview")
async def get_ai_overview(
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
):
    # Total requests
    total_reqs = (
        await db.execute(select(func.count(LLMDiagnosticEvent.id)))
    ).scalar() or 0

    # Success/Failure
    success_count = (
        await db.execute(
            select(func.count(LLMDiagnosticEvent.id)).where(
                LLMDiagnosticEvent.status == "success"
            )
        )
    ).scalar() or 0
    failure_count = (
        await db.execute(
            select(func.count(LLMDiagnosticEvent.id)).where(
                LLMDiagnosticEvent.status == "error"
            )
        )
    ).scalar() or 0
    timeout_count = (
        await db.execute(
            select(func.count(LLMDiagnosticEvent.id)).where(
                LLMDiagnosticEvent.status == "timeout"
            )
        )
    ).scalar() or 0
    fallback_count = (
        await db.execute(
            select(func.count(LLMDiagnosticEvent.id)).where(
                LLMDiagnosticEvent.fallback_used is True
            )
        )
    ).scalar() or 0

    # Average Latency
    avg_latency = (
        await db.execute(select(func.avg(LLMDiagnosticEvent.latency_ms)))
    ).scalar() or 0

    # By Provider
    provider_stats = (
        await db.execute(
            select(
                LLMDiagnosticEvent.provider, func.count(LLMDiagnosticEvent.id)
            ).group_by(LLMDiagnosticEvent.provider)
        )
    ).all()

    return {
        "status": "ok",
        "overview": {
            "total_requests": total_reqs,
            "success_rate": (success_count / total_reqs * 100) if total_reqs > 0 else 0,
            "failure_rate": (failure_count / total_reqs * 100) if total_reqs > 0 else 0,
            "timeout_rate": (timeout_count / total_reqs * 100) if total_reqs > 0 else 0,
            "avg_latency_ms": round(avg_latency, 2),
            "fallback_usage": fallback_count,
            "providers": [{"provider": p, "requests": r} for p, r in provider_stats],
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
    stmt = (
        select(LLMDiagnosticEvent.error_category, func.count(LLMDiagnosticEvent.id))
        .where(LLMDiagnosticEvent.error_category is not None)
        .group_by(LLMDiagnosticEvent.error_category)
        .order_by(func.count(LLMDiagnosticEvent.id).desc())
    )

    result = await db.execute(stmt)
    categories = result.all()

    return {
        "status": "ok",
        "failures": [{"category": c, "count": count} for c, count in categories],
    }
