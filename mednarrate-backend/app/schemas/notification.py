from pydantic import BaseModel, Field
from typing import Optional

class RegisterTokenRequest(BaseModel):
    token: str = Field(..., min_length=1)
    platform: str = Field(..., pattern="^(ios|android)$")
    
class UnregisterTokenRequest(BaseModel):
    token: str = Field(..., min_length=1)
    
class GenericResponse(BaseModel):
    success: bool
    message: str

from uuid import UUID
from datetime import datetime
from typing import List

class MedicationScheduleOut(BaseModel):
    id: UUID
    report_id: UUID
    medication_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    times_of_day: List[str]
    duration_days: Optional[int]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
