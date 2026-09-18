from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.core.security import hash_password
from slowapi import Limiter
from slowapi.util import get_remote_address
import sys
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

router = APIRouter()
limiter = Limiter(key_func=get_remote_address, enabled="pytest" not in sys.modules)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ForgotPasswordResponse(BaseModel):
    message: str


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
async def forgot_password(request: Request, req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        # Return success even if email not found (prevents enumeration)
        return ForgotPasswordResponse(
            message="If this email is registered, a reset link has been sent."
        )

    # Generate a secure random token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    db_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    db.add(db_token)
    await db.commit()

    # In production: send email with reset link containing raw_token
    # We do NOT return raw_token in the API response for security reasons.
    return ForgotPasswordResponse(
        message="If this email is registered, a reset link has been sent."
    )


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()
    
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used == False
    )
    result = await db.execute(stmt)
    db_token = result.scalars().first()

    if not db_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    # Convert naive to aware UTC if necessary, though SQLAlchemy DateTime might be naive
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if datetime.now(timezone.utc) > expires_at:
        db_token.used = True
        await db.commit()
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")

    stmt = select(User).where(User.id == db_token.user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(req.new_password)
    db_token.used = True
    await db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}
