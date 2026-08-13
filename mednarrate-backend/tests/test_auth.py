import pytest
from httpx import AsyncClient

async def test_signup_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "Password1", "full_name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data

async def test_signup_duplicate_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "Password1", "full_name": "Test User"}
    )
    assert response.status_code == 409

async def test_signup_weak_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "weak@example.com", "password": "weak", "full_name": "Test User"}
    )
    assert response.status_code == 422

async def test_login_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Password1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

async def test_login_wrong_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "WrongPassword1"}
    )
    assert response.status_code == 401

async def test_refresh_token(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Password1"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    new_refresh_token = data["refresh_token"]
    assert new_refresh_token != refresh_token

    # Old token should be revoked
    old_refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert old_refresh_resp.status_code == 401

async def test_logout(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Password1"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token}
    )
    assert logout_resp.status_code == 204

    # Token should be revoked
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 401

async def test_auth_me_requires_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
