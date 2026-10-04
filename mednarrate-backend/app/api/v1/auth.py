from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.security import OAuth2PasswordRequestForm
from app.core.rate_limit import limiter, SENSITIVE_LIMIT, REFRESH_LIMIT
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import RefreshRequest, SignupRequest, Token, MFAChallengeResponse, MFAVerifyRequest, MFARecoverRequest
from app.schemas.user import UserOut
from app.services.audit import log_admin_action


router = APIRouter()


@router.post("/signup", response_model=UserOut, status_code=201)
@limiter.limit(SENSITIVE_LIMIT)
async def signup(
    request: Request, signup_data: SignupRequest, db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == signup_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=409, detail="You already have an account")

    hashed_password = hash_password(signup_data.password)
    new_user = User(
        email=signup_data.email,
        hashed_password=hashed_password,
        full_name=signup_data.full_name,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


from typing import Union
@router.post("/login", response_model=Union[Token, MFAChallengeResponse])
@limiter.limit(SENSITIVE_LIMIT)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    # Prevent timing attack account enumeration
    if not user:
        # Dummy bcrypt hash with typical work factor
        verify_password(form_data.password, "$2b$12$NqO1D9TfUoVp2lX2Q9yU2uD0Z3m6E7QxO.B8G.Y3yK1V9j6U6oP8.")
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Check if locked out
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=401, detail="Account is temporarily locked due to multiple failed login attempts")
        
    if user.locked_until and user.locked_until <= now:
        user.failed_login_attempts = 0
        user.locked_until = None

    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            
        if user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="FAILED_ADMIN_LOGIN",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                result="failure",
                reason="Incorrect password or locked out",
                request=request,
            )
            
        db.add(user)
        await db.commit()
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    user.failed_login_attempts = 0
    user.locked_until = None
    db.add(user)

    if not user.is_active:
        if user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="FAILED_ADMIN_LOGIN",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                result="denied",
                reason="Admin account is suspended",
                request=request,
            )
            await db.commit()
        raise HTTPException(status_code=403, detail="Account is inactive")

    if user.mfa_enabled:
        from app.core.security import create_mfa_challenge_token
        mfa_token = create_mfa_challenge_token(str(user.id))

        # If admin needs MFA, log the challenge event
        if user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="ADMIN_LOGIN_MFA_CHALLENGE",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                request=request,
            )
            await db.commit()

        return {
            "mfa_required": True,
            "mfa_token": mfa_token,
            "message": "MFA challenge required"
        }

    access_token = create_access_token(subject=user.id, session_version=user.session_version)
    refresh_token_str = create_refresh_token()

    expires_at = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    db_refresh_token = RefreshToken(
        user_id=user.id, token_hash=hash_token(refresh_token_str), expires_at=expires_at
    )
    db.add(db_refresh_token)
    if user.role == UserRole.admin:
        await log_admin_action(
            db=db,
            action="ADMIN_LOGIN_SUCCESS",
            actor_admin_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            request=request,
        )
    await db.commit()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }

from pydantic import BaseModel
from typing import Optional

class StepUpRequest(BaseModel):
    password: str
    code: Optional[str] = None

class StepUpResponse(BaseModel):
    step_up_token: str

