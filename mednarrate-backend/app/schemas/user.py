from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from app.models.user import UserRole
from datetime import date, datetime

def validate_dob_string(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    trimmed = v.strip()
    try:
        parsed_date = datetime.strptime(trimmed, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid Date of Birth format or calendar date. Must be YYYY-MM-DD (e.g., 2006-05-20).")
    
    if parsed_date > date.today():
        raise ValueError("Date of Birth cannot be in the future.")
    if parsed_date.year < 1900:
        raise ValueError("Date of Birth year must be 1900 or later.")
    return trimmed

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

def validate_blood_group_str(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    normalized = v.strip().upper()
    if normalized not in VALID_BLOOD_GROUPS:
        raise ValueError(f"Invalid blood group: '{v}'. Must be one of: A+, A-, B+, B-, AB+, AB-, O+, O-")
    return normalized

def validate_text_field_str(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    trimmed = v.strip()
    import re
    if not re.search(r'[a-zA-Z0-9]', trimmed):
        raise ValueError("Field content cannot consist solely of special characters.")
    return trimmed

import re

VALID_INDIAN_PHONE_REGEX = re.compile(r'^[6-9]\d{9}$')
DUMMY_REPEATED_PHONES = {
    '0000000000', '1111111111', '2222222222', '3333333333', '4444444444',
    '5555555555', '6666666666', '7777777777', '8888888888', '9999999999'
}

def validate_indian_phone_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    trimmed = v.strip()
    if trimmed == "" or not VALID_INDIAN_PHONE_REGEX.match(trimmed) or trimmed in DUMMY_REPEATED_PHONES:
        raise ValueError("Please enter a valid 10-digit Indian mobile number.")
    return trimmed

def validate_emergency_name_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    trimmed = v.strip()
    if trimmed == "" or not re.search(r'[a-zA-Z]', trimmed) or not re.match(r"^[a-zA-Z\s\.\'-]+$", trimmed):
        raise ValueError("Please enter a valid full name containing letters.")
    return trimmed

class MedicalProfileBase(BaseModel):
    blood_group: Optional[str] = None
    known_allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator('blood_group')
    @classmethod
    def validate_blood_group(cls, v: Optional[str]) -> Optional[str]:
        return validate_blood_group_str(v)

    @field_validator('known_allergies', 'chronic_conditions')
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return validate_text_field_str(v)

    @field_validator('emergency_contact_phone')
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_indian_phone_str(v)

    @field_validator('emergency_contact_name')
    @classmethod
    def validate_emergency_name(cls, v: Optional[str]) -> Optional[str]:
        return validate_emergency_name_str(v)

class MedicalProfileOut(MedicalProfileBase):
    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    preferred_language: str = "en"
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None

    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        return validate_dob_string(v)

class UserOut(UserBase):
    id: UUID
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserWithProfileOut(UserOut):
    medical_profile: Optional[MedicalProfileOut] = None

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    role: Optional[UserRole] = None
    medical_profile: Optional[MedicalProfileBase] = None

    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        return validate_dob_string(v)
