import pytest
from httpx import AsyncClient
import hashlib
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.core.security import hash_password, verify_password
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient, db_session):
    # Setup user
    user = User(
        email="reset_test@example.com",
        hashed_password=hash_password("OldPassword123"),
        full_name="Reset Test",
    )
    db_session.add(user)
    await db_session.commit()

    # Request forgot password
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "reset_test@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert "If this email is registered" in data["message"]
    # Ensure raw token is not exposed
    assert "dev_token" not in data

    # Check DB for the token
    stmt = select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    result = await db_session.execute(stmt)
    db_token = result.scalars().first()
    assert db_token is not None
    assert db_token.used is False


@pytest.mark.asyncio
async def test_forgot_password_non_existent(client: AsyncClient):
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert "If this email is registered" in data["message"]


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient, db_session):
    user = User(
        email="reset_success@example.com",
        hashed_password=hash_password("OldPassword123"),
        full_name="Reset Success",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    raw_token = "my_secret_token_123"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    db_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    db_session.add(db_token)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStrongPassword123!"}
    )
    assert resp.status_code == 200

    # Verify password was changed
    stmt = select(User).where(User.id == user.id)
    result = await db_session.execute(stmt)
    updated_user = result.scalars().first()
    assert verify_password("NewStrongPassword123!", updated_user.hashed_password)

    # Verify token is used
    stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    result = await db_session.execute(stmt)
    updated_token = result.scalars().first()
    assert updated_token.used is True


@pytest.mark.asyncio
async def test_reset_password_used_token(client: AsyncClient, db_session):
    user = User(
        email="reset_used@example.com",
        hashed_password=hash_password("OldPassword123"),
        full_name="Reset Used",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    raw_token = "my_used_token_123"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    db_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=True
    )
    db_session.add(db_token)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStrongPassword123!"}
    )
    assert resp.status_code == 400
    assert "Invalid or expired reset token" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_expired_token(client: AsyncClient, db_session):
    user = User(
        email="reset_expired@example.com",
        hashed_password=hash_password("OldPassword123"),
        full_name="Reset Expired",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    raw_token = "my_expired_token_123"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    db_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    db_session.add(db_token)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStrongPassword123!"}
    )
    assert resp.status_code == 400
    assert "Reset token has expired" in resp.json()["detail"]
