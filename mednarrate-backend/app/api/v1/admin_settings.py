import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.models.system_setting import MaintenanceMode, SystemSetting
from app.services.audit import log_admin_action

router = APIRouter()


class SettingItemUpdate(BaseModel):
    key: str
    value: str
    category: str = "general"
    is_sensitive: bool = False
    description: Optional[str] = None


class MaintenanceModeToggle(BaseModel):
    is_enabled: bool
    scope: str = Field(
        default="all", example="report_analysis"
    )  # all, report_analysis, chat, translation, notifications
    reason: Optional[str] = Field(None, example="Scheduled database maintenance")
    message: Optional[str] = Field(
        None,
        example="MedNarrate report processing is undergoing scheduled maintenance. Please try again shortly.",
    )


@router.get("/settings")
async def get_system_settings(
    request: Request,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("settings:read")),
):
    query = select(SystemSetting)
    if category:
        query = query.where(SystemSetting.category == category)

    res = await db.execute(query)
    settings_list = res.scalars().all()

    items = []
    for s in settings_list:
        display_val = "********" if s.is_sensitive else s.value
        items.append(
            {
                "id": str(s.id),
                "key": s.key,
                "value": display_val,
                "category": s.category,
                "is_sensitive": s.is_sensitive,
                "description": s.description,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
        )

    return {"settings": items}


@router.put("/settings")
async def update_system_setting(
    payload: SettingItemUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("settings:manage")),
):
    res = await db.execute(
        select(SystemSetting).where(SystemSetting.key == payload.key)
    )
    setting = res.scalar_one_or_none()

    if not setting:
        setting = SystemSetting(
            id=uuid.uuid4(),
            key=payload.key,
            value=payload.value,
            category=payload.category,
            is_sensitive=payload.is_sensitive,
            description=payload.description,
            updated_by_id=admin_ctx.user_id,
        )
        db.add(setting)
    else:
        setting.value = payload.value
        setting.category = payload.category
        setting.is_sensitive = payload.is_sensitive
        if payload.description:
            setting.description = payload.description
        setting.updated_by_id = admin_ctx.user_id

    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="setting_update",
        resource_type="system_setting",
        resource_id=payload.key,
        permission_used="settings:manage",
        result="success",
        reason=f"Updated setting '{payload.key}'",
        request=request,
        metadata={
            "key": payload.key,
            "category": payload.category,
            "is_sensitive": payload.is_sensitive,
        },
    )

    return {"message": f"Setting '{payload.key}' updated successfully"}


@router.get("/maintenance")
async def get_maintenance_mode(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(MaintenanceMode).order_by(desc(MaintenanceMode.enabled_at)).limit(1)
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()

    if not m:
        return {
            "is_enabled": False,
            "scope": "all",
            "reason": None,
            "message": None,
            "enabled_at": None,
        }

    return {
        "id": str(m.id),
        "is_enabled": m.is_enabled,
        "scope": m.scope,
        "reason": m.reason,
        "message": m.message,
        "enabled_at": m.enabled_at.isoformat() if m.enabled_at else None,
    }


@router.post("/maintenance")
async def set_maintenance_mode(
    payload: MaintenanceModeToggle,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("maintenance:manage")),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    m = MaintenanceMode(
        id=uuid.uuid4(),
        is_enabled=payload.is_enabled,
        scope=payload.scope,
        reason=payload.reason,
        message=payload.message,
        enabled_by_id=admin_ctx.user_id,
        enabled_at=now,
    )
    db.add(m)
    await db.commit()

    action_name = (
        "maintenance_mode_enable" if payload.is_enabled else "maintenance_mode_disable"
    )
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action=action_name,
        resource_type="maintenance_mode",
        resource_id=str(m.id),
        permission_used="maintenance:manage",
        result="success",
        reason=f"Maintenance mode set to {payload.is_enabled} (scope: {payload.scope})",
        request=request,
        metadata={
            "is_enabled": payload.is_enabled,
            "scope": payload.scope,
            "message": payload.message,
        },
    )

    return {
        "message": f"Maintenance mode {'enabled' if payload.is_enabled else 'disabled'} successfully",
        "maintenance": {
            "is_enabled": m.is_enabled,
            "scope": m.scope,
            "message": m.message,
            "enabled_at": m.enabled_at.isoformat(),
        },
    }
