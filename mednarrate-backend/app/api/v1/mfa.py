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
    enrollment_token: str
    provisioning_uri: str
    secret: str

class MFAVerifySetupRequest(BaseModel):
    code: str
    enrollment_token: str

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

    from app.core.security import create_mfa_enrollment_token
    enrollment_token = create_mfa_enrollment_token(user_id=str(current_user.id), secret=totp_secret)

    return MFASetupResponse(secret=totp_secret, provisioning_uri=provisioning_uri, enrollment_token=enrollment_token)

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

    from app.core.security import decode_mfa_enrollment_token
    import uuid

    # Verify the enrollment token to extract the true generated secret
    token_payload = decode_mfa_enrollment_token(payload.enrollment_token)
    token_sub = token_payload.get("sub")
    if token_sub != str(current_user.id):
        raise HTTPException(status_code=403, detail="Enrollment token belongs to a different user")

    true_secret = token_payload.get("secret")

    totp = pyotp.TOTP(true_secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Generate recovery codes
    raw_codes = [secrets.token_urlsafe(8) for _ in range(8)]
    hashed_codes = ",".join([hashlib.sha256(c.encode()).hexdigest() for c in raw_codes])

    # Save to DB
    from app.core.encryption import encrypt_value
    current_user.mfa_secret = encrypt_value(true_secret)
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

class MFADisableRequest(BaseModel):
    password: str
    code: str

@router.post("/disable")
@limiter.limit("5/minute")
async def disable_mfa(
    request: Request,
    payload: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.core.security import verify_password
    from app.core.encryption import decrypt_value

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="MFA disable is restricted to admins")
    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled")

    # Re-authenticate with password
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    # Verify TOTP
    secret = decrypt_value(current_user.mfa_secret)
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Disable MFA and clear secrets
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_recovery_codes = None

    # Invalidate existing sessions
    current_user.session_version += 1

    await log_admin_action(
        db=db,
        action="MFA_DISABLED",
        actor_admin_id=current_user.id,
        resource_type="User",
        resource_id=str(current_user.id),
        request=request
    )
class MFARegenerateRequest(BaseModel):
    password: str
    code: str

@router.post("/regenerate-recovery-codes", response_model=MFARecoveryCodesResponse)
@limiter.limit("5/minute")
async def regenerate_recovery_codes(
    request: Request,
    payload: MFARegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.core.security import verify_password
    from app.core.encryption import decrypt_value

    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled")

    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    secret = decrypt_value(current_user.mfa_secret)
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    raw_codes = [secrets.token_urlsafe(8) for _ in range(8)]
    hashed_codes = ",".join([hashlib.sha256(c.encode()).hexdigest() for c in raw_codes])

    current_user.mfa_recovery_codes = hashed_codes
    db.add(current_user)

    await log_admin_action(
        db=db,
        action="MFA_RECOVERY_CODES_REGENERATED",
        actor_admin_id=current_user.id,
        resource_type="User",
        resource_id=str(current_user.id),
        request=request
    )
    await db.commit()
    return MFARecoveryCodesResponse(recovery_codes=raw_codes)

@router.post("/reset/{target_user_id}")
@limiter.limit("5/minute")
async def super_admin_reset_mfa(
    target_user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.core.admin_auth import get_admin_context
    import uuid

    admin_ctx = await get_admin_context(current_user, db)
    if not admin_ctx.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super-admins can perform MFA reset")

    try:
        target_uuid = uuid.UUID(target_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    stmt = select(User).where(User.id == target_uuid)
    result = await db.execute(stmt)
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    if not target_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled for this user")

    target_user.mfa_enabled = False
    target_user.mfa_secret = None
    target_user.mfa_recovery_codes = None
    target_user.session_version += 1

    db.add(target_user)

    await log_admin_action(
        db=db,
        action="MFA_ADMIN_RESET",
        actor_admin_id=current_user.id,
        resource_type="User",
        resource_id=str(target_user.id),
        request=request
    )

    await db.commit()
    return {"message": "User MFA has been securely reset"}
