import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.feature_flag import FeatureFlag
from app.core.admin_auth import AdminContext, require_permission
from app.services.audit import log_admin_action

router = APIRouter()

class FeatureFlagCreate(BaseModel):
    name: str = Field(..., min_length=2, example="enable_ocr_v2")
    description: Optional[str] = None
    enabled: bool = False
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    target_environment: str = Field(default="all", example="production")
    target_segment: Optional[str] = None

class FeatureFlagUpdate(BaseModel):
    description: Optional[str] = None
    enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    target_environment: Optional[str] = None
    target_segment: Optional[str] = None

@router.get("/feature-flags")
async def list_feature_flags(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("feature_flags:read"))
):
    stmt = select(FeatureFlag).order_by(desc(FeatureFlag.created_at))
    res = await db.execute(stmt)
    flags = res.scalars().all()

    items = []
    for f in flags:
        items.append({
            "id": str(f.id),
            "name": f.name,
            "description": f.description,
            "enabled": f.enabled,
            "rollout_percentage": f.rollout_percentage,
            "target_environment": f.target_environment,
            "target_segment": f.target_segment,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        })

    return {"flags": items}

@router.post("/feature-flags")
async def create_feature_flag(
    payload: FeatureFlagCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("feature_flags:manage"))
):
    # Check duplicate name
    existing_res = await db.execute(select(FeatureFlag).where(FeatureFlag.name == payload.name))
    if existing_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Feature flag with name '{payload.name}' already exists")

    flag = FeatureFlag(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        enabled=payload.enabled,
        rollout_percentage=payload.rollout_percentage,
        target_environment=payload.target_environment,
        target_segment=payload.target_segment,
        updated_by_id=admin_ctx.user_id,
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="feature_flag_create",
        resource_type="feature_flag",
        resource_id=str(flag.id),
        permission_used="feature_flags:manage",
        result="success",
        reason=f"Created feature flag {flag.name}",
        request=request,
        metadata={"name": flag.name, "enabled": flag.enabled, "rollout": flag.rollout_percentage}
    )

    return {"message": "Feature flag created successfully", "flag": {"id": str(flag.id), "name": flag.name, "enabled": flag.enabled}}

@router.put("/feature-flags/{flag_id}")
async def update_feature_flag(
    flag_id: str,
    payload: FeatureFlagUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("feature_flags:manage"))
):
    try:
        f_uuid = uuid.UUID(flag_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flag ID format")

    res = await db.execute(select(FeatureFlag).where(FeatureFlag.name == flag_id) if not flag_id.count("-") == 4 else select(FeatureFlag).where(FeatureFlag.id == f_uuid))
    flag = res.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    old_enabled = flag.enabled
    changes = {}
    if payload.description is not None:
        flag.description = payload.description
        changes["description"] = payload.description
    if payload.enabled is not None:
        flag.enabled = payload.enabled
        changes["enabled"] = payload.enabled
    if payload.rollout_percentage is not None:
        flag.rollout_percentage = payload.rollout_percentage
        changes["rollout_percentage"] = payload.rollout_percentage
    if payload.target_environment is not None:
        flag.target_environment = payload.target_environment
        changes["target_environment"] = payload.target_environment
    if payload.target_segment is not None:
        flag.target_segment = payload.target_segment
        changes["target_segment"] = payload.target_segment

    flag.updated_by_id = admin_ctx.user_id
    flag.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="feature_flag_update",
        resource_type="feature_flag",
        resource_id=str(flag.id),
        permission_used="feature_flags:manage",
        result="success",
        reason=f"Updated feature flag {flag.name} (enabled={flag.enabled})",
        request=request,
        metadata={"name": flag.name, "changes": changes, "previous_enabled": old_enabled}
    )

    return {"message": "Feature flag updated successfully", "flag": {"id": str(flag.id), "name": flag.name, "enabled": flag.enabled}}

@router.delete("/feature-flags/{flag_id}")
async def delete_feature_flag(
    flag_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("feature_flags:manage"))
):
    try:
        f_uuid = uuid.UUID(flag_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flag ID format")

    res = await db.execute(select(FeatureFlag).where(FeatureFlag.id == f_uuid))
    flag = res.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag_name = flag.name
    await db.delete(flag)
    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="feature_flag_delete",
        resource_type="feature_flag",
        resource_id=flag_id,
        permission_used="feature_flags:manage",
        result="success",
        reason=f"Deleted feature flag {flag_name}",
        request=request,
        metadata={"name": flag_name}
    )

    return {"message": f"Feature flag '{flag_name}' deleted successfully"}
