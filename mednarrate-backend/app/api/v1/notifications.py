from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.push_token import PushToken
from app.models.medication_schedule import MedicationSchedule
from app.schemas.notification import RegisterTokenRequest, UnregisterTokenRequest, GenericResponse, MedicationScheduleOut
from typing import List

router = APIRouter()

@router.post("/register-token", response_model=GenericResponse)
async def register_token(
    req: RegisterTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Upsert the token
    stmt = select(PushToken).where(
        PushToken.user_id == current_user.id,
        PushToken.device_token == req.token
    )
    result = await db.execute(stmt)
    existing_token = result.scalars().first()
    
    if existing_token:
        existing_token.platform = req.platform
    else:
        new_token = PushToken(
            user_id=current_user.id,
            device_token=req.token,
            platform=req.platform
        )
        db.add(new_token)
        
    await db.commit()
    return GenericResponse(success=True, message="Device registered")

@router.delete("/unregister-token", response_model=GenericResponse)
async def unregister_token(
    req: UnregisterTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PushToken).where(
        PushToken.user_id == current_user.id,
        PushToken.device_token == req.token
    )
    result = await db.execute(stmt)
    existing_token = result.scalars().first()
    
    if existing_token:
        await db.delete(existing_token)
        await db.commit()
        return GenericResponse(success=True, message="Device unregistered")
        
    return GenericResponse(success=True, message="Token not found")

@router.get("/medication-schedules", response_model=List[MedicationScheduleOut])
async def get_medication_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).where(MedicationSchedule.user_id == current_user.id)
    result = await db.execute(stmt)
    schedules = result.scalars().all()
    return schedules

@router.patch("/medication-schedules/{schedule_id}/toggle", response_model=GenericResponse)
async def toggle_medication_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).where(
        MedicationSchedule.id == schedule_id,
        MedicationSchedule.user_id == current_user.id
    )
    result = await db.execute(stmt)
    schedule = result.scalars().first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    schedule.is_active = not schedule.is_active
    await db.commit()
    
    status = "activated" if schedule.is_active else "deactivated"
    return GenericResponse(success=True, message=f"Schedule {status}")

from app.services.notification_scheduler import scheduler

@router.get("/health")
async def check_scheduler_health():
    return {
        "scheduler_running": scheduler.running,
        "jobs_count": len(scheduler.get_jobs()) if scheduler.running else 0
    }
