"""Bootstrap the first administrator.

No credential is baked into this script. Provide them at run time:

    ADMIN_EMAIL=ops@example.com ADMIN_PASSWORD='<strong one-time secret>' \
        python scripts/create_admin.py

If ADMIN_PASSWORD is unset and a terminal is attached, you are prompted for it
(input hidden). The password is never printed. Re-running the script for an
existing administrator repairs its required portal role without changing the
password.
"""

import asyncio
import getpass
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.services.admin_bootstrap import ensure_super_admin_access
from app.models.user import User, UserRole

MIN_PASSWORD_LENGTH = 14
WEAK_PASSWORDS = {"admin123", "password123", "changeme", "password", "admin"}


def _read_email() -> str:
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    if not email and sys.stdin.isatty():
        email = input("Admin email: ").strip().lower()
    if not email or "@" not in email:
        raise SystemExit("ADMIN_EMAIL is required and must be a valid email address.")
    return email


def _read_password() -> str:
    password = os.environ.get("ADMIN_PASSWORD") or ""
    if not password and sys.stdin.isatty():
        password = getpass.getpass("Admin password (hidden): ")
    if len(password) < MIN_PASSWORD_LENGTH or password.lower() in WEAK_PASSWORDS:
        raise SystemExit(
            f"ADMIN_PASSWORD is required, at least {MIN_PASSWORD_LENGTH} characters, "
            "and must not be a well-known default."
        )
    return password


def _read_credentials() -> tuple[str, str]:
    """Read credentials for creating a new account (kept testable and private)."""
    return _read_email(), _read_password()


async def create_admin() -> None:
    email = _read_email()
    await init_db()
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(User).where(User.email == email))
        ).scalars().first()
        if existing:
            try:
                changed = await ensure_super_admin_access(session, existing)
            except ValueError as error:
                raise SystemExit(str(error)) from error
            await session.commit()
            status = "repaired" if changed else "already configured"
            print(f"Admin portal access {status}: {email} (password unchanged)")
            return

        password = _read_password()
        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name="System Admin",
            is_active=True,
            role=UserRole.admin,
        )
        session.add(admin)
        await session.flush()
        await ensure_super_admin_access(session, admin)
        await session.commit()
    print(f"Admin user created and portal access configured: {email}")


if __name__ == "__main__":
    asyncio.run(create_admin())
