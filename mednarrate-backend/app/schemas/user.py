from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from app.models.user import UserRole
from datetime import date

class MedicalProfileBase(BaseModel):
    blood_group: Optional[str] = None
    known_allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class MedicalProfileOut(MedicalProfileBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    preferred_language: str = "en"
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None

class UserOut(UserBase):
    id: UUID
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

class UserWithProfileOut(UserOut):
    medical_profile: Optional[MedicalProfileOut] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    medical_profile: Optional[MedicalProfileBase] = None
