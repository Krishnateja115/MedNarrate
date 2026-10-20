"""Public maintenance state for the mobile app."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.maintenance import latest_maintenance

router = APIRouter()


@router.get("/status")
async def maintenance_status(
    response: Response, db: AsyncSession = Depends(get_db)
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    mode = await latest_maintenance(db)
    return {
        "is_enabled": bool(mode and mode.is_enabled),
        "scope": mode.scope if mode and mode.is_enabled else None,
        "message": (
            mode.message or "MedNarrate is temporarily under maintenance. Please try again shortly."
            if mode and mode.is_enabled else None
        ),
    }
