import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.admin import SensitiveAccessGrant
from app.models.user import User
from app.core.admin_auth import AdminContext, require_permission
from app.services.audit import log_admin_action

router = APIRouter()

class BreakGlassRequest(BaseModel):
    resource_type: str = Field(..., example="patient_medical_record")
    resource_id: str = Field(..., example="rep_12345")
    reason: str = Field(..., min_length=10, example="Emergency clinical review requested by attending physician")
    duration_minutes: int = Field(default=30, ge=5, le=120)

@router.post("/break-glass/request")
async def request_break_glass_access(
    req: BreakGlassRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass:request"))
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(minutes=req.duration_minutes)

    grant = SensitiveAccessGrant(
        id=uuid.uuid4(),
        admin_id=admin_ctx.user_id,
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        reason=req.reason,
        created_at=now,
        expires_at=expires_at,
        approved_by_id=admin_ctx.user_id if admin_ctx.is_super_admin else None,
        status="active"
    )

    db.add(grant)
    await db.commit()
    await db.refresh(grant)

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="break_glass_request",
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        permission_used="break_glass:request",
        result="success",
        reason=req.reason,
        request=request,
        metadata={"duration_minutes": req.duration_minutes, "expires_at": expires_at.isoformat()},
        sensitive_access_flag=True
    )

    return {
        "message": "Temporary sensitive access grant created successfully",
        "grant": {
            "id": str(grant.id),
            "admin_id": str(grant.admin_id),
            "resource_type": grant.resource_type,
            "resource_id": grant.resource_id,
            "reason": grant.reason,
            "status": grant.status,
            "created_at": grant.created_at.isoformat(),
            "expires_at": grant.expires_at.isoformat(),
        }
    }

@router.get("/break-glass/grants")
async def list_break_glass_grants(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass:read"))
):
    stmt = select(SensitiveAccessGrant).order_by(desc(SensitiveAccessGrant.created_at))
    res = await db.execute(stmt)
    grants = res.scalars().all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    items = []
    mutated = False

    # Fetch admin emails
    admin_ids = list({g.admin_id for g in grants if g.admin_id})
    admins_map = {}
    if admin_ids:
        u_stmt = select(User).where(User.id.in_(admin_ids))
        u_res = await db.execute(u_stmt)
        for u in u_res.scalars().all():
            admins_map[str(u.id)] = u.email

    for g in grants:
        # Check backend authoritative expiration
        current_status = g.status
        if current_status == "active" and g.expires_at <= now:
            g.status = "expired"
            current_status = "expired"
            mutated = True

        items.append({
            "id": str(g.id),
            "admin_id": str(g.admin_id),
            "admin_email": admins_map.get(str(g.admin_id), "Unknown"),
            "resource_type": g.resource_type,
            "resource_id": g.resource_id,
            "reason": g.reason,
            "status": current_status,
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "expires_at": g.expires_at.isoformat() if g.expires_at else None,
            "revoked_at": g.revoked_at.isoformat() if g.revoked_at else None,
        })

    if mutated:
        await db.commit()

    return {"grants": items}

@router.post("/break-glass/grants/{grant_id}/revoke")
async def revoke_break_glass_grant(
    grant_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass:revoke"))
):
    try:
        g_uuid = uuid.UUID(grant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid grant ID format")

    res = await db.execute(select(SensitiveAccessGrant).where(SensitiveAccessGrant.id == g_uuid))
    grant = res.scalar_one_or_none()
    if not grant:
        raise HTTPException(status_code=404, detail="Sensitive access grant not found")

    if grant.status != "active":
        raise HTTPException(status_code=400, detail=f"Cannot revoke grant in status '{grant.status}'")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    grant.status = "revoked"
    grant.revoked_at = now
    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="break_glass_revoke",
        resource_type=grant.resource_type,
        resource_id=grant.resource_id,
        permission_used="break_glass:revoke",
        result="success",
        reason="Revoked manually by administrator",
        request=request,
        metadata={"grant_id": str(grant.id)},
        sensitive_access_flag=True
    )

    return {"message": "Sensitive access grant revoked successfully", "grant_id": str(grant.id)}
