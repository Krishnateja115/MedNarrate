import pytest
from httpx import AsyncClient


async def test_signup_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "StrongP@ssword1",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data


async def test_signup_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_dup@example.com", "password": "StrongP@ssword1", "full_name": "Test User"},
    )
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_dup@example.com", "password": "StrongP@ssword1", "full_name": "Test User"},
    )
    assert response.status_code == 409


async def test_signup_weak_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "weak@example.com", "password": "weak", "full_name": "Test User"},
    )
    assert response.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_login@example.com", "password": "StrongP@ssword1", "full_name": "Test User"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_login@example.com", "password": "StrongP@ssword1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_login_wrong@example.com", "password": "StrongP@ssword1", "full_name": "Test User"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_login_wrong@example.com", "password": "WrongStrongP@ssword1"},
    )
    assert response.status_code == 401


async def test_refresh_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_refresh@example.com", "password": "StrongP@ssword1", "full_name": "Test User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_refresh@example.com", "password": "StrongP@ssword1"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    new_refresh_token = data["refresh_token"]
    assert new_refresh_token != refresh_token

    # Old token should be revoked
    old_refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert old_refresh_resp.status_code == 401


async def test_logout(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test_logout@example.com", "password": "StrongP@ssword1", "full_name": "Test User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test_logout@example.com", "password": "StrongP@ssword1"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}
    )
    assert logout_resp.status_code == 204

    # Token should be revoked
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 401


async def test_auth_me_requires_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_account_lockout(client: AsyncClient, db_session, bystander_user):
    test_user = bystander_user
    
    # Attempt 5 incorrect logins
    for i in range(5):
        response = await client.post("/api/v1/auth/login", data={"username": test_user.email, "password": "wrongpassword"})
        assert response.status_code == 401

    # 6th attempt should be locked out (even if password is correct)
    response = await client.post("/api/v1/auth/login", data={"username": test_user.email, "password": "StrongP@ssword1"})
    assert response.status_code == 401
    assert "locked" in response.json()["detail"]

    # Reset locked_until to past
    from datetime import datetime, timedelta, timezone
    from sqlalchemy.future import select
    from app.models.user import User
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # get user and set locked_until
    user = (await db_session.execute(select(User).where(User.email == test_user.email))).scalar_one()
    user.locked_until = now - timedelta(minutes=1)
    db_session.add(user)
    await db_session.commit()

    # Now login should succeed
    response = await client.post("/api/v1/auth/login", data={"username": test_user.email, "password": "StrongP@ssword1"})
    assert response.status_code == 200
    assert "access_token" in response.json()
