"""
tests/test_token_lifecycle.py

Tests for token lifecycle (expired/invalid tokens) and upload unhappy paths.
Confirms that specific, actionable error details reach the client instead of generic messages.
"""
import io
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
import jwt

from app.main import app
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, create_access_token, create_refresh_token, hash_token
from app.models.user import User
from app.models.refresh_token import RefreshToken


# ─────────────────────────── Helpers ────────────────────────────────────────

def make_expired_access_token(user_id: str) -> str:
    """Returns a JWT that expired 5 minutes ago."""
    expire = datetime.now(timezone.utc) - timedelta(minutes=5)
    payload = {"exp": expire, "sub": str(user_id)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def make_invalid_token() -> str:
    """Returns a JWT signed with the wrong secret."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {"exp": expire, "sub": str(uuid.uuid4())}
    return jwt.encode(payload, "WRONG_SECRET_DO_NOT_USE", algorithm=settings.JWT_ALGORITHM)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def test_user_and_token():
    """Creates a real user in the DB and returns (user_id, valid_access_token, valid_refresh_token)."""
    async with AsyncSessionLocal() as db:
        email = f"lifecycle_{uuid.uuid4().hex[:8]}@test.dev"
        user = User(
            email=email,
            hashed_password=hash_password("Test@1234"),
            full_name="Lifecycle Test User",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        access_token = create_access_token(subject=str(user.id))
        refresh_str = create_refresh_token()
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_str),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(rt)
        await db.commit()

        yield str(user.id), access_token, refresh_str


# ─────────────────────────── Token Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_expired_access_token_returns_specific_detail(client, test_user_and_token):
    """An expired JWT must return HTTP 401 with detail='Token has expired', not a generic message."""
    user_id, _, _ = test_user_and_token
    token = make_expired_access_token(user_id)

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token has expired", (
        f"Expected 'Token has expired', got: {resp.json()['detail']}"
    )


@pytest.mark.asyncio
async def test_invalid_token_returns_specific_detail(client):
    """A JWT signed with the wrong secret must return HTTP 401 with detail='Invalid token'."""
    token = make_invalid_token()

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token", (
        f"Expected 'Invalid token', got: {resp.json()['detail']}"
    )


@pytest.mark.asyncio
async def test_malformed_token_returns_401(client):
    """A completely garbled token string must return HTTP 401 (not 500)."""
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not.a.real.jwt.token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_expired_refresh_token_returns_401(client, test_user_and_token):
    """A consumed refresh token must return HTTP 401 on second use."""
    _, _, refresh_str = test_user_and_token

    # Consume the refresh token once
    r1 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_str})
    assert r1.status_code == 200

    # Second use should fail
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_str})
    assert resp.status_code == 401
    detail = resp.json().get("detail", "").lower()
    assert "refresh" in detail or "expired" in detail or "invalid" in detail or "reuse" in detail, (
        f"Expected specific refresh token error, got: {resp.json().get('detail')}"
    )


# ─────────────────────────── Upload Unhappy Paths ───────────────────────────

@pytest.mark.asyncio
async def test_oversized_file_upload_returns_422(client, test_user_and_token):
    """A file larger than MAX_UPLOAD_MB must return HTTP 422 with a clear size error."""
    _, access_token, _ = test_user_and_token
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    oversized_bytes = b"%PDF-" + b"A" * (max_bytes + 1024)

    resp = await client.post(
        "/api/v1/reports/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("big.pdf", io.BytesIO(oversized_bytes), "application/pdf")},
        data={"title": "Oversized", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert resp.status_code == 422
    detail = resp.json().get("detail", "").lower()
    assert "too large" in detail or "max size" in detail, (
        f"Expected size error message, got: {resp.json().get('detail')}"
    )


@pytest.mark.asyncio
async def test_corrupt_pdf_upload_returns_422(client, test_user_and_token):
    """A file with .pdf extension but invalid magic bytes must return HTTP 422."""
    _, access_token, _ = test_user_and_token
    fake_pdf = b"This is not a real PDF file at all"

    resp = await client.post(
        "/api/v1/reports/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("report.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        data={"title": "Corrupt", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert resp.status_code == 422
    assert "invalid" in resp.json().get("detail", "").lower(), (
        f"Expected invalid file error, got: {resp.json().get('detail')}"
    )


@pytest.mark.asyncio
async def test_unsupported_file_type_returns_422(client, test_user_and_token):
    """A file with an unsupported extension must return HTTP 422."""
    _, access_token, _ = test_user_and_token

    resp = await client.post(
        "/api/v1/reports/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        data={"title": "Exe file", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert resp.status_code == 422
    detail = resp.json().get("detail", "").lower()
    assert "unsupported" in detail or "extension" in detail, (
        f"Expected unsupported extension error, got: {resp.json().get('detail')}"
    )


@pytest.mark.asyncio
async def test_empty_file_upload_returns_422(client, test_user_and_token):
    """An empty (zero-byte) file must return HTTP 422."""
    _, access_token, _ = test_user_and_token

    resp = await client.post(
        "/api/v1/reports/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        data={"title": "Empty", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert resp.status_code == 422
    detail = resp.json().get("detail", "").lower()
    assert "empty" in detail or "payload" in detail, (
        f"Expected empty file error, got: {resp.json().get('detail')}"
    )
