from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.medication_schedule import MedicationSchedule
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter()

class ReminderCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    times_of_day: List[str]
    duration_days: Optional[int]
    notes: Optional[str]

class ReminderOut(ReminderCreate):
    id: uuid.UUID
    is_active: bool

@router.post("/", response_model=ReminderOut, status_code=201)
async def create_reminder(
    reminder: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    db_reminder = MedicationSchedule(
        user_id=current_user.id,
        **reminder.model_dump()
    )
    db.add(db_reminder)
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder

@router.get("/", response_model=List[ReminderOut])
async def get_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).where(MedicationSchedule.user_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: uuid.UUID,
    reminder: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).where(
        MedicationSchedule.id == reminder_id,
        MedicationSchedule.user_id == current_user.id
    )
    result = await db.execute(stmt)
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    for k, v in reminder.items():
        setattr(db_reminder, k, v)
    
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder

@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).where(
        MedicationSchedule.id == reminder_id,
        MedicationSchedule.user_id == current_user.id
    )
    result = await db.execute(stmt)
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    await db.delete(db_reminder)
    await db.commit()
    return None
