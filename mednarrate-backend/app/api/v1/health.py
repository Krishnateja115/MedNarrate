from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional
import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class HealthDataPoint(BaseModel):
    timestamp: datetime.datetime
    value: float
    unit: str

class SyncHealthDataRequest(BaseModel):
    source: str  # e.g., "apple_health", "google_fit"
    heart_rate: Optional[List[HealthDataPoint]] = None
    steps: Optional[List[HealthDataPoint]] = None
    sleep_hours: Optional[float] = None

@router.post("/sync", status_code=200)
async def sync_health_data(
    req: SyncHealthDataRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stub endpoint to receive health data from wearables.
    Currently logs the data; future implementations will store this in a dedicated table.
    """
    logger.info(f"Received health sync from {req.source} for user {current_user.id}")
    
    # In a full implementation, this would insert rows into a `health_metrics` table
    total_metrics = 0
    if req.heart_rate:
        total_metrics += len(req.heart_rate)
    if req.steps:
        total_metrics += len(req.steps)
        
    return {
        "status": "success", 
        "message": f"Synced {total_metrics} data points from {req.source}",
        "sleep_hours_recorded": req.sleep_hours is not None
    }
