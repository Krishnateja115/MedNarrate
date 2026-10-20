from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.core.database import get_db
from app.models.system_setting import MaintenanceMode


async def latest_maintenance(db: AsyncSession) -> MaintenanceMode | None:
    result = await db.execute(
        select(MaintenanceMode).order_by(desc(MaintenanceMode.enabled_at)).limit(1)
    )
    return result.scalar_one_or_none()


def maintenance_error(mode: MaintenanceMode) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "error": "maintenance_mode",
            "scope": mode.scope,
            "message": mode.message or "MedNarrate is temporarily under maintenance. Please try again shortly.",
            "reason": mode.reason,
        },
        headers={"Retry-After": "3600"},
    )


async def enforce_global_maintenance(
    request: Request, db: AsyncSession = Depends(get_db)
) -> None:
    """Keep admin, sign-in, health and status available while the app is paused."""
    path = request.url.path
    exempt = ("/api/v1/admin/", "/api/v1/auth/", "/api/v1/health/", "/api/v1/maintenance/")
    if path in {"/api/v1/admin", "/api/v1/health", "/api/v1/maintenance"} or path.startswith(exempt):
        return
    mode = await latest_maintenance(db)
    if mode and mode.is_enabled and mode.scope == "all":
        raise maintenance_error(mode)

def check_maintenance(scope: str):
    async def dependency(db: AsyncSession = Depends(get_db)):
        m = await latest_maintenance(db)
        if m and m.is_enabled:
            if m.scope == "all" or m.scope == scope:
                raise maintenance_error(m)
        return m
    return dependency
