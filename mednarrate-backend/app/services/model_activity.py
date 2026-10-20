"""Record safe metadata about model calls made outside the main LLM chain."""

import logging

from app.core.database import AsyncSessionLocal
from app.models.llm_telemetry import LLMDiagnosticEvent

logger = logging.getLogger(__name__)


async def record_successful_model_call(
    *,
    request_id: str,
    provider: str,
    model: str | None,
    feature: str,
    latency_ms: float,
    fallback_used: bool,
) -> None:
    """Store only operational metadata; telemetry failures cannot fail a request."""
    try:
        async with AsyncSessionLocal() as session:
            session.add(
                LLMDiagnosticEvent(
                    request_id=request_id,
                    provider=provider,
                    model_name=model,
                    feature=feature,
                    status="success",
                    latency_ms=latency_ms,
                    fallback_used=fallback_used,
                )
            )
            await session.commit()
    except Exception as exc:
        logger.warning("Could not record model activity: %s", type(exc).__name__)
