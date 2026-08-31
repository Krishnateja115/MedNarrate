from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.models.user import User
from app.core.security import hash_password
import secrets
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory token store (keyed by hash → {user_id, expires_at})
# In production, use a DB table or Redis.
_reset_tokens: dict = {}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ForgotPasswordResponse(BaseModel):
    message: str
    # In dev mode only, return the token directly so it can be tested
    dev_token: str | None = None


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
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

    _reset_tokens[token_hash] = {
        "user_id": str(user.id),
        "expires_at": expires_at,
    }

    # In production: send email with reset link
    if settings.SENDGRID_API_KEY:
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            message = Mail(
                from_email=settings.SENDGRID_FROM_EMAIL,
                to_emails=req.email,
                subject="Password Reset Request",
                html_content=f"Your password reset token is: <strong>{raw_token}</strong>"
            )
            sg.send(message)
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
    else:
        logger.info(f"OTP generated for {req.email}: {raw_token}")

    # For development: return the token directly in the response if no sendgrid key
    return ForgotPasswordResponse(
        message="If this email is registered, a reset link has been sent.",
        dev_token=raw_token if not settings.SENDGRID_API_KEY else None,
    )


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()
    token_data = _reset_tokens.get(token_hash)

    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    expires_at = token_data["expires_at"]
    if datetime.now(timezone.utc) > expires_at:
        del _reset_tokens[token_hash]
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")

    stmt = select(User).where(User.id == token_data["user_id"])
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(req.new_password)
    await db.commit()

    # Invalidate the token after use
    del _reset_tokens[token_hash]

    return {"message": "Password reset successfully. You can now log in with your new password."}
