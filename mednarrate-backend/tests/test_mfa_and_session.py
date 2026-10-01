import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token
import pyotp

@pytest.mark.asyncio
async def test_mfa_enrollment_and_login_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Create admin user
    user = User(
        email="mfa_admin@example.com",
        hashed_password=hash_password("SuperSecret1!"),
        full_name="MFA Admin",
        role=UserRole.admin,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Login normally before MFA is enabled
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "mfa_admin@example.com", "password": "SuperSecret1!"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]

    # 3. Setup MFA
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.post("/api/v1/mfa/setup", headers=headers)
    assert response.status_code == 200
    setup_data = response.json()
    secret = setup_data["secret"]

    # 4. Verify MFA setup
    totp = pyotp.TOTP(secret)
    code = totp.now()
    response = await client.post(
        "/api/v1/mfa/verify-setup",
        json={"secret": secret, "code": code},
        headers=headers
    )
    assert response.status_code == 200

    # 5. Logout and login again (MFA now required)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "mfa_admin@example.com", "password": "SuperSecret1!"}
    )
    assert response.status_code == 200
    login_data = response.json()
    assert login_data.get("mfa_required") is True
    assert "mfa_token" in login_data
    mfa_token = login_data["mfa_token"]

    # 6. Verify MFA token
    code = pyotp.TOTP(secret).now()
    response = await client.post(
        "/api/v1/auth/mfa-verify",
        json={"mfa_token": mfa_token, "code": code}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_session_invalidation_on_logout(client: AsyncClient, db_session: AsyncSession):
    # 1. Create admin user
    user = User(
        email="logout_admin@example.com",
        hashed_password=hash_password("SuperSecret1!"),
        full_name="Logout Admin",
        role=UserRole.admin,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "logout_admin@example.com", "password": "SuperSecret1!"}
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]

    # 3. Request works
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200

    # 4. Logout (invalidates session_version)
    response = await client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 204

    # 5. Request with same access token is rejected
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
    assert "Session has been invalidated" in response.json()["detail"]