@router.post("/step-up", response_model=StepUpResponse)
@limiter.limit(SENSITIVE_LIMIT)
async def step_up_auth(
    request: Request,
    payload: StepUpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_password, create_step_up_token
    from app.core.encryption import decrypt_value

    if not verify_password(payload.password, current_user.hashed_password):
        if current_user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="ADMIN_STEP_UP_FAILED",
                actor_admin_id=current_user.id,
                resource_type="User",
                resource_id=str(current_user.id),
                request=request
            )
            await db.commit()
        raise HTTPException(status_code=400, detail="Invalid password")

    if current_user.role == UserRole.admin and not (current_user.mfa_enabled and current_user.mfa_secret):
        raise HTTPException(status_code=403, detail="MFA enrollment required for step-up authentication")

    if current_user.mfa_enabled and current_user.mfa_secret:
        if not payload.code:
            raise HTTPException(status_code=400, detail="MFA code required for step-up authentication")

        from app.core.security import verify_totp_and_prevent_replay

        # Lock user for MFA operation
        stmt = select(User).where(User.id == current_user.id).with_for_update()
        locked_user = (await db.execute(stmt)).scalars().first()

        secret = decrypt_value(locked_user.mfa_secret)
        if not await verify_totp_and_prevent_replay(locked_user, payload.code, secret, db):
            if current_user.role == UserRole.admin:
                await log_admin_action(
                    db=db,
                    action="ADMIN_STEP_UP_FAILED",
                    actor_admin_id=current_user.id,
                    resource_type="User",
                    resource_id=str(current_user.id),
                    request=request
                )
                await db.commit()
            raise HTTPException(status_code=400, detail="Invalid or reused OTP code")

        db.add(locked_user)
        # Flush the counter update
        await db.flush()

    step_up_token = create_step_up_token(user_id=str(current_user.id), session_version=current_user.session_version)

    if current_user.role == UserRole.admin:
        await log_admin_action(
            db=db,
            action="ADMIN_STEP_UP_SUCCESS",
            actor_admin_id=current_user.id,
            resource_type="User",
            resource_id=str(current_user.id),
            request=request
        )
    await db.commit()

    return {"step_up_token": step_up_token}


@router.post("/mfa-verify", response_model=Token)
@limiter.limit(SENSITIVE_LIMIT)
async def mfa_verify(
    request: Request,
    response: Response,
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import decode_mfa_challenge_token
    import pyotp
    from app.core.encryption import decrypt_value
    import uuid

    payload_dict = decode_mfa_challenge_token(payload.mfa_token)
    user_id_str = payload_dict.get("sub")
    jti = payload_dict.get("jti")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    stmt = select(User).where(User.id == user_uuid).with_for_update()
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not enabled for user")

    from app.core.security import consume_mfa_challenge, verify_totp_and_prevent_replay

    if not await consume_mfa_challenge(jti, user.id, db):
        raise HTTPException(status_code=401, detail="MFA challenge already used")

    secret = decrypt_value(user.mfa_secret)

    if not await verify_totp_and_prevent_replay(user, payload.code, secret, db):
        if user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="ADMIN_LOGIN_MFA_FAILED",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                request=request
            )
            await db.commit()
        raise HTTPException(status_code=400, detail="Invalid or reused OTP code")

    # Valid OTP! Issue tokens.
    db.add(user)

    access_token = create_access_token(subject=user.id, session_version=user.session_version)
    refresh_token_str = create_refresh_token()

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh_token = RefreshToken(
        user_id=user.id, token_hash=hash_token(refresh_token_str), expires_at=expires_at
    )
    db.add(db_refresh_token)

    if user.role == UserRole.admin:
        await log_admin_action(
            db=db,
            action="ADMIN_LOGIN_SUCCESS",
            actor_admin_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            request=request,
        )
    await db.commit()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/mfa-recover", response_model=Token)
@limiter.limit(SENSITIVE_LIMIT)
async def mfa_recover(
    request: Request,
    response: Response,
    payload: MFARecoverRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import decode_mfa_challenge_token
    import uuid
    import hashlib

    payload_dict = decode_mfa_challenge_token(payload.mfa_token)
    user_id_str = payload_dict.get("sub")
    jti = payload_dict.get("jti")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    stmt = select(User).where(User.id == user_uuid).with_for_update()
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    if not user.mfa_enabled or not user.mfa_recovery_codes:
        raise HTTPException(status_code=400, detail="MFA or recovery codes not enabled for user")

    from app.core.security import consume_mfa_challenge
    if not await consume_mfa_challenge(jti, user.id, db):
        raise HTTPException(status_code=401, detail="MFA challenge already used")

    # Check recovery code
    import secrets
    provided_hash = hashlib.sha256(payload.recovery_code.encode()).hexdigest()

    current_codes = user.mfa_recovery_codes.split(",")

    matched = False
    for code in current_codes:
        if secrets.compare_digest(code, provided_hash):
            current_codes.remove(code)
            matched = True
            break

    if not matched:
        if user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="ADMIN_LOGIN_MFA_RECOVERY_FAILED",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                request=request
            )
            await db.commit()
        raise HTTPException(status_code=400, detail="Invalid recovery code")

    # Valid recovery code! Remove it.
    user.mfa_recovery_codes = ",".join(current_codes)
    db.add(user)

    access_token = create_access_token(subject=user.id, session_version=user.session_version)
    refresh_token_str = create_refresh_token()

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_refresh_token = RefreshToken(
        user_id=user.id, token_hash=hash_token(refresh_token_str), expires_at=expires_at
    )
    db.add(db_refresh_token)

    if user.role == UserRole.admin:
        await log_admin_action(
            db=db,
            action="ADMIN_LOGIN_MFA_RECOVERY_SUCCESS",
            actor_admin_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            request=request,
        )
    await db.commit()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
