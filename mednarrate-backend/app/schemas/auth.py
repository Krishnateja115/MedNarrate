import re

from pydantic import BaseModel, EmailStr, field_validator


def validate_password_policy(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(v) > 128:
        raise ValueError("Password must be at most 128 characters long")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", v):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[^a-zA-Z0-9]", v):
        raise ValueError("Password must contain at least one special character")
    return v


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_policy(v)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class MFAChallengeResponse(BaseModel):
    mfa_required: bool
    mfa_token: str
    message: str


class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str

class RefreshRequest(BaseModel):
    refresh_token: str
    device_token: str | None = None
