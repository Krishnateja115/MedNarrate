from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, hash_token, get_current_user
)
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import SignupRequest, Token, RefreshRequest
from app.schemas.user import UserOut
from app.core.config import settings

from slowapi import Limiter
from slowapi.util import get_remote_address

import sys
limiter = Limiter(key_func=get_remote_address, enabled="pytest" not in sys.modules)

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=201)
@limiter.limit("5/minute")
async def signup(request: Request, signup_data: SignupRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == signup_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
        
    hashed_password = hash_password(signup_data.password)
    new_user = User(
        email=signup_data.email,
        hashed_password=hashed_password,
        full_name=signup_data.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(subject=user.id)
    refresh_token_str = create_refresh_token()
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_req: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    token_hash_str = hash_token(refresh_req.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash_str)
    result = await db.execute(stmt)
    db_refresh_token = result.scalars().first()
    
    if not db_refresh_token or db_refresh_token.revoked or db_refresh_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    db_refresh_token.revoked = True
    
    access_token = create_access_token(subject=db_refresh_token.user_id)
    new_refresh_token_str = create_refresh_token()
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_db_refresh_token = RefreshToken(
        user_id=db_refresh_token.user_id,
        token_hash=hash_token(new_refresh_token_str),
        expires_at=expires_at
    )
    db.add(new_db_refresh_token)
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token_str,
        "token_type": "bearer"
    }

@router.post("/logout", status_code=204)
async def logout(
    refresh_req: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    token_hash_str = hash_token(refresh_req.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash_str)
    result = await db.execute(stmt)
    db_refresh_token = result.scalars().first()
    
    if db_refresh_token:
        db_refresh_token.revoked = True
        await db.commit()

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
