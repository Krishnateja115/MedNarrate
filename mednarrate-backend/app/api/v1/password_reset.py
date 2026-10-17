import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from app.core.rate_limit import limiter, SENSITIVE_LIMIT
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.email_service import send_password_reset_email

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.auth import validate_password_policy

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_policy(v)


class ForgotPasswordResponse(BaseModel):
    message: str


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(SENSITIVE_LIMIT)
async def forgot_password(
    request: Request,
    req: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Case-insensitive match: signup/login treat e-mail case-insensitively.
    stmt = select(User).where(func.lower(User.email) == req.email.strip().lower())
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
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    db_token = PasswordResetToken(
        user_id=user.id, token_hash=token_hash, expires_at=expires_at, used=False
    )
    db.add(db_token)
    await db.commit()

    # The raw token is delivered ONLY by e-mail (never in the API response).
    # Sent in a background task so response time does not reveal whether the
    # address is registered.
    if user.is_active:
        background_tasks.add_task(send_password_reset_email, user.email, raw_token)
    return ForgotPasswordResponse(
        message="If this email is registered, a reset link has been sent."
    )


@router.post("/reset-password")
@limiter.limit(SENSITIVE_LIMIT)
async def reset_password(
    request: Request, req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()

    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token_hash == token_hash, PasswordResetToken.used == False
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
        raise HTTPException(
            status_code=400, detail="Reset token has expired. Please request a new one."
        )

    stmt = select(User).where(User.id == db_token.user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(req.new_password)
    db_token.used = True

    # Revoke all existing sessions for this user upon password reset
    from app.core.security import revoke_all_user_sessions
    await revoke_all_user_sessions(user, db, increment_session_version=True)

    await db.commit()

    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }
