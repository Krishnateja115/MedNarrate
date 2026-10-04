"""Bootstrap the first administrator.

No credential is baked into this script. Provide them at run time:

    ADMIN_EMAIL=ops@example.com ADMIN_PASSWORD='<strong one-time secret>' \
        python scripts/create_admin.py

If ADMIN_PASSWORD is unset and a terminal is attached, you are prompted for it
(input hidden). The password is never printed. Rotate it after first login.
"""

import asyncio
import getpass
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.user import User, UserRole

MIN_PASSWORD_LENGTH = 14
WEAK_PASSWORDS = {"admin123", "password123", "changeme", "password", "admin"}


def _read_credentials() -> tuple[str, str]:
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    if not email and sys.stdin.isatty():
        email = input("Admin email: ").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or ""
    if not password and sys.stdin.isatty():
        password = getpass.getpass("Admin password (hidden): ")
    if not email or "@" not in email:
        raise SystemExit("ADMIN_EMAIL is required and must be a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH or password.lower() in WEAK_PASSWORDS:
        raise SystemExit(
            f"ADMIN_PASSWORD is required, at least {MIN_PASSWORD_LENGTH} characters, "
            "and must not be a well-known default."
        )
    return email, password


async def create_admin() -> None:
    email, password = _read_credentials()
    await init_db()
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(User).where(User.email == email))
        ).scalars().first()
        if existing:
            raise SystemExit(f"A user with email {email} already exists; nothing changed.")
        session.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                full_name="System Admin",
                is_active=True,
                role=UserRole.admin,
            )
        )
        await session.commit()
    print(f"Admin user created: {email} (rotate the password after first login)")


if __name__ == "__main__":
    asyncio.run(create_admin())
