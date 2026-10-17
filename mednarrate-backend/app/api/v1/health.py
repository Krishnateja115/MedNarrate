import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


MAX_POINTS_PER_SYNC = 2000


class HealthDataPoint(BaseModel):
    timestamp: datetime.datetime
    value: float = Field(..., ge=0, le=1_000_000)
    unit: str = Field(..., max_length=32)


class SyncHealthDataRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=64)  # "apple_health", "google_fit"
    heart_rate: Optional[List[HealthDataPoint]] = Field(None, max_length=MAX_POINTS_PER_SYNC)
    steps: Optional[List[HealthDataPoint]] = Field(None, max_length=MAX_POINTS_PER_SYNC)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)


@router.post("/sync", status_code=200)
async def sync_health_data(
    req: SyncHealthDataRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate-and-acknowledge endpoint for wearable data.

    NOTE: wearable metrics are NOT persisted yet (no health_metrics table), and
    the mobile app does not call this endpoint. The response says so
    explicitly (``persisted: false``) instead of implying data was stored.
    """
    logger.info(f"Received health sync from {req.source} for user {current_user.id}")

    # In a full implementation, this would insert rows into a `health_metrics` table
    total_metrics = 0
    if req.heart_rate:
        total_metrics += len(req.heart_rate)
    if req.steps:
        total_metrics += len(req.steps)

    return {
        "status": "accepted",
        "persisted": False,
        "message": f"Validated {total_metrics} data points from {req.source}; storage is not enabled yet",
        "sleep_hours_recorded": req.sleep_hours is not None,
    }
