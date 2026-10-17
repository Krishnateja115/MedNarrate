import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.medication_schedule import MedicationSchedule
from app.models.user import User

router = APIRouter()


def _check_times(v):
    """Bound the list; clock formats vary ("08:00", "8:00 PM"), so only length is enforced."""
    if v is None:
        return v
    if len(v) > 24:
        raise ValueError("At most 24 reminder times are allowed")
    cleaned = []
    for item in v:
        item = (item or "").strip()
        if not item or len(item) > 24:
            raise ValueError("Each reminder time must be 1-24 characters")
        cleaned.append(item)
    return cleaned


class ReminderCreate(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    times_of_day: List[str]
    duration_days: Optional[int] = Field(None, ge=1, le=3650)
    notes: Optional[str] = Field(None, max_length=1000)
    report_id: Optional[uuid.UUID] = None

    @field_validator("times_of_day")
    @classmethod
    def _times(cls, v):
        return _check_times(v)


class ReminderUpdate(BaseModel):
    """Allowlisted, typed PATCH body.

    Ownership (user_id), id and timestamps are intentionally absent and unknown
    keys are rejected, so a caller can never reassign a schedule to another user.
    """

    model_config = ConfigDict(extra="forbid")

    medication_name: Optional[str] = Field(None, min_length=1, max_length=200)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    times_of_day: Optional[List[str]] = None
    duration_days: Optional[int] = Field(None, ge=1, le=3650)
    notes: Optional[str] = Field(None, max_length=1000)
    report_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

    @field_validator("times_of_day")
    @classmethod
    def _times(cls, v):
        return _check_times(v)


class ReminderOut(BaseModel):
    """Response model: intentionally unconstrained so legacy rows always serialize."""

    model_config = ConfigDict(from_attributes=True)

    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    times_of_day: List[str] = []
    duration_days: Optional[int] = None
    notes: Optional[str] = None
    report_id: Optional[uuid.UUID] = None
    id: uuid.UUID
    is_active: bool
    created_at: datetime


@router.post("/", response_model=ReminderOut, status_code=201)
async def create_reminder(
    reminder: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if reminder.report_id:
        from app.middleware.ownership import verify_report_ownership

        await verify_report_ownership(str(reminder.report_id), str(current_user.id), db)
    db_reminder = MedicationSchedule(user_id=current_user.id, **reminder.model_dump())
    db.add(db_reminder)
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder


@router.get("/", response_model=List[ReminderOut])
async def get_reminders(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicationSchedule).where(
        MedicationSchedule.user_id == current_user.id
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: uuid.UUID,
    reminder: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicationSchedule).where(
        MedicationSchedule.id == reminder_id,
        MedicationSchedule.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    changes = reminder.model_dump(exclude_unset=True)
    if changes.get("report_id"):
        from app.middleware.ownership import verify_report_ownership

        await verify_report_ownership(str(changes["report_id"]), str(current_user.id), db)
    for k, v in changes.items():
        setattr(db_reminder, k, v)

    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder


@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicationSchedule).where(
        MedicationSchedule.id == reminder_id,
        MedicationSchedule.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await db.delete(db_reminder)
    await db.commit()
    return None
