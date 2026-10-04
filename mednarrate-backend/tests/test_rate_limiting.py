"""Rate limiting is enabled explicitly here (it is off for the general suite)."""
import pytest

from app.core.rate_limit import limiter, SENSITIVE_LIMIT, REFRESH_LIMIT
from app.main import app


LIMIT = int(SENSITIVE_LIMIT.split("/")[0])


@pytest.fixture(autouse=True)
def enable_limiter():
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.reset()
    limiter.enabled = False


def test_single_centralized_limiter():
    assert app.state.limiter is limiter
    import app.api.v1.auth as a, app.api.v1.mfa as m, app.api.v1.password_reset as p

    assert a.limiter is limiter and m.limiter is limiter and p.limiter is limiter


@pytest.mark.asyncio
async def test_login_abuse_returns_429(client):
    codes = []
    for _ in range(LIMIT + 3):
        r = await client.post(
            "/api/v1/auth/login", data={"username": "nobody@example.com", "password": "x"}
        )
        codes.append(r.status_code)
    assert codes[:LIMIT] == [401] * LIMIT
    assert set(codes[LIMIT:]) == {429}


@pytest.mark.asyncio
async def test_forgot_password_abuse_returns_429(client):
    codes = []
    for _ in range(LIMIT + 2):
        r = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
        codes.append(r.status_code)
    assert 429 in codes[LIMIT:]
    assert 429 not in codes[:LIMIT]


@pytest.mark.asyncio
async def test_spoofed_forwarded_for_does_not_bypass_limit(client, monkeypatch):
    """Without TRUSTED_PROXY, rotating X-Forwarded-For must not reset the counter."""
    monkeypatch.delenv("TRUSTED_PROXY", raising=False)
    codes = []
    for i in range(LIMIT + 2):
        r = await client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "x"},
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        )
        codes.append(r.status_code)
    assert 429 in codes


@pytest.mark.asyncio
async def test_refresh_endpoint_is_rate_limited(client):
    limit = int(REFRESH_LIMIT.split("/")[0])
    codes = []
    for _ in range(limit + 3):
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
        codes.append(r.status_code)
    assert 429 not in codes[:limit]
    assert set(codes[limit:]) == {429}
