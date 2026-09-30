from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.core.database import get_db
from app.models.system_setting import MaintenanceMode

def check_maintenance(scope: str):
    async def dependency(db: AsyncSession = Depends(get_db)):
        stmt = select(MaintenanceMode).order_by(desc(MaintenanceMode.enabled_at)).limit(1)
        res = await db.execute(stmt)
        m = res.scalar_one_or_none()
        if m and m.is_enabled:
            if m.scope == "all" or m.scope == scope:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "maintenance_mode",
                        "scope": m.scope,
                        "message": m.message or "Service under maintenance",
                        "reason": m.reason
                    },
                    headers={"Retry-After": "3600"}
                )
        return m
    return dependency
