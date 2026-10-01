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
    enrollment_token = setup_data["enrollment_token"]

    # 4. Verify MFA setup
    totp = pyotp.TOTP(secret)
    code = totp.now()
    response = await client.post(
        "/api/v1/mfa/verify-setup",
        json={"enrollment_token": enrollment_token, "code": code},
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

    # 4. Logout (invalidates session_version if all_devices is true)
    response = await client.post("/api/v1/auth/logout?all_devices=true", headers=headers)
    assert response.status_code == 204

    # 5. Request with same access token is rejected
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
    assert "Session has been invalidated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_mfa_enablement_invalidates_pre_mfa_sessions(client: AsyncClient, db_session: AsyncSession):
    user = User(email="pre_mfa@example.com", hashed_password=hash_password("SuperSecret1!"), full_name="Pre MFA Admin", role=UserRole.admin, is_active=True)
    db_session.add(user)
    await db_session.commit()

    # Login and get pre-MFA access token
    res = await client.post("/api/v1/auth/login", data={"username": "pre_mfa@example.com", "password": "SuperSecret1!"})
    assert res.status_code == 200
    pre_mfa_access = res.json()["access_token"]

    # Setup MFA
    headers = {"Authorization": f"Bearer {pre_mfa_access}"}
    setup_res = await client.post("/api/v1/mfa/setup", headers=headers)
    assert setup_res.status_code == 200
    setup_data = setup_res.json()

    enrollment_token = setup_data["enrollment_token"]
    secret = setup_data["secret"]
    code = pyotp.TOTP(secret).now()

    verify_res = await client.post("/api/v1/mfa/verify-setup", json={"enrollment_token": enrollment_token, "code": code}, headers=headers)
    assert verify_res.status_code == 200

    # Try to use pre-MFA token again, should be invalid due to session_version increment
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 401

@pytest.mark.asyncio
async def test_totp_replay_is_rejected(client: AsyncClient, db_session: AsyncSession):
    user = User(email="totp_replay@example.com", hashed_password=hash_password("SuperSecret1!"), full_name="Replay Admin", role=UserRole.admin, is_active=True)
    import pyotp
    secret = pyotp.random_base32()
    from app.core.encryption import encrypt_value
    user.mfa_enabled = True
    user.mfa_secret = encrypt_value(secret)
    db_session.add(user)
    await db_session.commit()

    # Login to get mfa token
    res = await client.post("/api/v1/auth/login", data={"username": "totp_replay@example.com", "password": "SuperSecret1!"})
    mfa_token = res.json()["mfa_token"]

    # Verify first time
    code = pyotp.TOTP(secret).now()
    verify_res = await client.post("/api/v1/auth/mfa-verify", json={"mfa_token": mfa_token, "code": code})
    assert verify_res.status_code == 200

    # Try to verify with same code and same/new mfa challenge, it should fail
    # Need new mfa token for second attempt
    res2 = await client.post("/api/v1/auth/login", data={"username": "totp_replay@example.com", "password": "SuperSecret1!"})
    mfa_token2 = res2.json()["mfa_token"]
    verify_res2 = await client.post("/api/v1/auth/mfa-verify", json={"mfa_token": mfa_token2, "code": code})
    assert verify_res2.status_code == 400
    assert "Invalid or reused OTP" in verify_res2.json()["detail"]

@pytest.mark.asyncio
async def test_mfa_challenge_replay_is_rejected(client: AsyncClient, db_session: AsyncSession):
    user = User(email="challenge_replay@example.com", hashed_password=hash_password("SuperSecret1!"), full_name="Challenge Replay Admin", role=UserRole.admin, is_active=True)
    import pyotp
    secret = pyotp.random_base32()
    from app.core.encryption import encrypt_value
    user.mfa_enabled = True
    user.mfa_secret = encrypt_value(secret)
    db_session.add(user)
    await db_session.commit()

    # Login to get mfa token
    res = await client.post("/api/v1/auth/login", data={"username": "challenge_replay@example.com", "password": "SuperSecret1!"})
    mfa_token = res.json()["mfa_token"]

    import datetime
    code1 = pyotp.TOTP(secret).generate_otp(pyotp.TOTP(secret).timecode(datetime.datetime.now()) - 1) # use previous window code to avoid reuse logic on current window
    verify_res = await client.post("/api/v1/auth/mfa-verify", json={"mfa_token": mfa_token, "code": code1})
    assert verify_res.status_code == 200

    # Replay same challenge token with next code
    code2 = pyotp.TOTP(secret).now()
    verify_res2 = await client.post("/api/v1/auth/mfa-verify", json={"mfa_token": mfa_token, "code": code2})
    assert verify_res2.status_code == 401
    assert "MFA challenge already used" in verify_res2.json()["detail"]

@pytest.mark.asyncio
async def test_refresh_token_reuse_invalidates_access_token(client: AsyncClient, db_session: AsyncSession):
    user = User(email="refresh_reuse@example.com", hashed_password=hash_password("SuperSecret1!"), full_name="Refresh Reuse", role=UserRole.admin, is_active=True)
    db_session.add(user)
    await db_session.commit()

    res = await client.post("/api/v1/auth/login", data={"username": "refresh_reuse@example.com", "password": "SuperSecret1!"})
    access_token_1 = res.json()["access_token"]
    refresh_token = res.json()["refresh_token"]

    # Use refresh token once
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200

    # The access_token_1 should still be valid technically (if session_version wasn't bumped)
    assert (await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token_1}"})).status_code == 200

    # REUSE the refresh token (simulate theft)
    refresh_res2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res2.status_code == 401
    assert "reuse detected" in refresh_res2.json()["detail"]

    # Now, access_token_1 MUST be invalid because session_version was bumped
    assert (await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token_1}"})).status_code == 401

@pytest.mark.asyncio
async def test_super_admin_cannot_self_reset_mfa(client: AsyncClient, db_session: AsyncSession):
    from app.models.admin import AdminRole, AdminRoleAssignment
    from sqlalchemy.future import select
    
    user = User(
        email="super_self_reset@example.com",
        hashed_password=hash_password("SuperSecret1!"),
        full_name="Super Admin Self Reset",
        role=UserRole.admin,
        is_active=True
    )
    import pyotp
    secret = pyotp.random_base32()
    from app.core.encryption import encrypt_value
    user.mfa_enabled = True
    user.mfa_secret = encrypt_value(secret)
    db_session.add(user)
    await db_session.flush()

    super_admin_role = (await db_session.execute(select(AdminRole).where(AdminRole.name == "Super Admin"))).scalars().first()
    if not super_admin_role:
        super_admin_role = AdminRole(name="Super Admin", description="super")
        db_session.add(super_admin_role)
        await db_session.flush()
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=super_admin_role.id))
    await db_session.commit()

    res = await client.post("/api/v1/auth/login", data={"username": "super_self_reset@example.com", "password": "SuperSecret1!"})
    mfa_token = res.json()["mfa_token"]

    code = pyotp.TOTP(secret).now()
    verify_res = await client.post("/api/v1/auth/mfa-verify", json={"mfa_token": mfa_token, "code": code})
    access_token = verify_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    
    reset_res = await client.post(f"/api/v1/mfa/reset/{user.id}", headers=headers)
    assert reset_res.status_code == 400
    assert "cannot use emergency reset on their own account" in reset_res.json()["detail"]
