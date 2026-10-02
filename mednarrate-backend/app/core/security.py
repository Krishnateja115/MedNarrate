import hashlib
import hashlib as _hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if authorization and scheme.lower() == "bearer":
            return param

        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            return cookie_token

        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/login")


def _pre_hash(password: str) -> bytes:
    """Pre-hash password with SHA256 to avoid bcrypt 72-byte truncation and quirks."""
    return _hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")


def hash_password(password: str) -> str:
    pwd_bytes = _pre_hash(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = _pre_hash(plain)
    return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))


def create_access_token(subject: str, session_version: int = 1) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"exp": expire, "sub": str(subject), "session_version": session_version, "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)

def create_mfa_challenge_token(user_id: str) -> str:
    import uuid
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {"exp": expire, "sub": str(user_id), "type": "mfa_challenge", "jti": str(uuid.uuid4())}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_mfa_challenge_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "mfa_challenge":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="MFA challenge expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid MFA token")

def create_mfa_enrollment_token(user_id: str, secret: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    to_encode = {"exp": expire, "sub": str(user_id), "type": "mfa_enrollment", "secret": secret}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_mfa_enrollment_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "mfa_enrollment":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="MFA enrollment expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid MFA enrollment token")

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def verify_totp_and_prevent_replay(user, code: str, secret: str, db: AsyncSession) -> bool:
    import pyotp
    totp = pyotp.TOTP(secret)
    # PyOTP uses valid_window to check current and nearby timesteps.
    # We want to identify EXACTLY which counter matched, to prevent replay.
    current_counter = int(datetime.now().timestamp() / totp.interval)

    # valid_window=1 means checking current, current-1, current+1
    matched_counter = None
    for offset in (0, -1, 1):
        test_counter = current_counter + offset
        if secrets.compare_digest(totp.generate_otp(test_counter), code):
            matched_counter = test_counter
            break

    if matched_counter is None:
        return False

    if user.last_totp_counter is not None and matched_counter <= user.last_totp_counter:
        # Replay detected or old code used
        return False

    # Update counter
    user.last_totp_counter = matched_counter
    db.add(user)
    return True

async def consume_mfa_challenge(jti: str, user_id, db: AsyncSession) -> bool:
    from app.models.mfa_challenge import MFAChallenge
    from sqlalchemy.exc import IntegrityError
    try:
        challenge = MFAChallenge(
            jti=jti,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            used_at=datetime.now(timezone.utc)
        )
        db.add(challenge)
        await db.flush() # Will raise IntegrityError if jti already exists (already consumed)
        return True
    except IntegrityError:
        await db.rollback()
        return False


def decode_access_token(token: str) -> dict:
    try:
        decoded_token = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if decoded_token.get("type") not in (None, "access"):
            raise HTTPException(status_code=401, detail="Invalid token type")
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_step_up_token(user_id: str, session_version: int) -> str:
    import uuid
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "type": "privileged_step_up",
        "session_version": session_version,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_step_up_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "privileged_step_up":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Step-up token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid step-up token")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    from app.models.user import User  # Local import to avoid circular dependencies

    # decode_access_token raises HTTPException with specific detail ("Token has expired",
    # "Invalid token"). Re-raise those directly so the real cause reaches the client.
    # Only fall back to a generic 401 for truly unexpected errors (e.g., DB unavailable).
    try:
        payload = decode_access_token(token)
    except HTTPException:
        raise  # Propagate specific detail ("Token has expired" / "Invalid token")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    import uuid

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_session_version = payload.get("session_version")
    if token_session_version is None or token_session_version != user.session_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been invalidated or is missing version claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def revoke_all_user_sessions(user, db: AsyncSession, increment_session_version: bool = True):
    """
    Centrally revokes all refresh tokens for a user and optionally increments session_version
    to instantly invalidate active access tokens.
    """
    from sqlalchemy import update
    from app.models.refresh_token import RefreshToken

    if increment_session_version:
        user.session_version += 1
        db.add(user)

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(revoked=True)
    )
