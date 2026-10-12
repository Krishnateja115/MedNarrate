"""Exercise a running local API over HTTP using one disposable synthetic account."""

from __future__ import annotations

import argparse
import time
import uuid
from urllib.parse import urlparse

import httpx


def expect_status(response: httpx.Response, expected: int, step: str) -> None:
    if response.status_code != expected:
        raise RuntimeError(f"{step} returned HTTP {response.status_code}; expected {expected}")


def wait_for_api(client: httpx.Client, require_migrations: bool) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        try:
            response = client.get("/health")
            if response.status_code == 200:
                health = response.json()
                if health.get("service") == "mednarrate" and health.get("db") == "up":
                    if require_migrations and health.get("schema_revision") != health.get("schema_expected"):
                        raise RuntimeError("API is running with the wrong database migration revision")
                    return
        except httpx.ConnectError:
            pass
        time.sleep(1)
    raise RuntimeError("API did not become healthy within 45 seconds")


def run_smoke(base_url: str, require_migrations: bool) -> None:
    parsed = urlparse(base_url)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Smoke tests create an account and must target a local disposable API")

    email = f"smoke-{uuid.uuid4().hex}@example.com"
    password = "SyntheticSmokePassword1!"
    token: str | None = None
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=15) as client:
        wait_for_api(client, require_migrations)
        expect_status(client.get("/api/v1/users/me"), 401, "Anonymous profile access")
        expect_status(
            client.post(
                "/api/v1/auth/signup",
                json={"email": email, "password": password, "full_name": "Synthetic Smoke User"},
            ),
            201,
            "Signup",
        )
        try:
            login = client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": password},
            )
            expect_status(login, 200, "Login")
            token = login.json().get("access_token")
            if not token:
                raise RuntimeError("Login did not return an access token")
            headers = {"Authorization": f"Bearer {token}"}
            profile = client.get("/api/v1/users/me", headers=headers)
            expect_status(profile, 200, "Authenticated profile")
            if profile.json().get("email") != email:
                raise RuntimeError("Authenticated profile belongs to another user")
            reports = client.get("/api/v1/reports", headers=headers)
            expect_status(reports, 200, "Report list")
            if reports.json() != []:
                raise RuntimeError("New synthetic account can see existing reports")
            admin = client.get("/api/v1/admin/me", headers=headers)
            expect_status(admin, 403, "Patient admin access")
        finally:
            if token:
                deletion = client.request(
                    "DELETE",
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"password": password},
                )
                expect_status(deletion, 204, "Synthetic account cleanup")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--require-migrations", action="store_true")
    args = parser.parse_args()
    run_smoke(args.base_url, args.require_migrations)
    print("HTTP smoke passed: health, auth, isolation, reports, admin denial, cleanup")


if __name__ == "__main__":
    main()