@limiter.limit(REFRESH_LIMIT)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_req: Optional[RefreshRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    token = (
        refresh_req.refresh_token
        if (refresh_req and refresh_req.refresh_token)
        else request.cookies.get("refresh_token")
    )

    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token_hash_str = hash_token(token)
    # Use row-level locking to prevent race conditions on concurrent refresh requests
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash_str)
        .with_for_update()
    )
    result = await db.execute(stmt)
    db_refresh_token = result.scalars().first()

    if not db_refresh_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if db_refresh_token.revoked:
        # Token reuse detection: possible token theft!
        # Revoke all tokens and bump session_version for this user.
        from app.core.security import revoke_all_user_sessions

        user = await db.get(User, db_refresh_token.user_id)
        if user:
            await revoke_all_user_sessions(user, db, increment_session_version=True)
            await db.commit()

        raise HTTPException(
            status_code=401, detail="Token reuse detected. All sessions revoked."
        )

    expires_at = db_refresh_token.expires_at
    # Always compare using naive UTC times
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    if expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    refresh_user = await db.get(User, db_refresh_token.user_id)
    if not refresh_user or not refresh_user.is_active:
        db_refresh_token.revoked = True
        await db.commit()
        raise HTTPException(status_code=401, detail="Account is inactive")

    # Revoke the current token
    db_refresh_token.revoked = True

    access_token = create_access_token(subject=db_refresh_token.user_id, session_version=refresh_user.session_version)
    new_refresh_token_str = create_refresh_token()

    expires_at = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    new_db_refresh_token = RefreshToken(
        user_id=db_refresh_token.user_id,
        token_hash=hash_token(new_refresh_token_str),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(new_db_refresh_token)
    await db.commit()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_str,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    all_devices: bool = Query(False, description="If true, logs out of all devices by invalidating the global session version"),
    refresh_req: Optional[RefreshRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    token = (
        refresh_req.refresh_token
        if (refresh_req and refresh_req.refresh_token)
        else request.cookies.get("refresh_token")
    )

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    if not token:
        return

    token_hash_str = hash_token(token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash_str)
    result = await db.execute(stmt)
    db_refresh_token = result.scalars().first()

    if db_refresh_token:
        db_refresh_token.revoked = True

        user = (
            (await db.execute(select(User).where(User.id == db_refresh_token.user_id)))
            .scalars()
            .first()
        )
        if user and user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="ADMIN_LOGOUT" if not all_devices else "ADMIN_LOGOUT_ALL",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                request=request,
            )

        # If device_token is provided, unregister it
        if refresh_req and refresh_req.device_token:
            from app.models.push_token import PushToken

            pt_stmt = select(PushToken).where(
                PushToken.user_id == db_refresh_token.user_id,
                PushToken.device_token == refresh_req.device_token,
            )
            pt_result = await db.execute(pt_stmt)
            push_token_record = pt_result.scalars().first()
            if push_token_record:
                await db.delete(push_token_record)

        if user and all_devices:
            from app.core.security import revoke_all_user_sessions

            await revoke_all_user_sessions(user, db, increment_session_version=True)

        await db.commit()


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
