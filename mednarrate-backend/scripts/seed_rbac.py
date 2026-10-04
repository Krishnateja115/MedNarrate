"""Repair super-admin portal access for a named administrator.

Prefer ``scripts/create_admin.py`` for new accounts; it now performs this
setup automatically. This compatibility script is intentionally email-driven
and never relies on a hard-coded administrator address.
"""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User
from app.services.admin_bootstrap import ensure_super_admin_access


async def seed() -> None:
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    if not email or "@" not in email:
        raise SystemExit("ADMIN_EMAIL is required, for example ADMIN_EMAIL=ops@example.com")

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email)
        admin_user = (await session.execute(stmt)).scalars().first()
        if admin_user is None:
            raise SystemExit("Admin user not found. Run scripts/create_admin.py first.")
        try:
            changed = await ensure_super_admin_access(session, admin_user)
        except ValueError as error:
            raise SystemExit(str(error)) from error
        await session.commit()
        status = "configured" if changed else "already configured"
        print(f"Admin portal access {status}: {email}")

if __name__ == "__main__":
    asyncio.run(seed())
