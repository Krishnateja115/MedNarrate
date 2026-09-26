import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
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
from app.schemas.auth import RefreshRequest, SignupRequest, Token
from app.schemas.user import UserOut
from app.services.audit import log_admin_action

limiter = Limiter(key_func=get_remote_address, enabled="pytest" not in sys.modules)

router = APIRouter()


@router.post("/signup", response_model=UserOut, status_code=201)
@limiter.limit("5/minute")
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


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        if user and user.role == UserRole.admin:
            await log_admin_action(
                db=db,
                action="FAILED_ADMIN_LOGIN",
                actor_admin_id=user.id,
                resource_type="User",
                resource_id=str(user.id),
                result="failure",
                reason="Incorrect password",
                request=request,
            )
            await db.commit()
        raise HTTPException(status_code=401, detail="Incorrect email or password")

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

    access_token = create_access_token(subject=user.id)
    refresh_token_str = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(
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


@router.post("/refresh", response_model=Token)
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
        # Revoke all tokens for this user.
        from sqlalchemy import update

        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == db_refresh_token.user_id)
            .values(revoked=True)
        )
        await db.commit()
        raise HTTPException(
            status_code=401, detail="Token reuse detected. All sessions revoked."
        )

    expires_at = db_refresh_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Revoke the current token
    db_refresh_token.revoked = True

    access_token = create_access_token(subject=db_refresh_token.user_id)
    new_refresh_token_str = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(
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
                action="ADMIN_LOGOUT",
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

        await db.commit()


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
