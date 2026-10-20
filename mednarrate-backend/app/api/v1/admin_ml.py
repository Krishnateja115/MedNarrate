"""Admin view of model performance and explainability (XAI)."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.ml import xai
from app.ml.model_report import build_report
from app.ml.xai_examples import MAX_EXPLAIN_CHARS, explain_classifier
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.services.audit import log_admin_action

logger = logging.getLogger(__name__)
router = APIRouter()

# Occlusion runs the NER model once per word, so keep the input short.
MAX_NER_CHARS = 500
MAX_NER_WORDS = 60
EXPLAIN_TIMEOUT_SECONDS = 90.0


class ExplainRequest(BaseModel):
    text: str = Field(max_length=MAX_EXPLAIN_CHARS)

    @field_validator("text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


@router.get("/model-performance")
async def admin_model_performance(
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
):
    return build_report()


@router.get("/live-activity")
async def admin_live_model_activity(
    response: Response,
    hours: int = Query(24, ge=1, le=168),
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Successful model calls in a recent window, separate from benchmark scores.

    A translation can make multiple model calls, so these are calls, not users or
    clinical accuracy measurements. Only safe telemetry metadata is returned.
    """
    response.headers["Cache-Control"] = "no-store"
    now = datetime.now(timezone.utc)
    since = now.replace(tzinfo=None) - timedelta(hours=hours)
    rows = (
        await db.execute(
            select(
                LLMDiagnosticEvent.provider,
                LLMDiagnosticEvent.model_name,
                LLMDiagnosticEvent.feature,
                func.count(LLMDiagnosticEvent.id),
                func.avg(LLMDiagnosticEvent.latency_ms),
                func.count(LLMDiagnosticEvent.latency_ms),
                func.max(LLMDiagnosticEvent.timestamp),
            )
            .where(
                LLMDiagnosticEvent.timestamp >= since,
                LLMDiagnosticEvent.status == "success",
            )
            .group_by(
                LLMDiagnosticEvent.provider,
                LLMDiagnosticEvent.model_name,
                LLMDiagnosticEvent.feature,
            )
        )
    ).all()

    by_model: dict[tuple[str, str], dict] = {}
    for provider, model, feature, count, average_ms, measured_count, last_used in rows:
        provider_name = provider or "unknown"
        model_name = model or "unknown"
        key = (provider_name, model_name)
        if key not in by_model:
            by_model[key] = {
                "provider": provider_name,
                "model": model_name,
                "location": (
                    "local" if provider_name in {"local", "ollama"}
                    else "internal" if provider_name == "fallback"
                    else "hosted"
                ),
                "successful_calls": 0,
                "avg_latency_ms": None,
                "last_used": None,
                "features": {},
                "_latency_total": 0.0,
                "_latency_count": 0,
            }
        item = by_model[key]
        item["successful_calls"] += count
        item["features"][feature or "unspecified"] = count
        if average_ms is not None:
            item["_latency_total"] += float(average_ms) * measured_count
            item["_latency_count"] += measured_count
        if last_used is not None and (
            item["last_used"] is None or last_used > item["last_used"]
        ):
            item["last_used"] = last_used

    models = []
    for item in by_model.values():
        latency_count = item.pop("_latency_count")
        latency_total = item.pop("_latency_total")
        item["avg_latency_ms"] = (
            round(latency_total / latency_count, 1) if latency_count else None
        )
        if item["last_used"] is not None:
            last_used = item["last_used"]
            item["last_used"] = last_used.replace(
                tzinfo=last_used.tzinfo or timezone.utc
            ).isoformat()
        models.append(item)
    models.sort(key=lambda item: (-item["successful_calls"], item["provider"], item["model"]))

    return {
        "generated_at": now.isoformat(),
        "window_hours": hours,
        "total_successful_calls": sum(item["successful_calls"] for item in models),
        "models": models,
    }


@router.post("/explain/report-type")
@limiter.limit("20/minute")
async def explain_report_type(
    request: Request,
    payload: ExplainRequest,
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
):
    """LIME and exact linear attribution for the report-type classifier."""
    from app.ml.medical_classifier import MedicalReportClassifier

    def run():
        return explain_classifier(payload.text, MedicalReportClassifier())

    try:
        result = await asyncio.wait_for(asyncio.to_thread(run), EXPLAIN_TIMEOUT_SECONDS)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="The classifier has not been trained on this server.")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="The explanation took too long. Try shorter text.")
    # Only the size is logged: the pasted text may contain patient details.
    await log_admin_action(
        db=db, action="XAI_EXPLAIN_REPORT_TYPE", actor_admin_id=admin_ctx.user.id,
        permission_used="ai.view", request=request, metadata={"characters": len(payload.text)},
    )
    await db.commit()
    return result


@router.post("/explain/entities")
@limiter.limit("10/minute")
async def explain_entities(
    request: Request,
    payload: ExplainRequest,
    admin_ctx: AdminContext = Depends(require_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
):
    """Occlusion saliency for the biomedical entity-recognition model."""
    text = payload.text.strip()
    if len(text) > MAX_NER_CHARS or len(text.split()) > MAX_NER_WORDS:
        raise HTTPException(
            status_code=422,
            detail=f"Use at most {MAX_NER_WORDS} words ({MAX_NER_CHARS} characters) for this explanation.",
        )

    def run():
        from app.services import model_registry

        pipe = model_registry.get_ner_pipeline()

        def predict(t: str):
            return [
                {"start": int(e["start"]), "end": int(e["end"]),
                 "entity_group": str(e["entity_group"]), "score": float(e["score"])}
                for e in pipe(t)
            ]

        return xai.occlusion_ner(predict, text)

    try:
        result = await asyncio.wait_for(asyncio.to_thread(run), EXPLAIN_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="The entity model took too long to answer.")
    except Exception as exc:  # model missing, download blocked, etc.
        logger.warning("NER explanation unavailable: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="The entity-recognition model is not available on this server.")
    await log_admin_action(
        db=db, action="XAI_EXPLAIN_ENTITIES", actor_admin_id=admin_ctx.user.id,
        permission_used="ai.view", request=request, metadata={"characters": len(text)},
    )
    await db.commit()
    return result
