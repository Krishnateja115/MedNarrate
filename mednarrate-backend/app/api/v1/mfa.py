import sys
import secrets
import pyotp
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.services.audit import log_admin_action

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled="pytest" not in sys.modules)

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str

class MFAVerifySetupRequest(BaseModel):
    code: str
    secret: str

class MFARecoveryCodesResponse(BaseModel):
    recovery_codes: List[str]

@router.post("/setup", response_model=MFASetupResponse)
@limiter.limit("5/minute")
async def setup_mfa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="MFA setup is restricted to admins")
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled")

    # Generate a new TOTP secret (do NOT save to DB yet!)
    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name="MedNarrate")

    return MFASetupResponse(secret=totp_secret, provisioning_uri=provisioning_uri)

@router.post("/verify-setup", response_model=MFARecoveryCodesResponse)
@limiter.limit("5/minute")
async def verify_mfa_setup(
    request: Request,
    payload: MFAVerifySetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="MFA setup is restricted to admins")
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled")

    totp = pyotp.TOTP(payload.secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Generate recovery codes
    raw_codes = [secrets.token_urlsafe(8) for _ in range(8)]
    hashed_codes = ",".join([hashlib.sha256(c.encode()).hexdigest() for c in raw_codes])

    # Save to DB
    from app.core.encryption import encrypt_value
    current_user.mfa_secret = encrypt_value(payload.secret)
    current_user.mfa_recovery_codes = hashed_codes
    current_user.mfa_enabled = True

    await log_admin_action(
        db=db,
        action="MFA_ENABLED",
        actor_admin_id=current_user.id,
        resource_type="User",
        resource_id=str(current_user.id),
        request=request
    )
    await db.commit()

    # Return plain-text codes once for the user to save
    return MFARecoveryCodesResponse(recovery_codes=raw_codes)
