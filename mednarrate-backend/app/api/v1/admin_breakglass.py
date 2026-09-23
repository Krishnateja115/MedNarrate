"""
Break-Glass / Sensitive Access API.

Lifecycle:
  REQUESTED  — admin requests access, awaiting approval
  APPROVED   — a *different* admin approved (sets status to 'active' with expiry timer)
  ACTIVE     — access window open; enforced server-side by validate_access_grant()
  EXPIRED    — server-side expiry detected (lazy or background)
  REVOKED    — explicitly revoked before expiry

Permissions:
  break_glass.request  — submit a request
  break_glass.approve  — approve another admin's request (cannot approve own)
  break_glass.revoke   — revoke an active grant
  break_glass.read     — list/view grants (security admins)
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
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
    resource_type: str = Field(..., example="medical_report")
    resource_id: str = Field(..., example="rep_12345",
                             description="Exact resource ID, or '*' for all resources of this type")
    reason: str = Field(..., min_length=10, example="Emergency clinical review requested by attending physician")
    duration_minutes: int = Field(default=30, ge=5, le=120)


class BreakGlassApprovalPayload(BaseModel):
    notes: Optional[str] = Field(None, description="Optional approval notes")


class BreakGlassRevokePayload(BaseModel):
    reason: str = Field(default="Revoked by administrator", min_length=3)


def _serialize_grant(g: SensitiveAccessGrant, admins_map: dict) -> dict:
    return {
        "id": str(g.id),
        "admin_id": str(g.admin_id),
        "admin_email": admins_map.get(str(g.admin_id), "Unknown"),
        "resource_type": g.resource_type,
        "resource_id": g.resource_id,
        "reason": g.reason,
        "status": g.status,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "expires_at": g.expires_at.isoformat() if g.expires_at else None,
        "approved_by_id": str(g.approved_by_id) if g.approved_by_id else None,
        "approved_by_email": admins_map.get(str(g.approved_by_id), None) if g.approved_by_id else None,
        "approved_at": g.approved_at.isoformat() if g.approved_at else None,
        "revoked_at": g.revoked_at.isoformat() if g.revoked_at else None,
        "revoker_id": str(g.revoker_id) if g.revoker_id else None,
        "revoker_email": admins_map.get(str(g.revoker_id), None) if g.revoker_id else None,
        "revoke_reason": g.revoke_reason,
    }


async def _build_admins_map(grants: list, db: AsyncSession) -> dict:
    """Pre-fetch admin emails for a list of grants."""
    admin_ids = set()
    for g in grants:
        if g.admin_id:
            admin_ids.add(g.admin_id)
        if g.approved_by_id:
            admin_ids.add(g.approved_by_id)
        if g.revoker_id:
            admin_ids.add(g.revoker_id)
    
    admins_map = {}
    if admin_ids:
        u_stmt = select(User).where(User.id.in_(admin_ids))
        for u in (await db.execute(u_stmt)).scalars().all():
            admins_map[str(u.id)] = u.email
    return admins_map


@router.post("/break-glass/request")
async def request_break_glass_access(
    req: BreakGlassRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass.request"))
):
    """
    Submit a break-glass access request.
    Status starts as 'requested' — a different admin must approve it.
    Super Admins can self-approve through the approve endpoint explicitly.
    """
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
        status="requested",   # Always starts as REQUESTED — never auto-active
        approved_by_id=None,
        approved_at=None,
    )
    db.add(grant)

    # Audit within same transaction
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="break_glass_requested",
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        permission_used="break_glass.request",
        result="success",
        reason=req.reason,
        request=request,
        metadata={"duration_minutes": req.duration_minutes, "expires_at": expires_at.isoformat()},
        sensitive_access_flag=True
    )

    # Single commit: grant + audit together
    await db.commit()
    await db.refresh(grant)

    return {
        "message": "Sensitive access request submitted. Awaiting approval from another administrator.",
        "grant": {
            "id": str(grant.id),
            "status": grant.status,
            "resource_type": grant.resource_type,
            "resource_id": grant.resource_id,
            "reason": grant.reason,
            "created_at": grant.created_at.isoformat(),
            "expires_at": grant.expires_at.isoformat(),
        }
    }


@router.post("/break-glass/grants/{grant_id}/approve")
async def approve_break_glass_grant(
    grant_id: str,
    payload: BreakGlassApprovalPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass.approve"))
):
    """
    Approve a break-glass request from another admin.
    Self-approval is explicitly blocked — the requester and approver must differ.
    Super Admins are also blocked from approving their own requests to maintain audit integrity.
    """
    try:
        g_uuid = uuid.UUID(grant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid grant ID format")

    res = await db.execute(select(SensitiveAccessGrant).where(SensitiveAccessGrant.id == g_uuid))
    grant = res.scalar_one_or_none()
    if not grant:
        raise HTTPException(status_code=404, detail="Sensitive access grant not found")

    if grant.status != "requested":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve a grant in status '{grant.status}'. Only 'requested' grants can be approved."
        )

    # CRITICAL: Block self-approval
    if grant.admin_id == admin_ctx.user_id:
        raise HTTPException(
            status_code=403,
            detail="Self-approval is not permitted. A different administrator must approve this request."
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    grant.status = "active"
    grant.approved_by_id = admin_ctx.user_id
    grant.approved_at = now

    # Audit within same transaction
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="break_glass_approved",
        resource_type=grant.resource_type,
        resource_id=grant.resource_id,
        permission_used="break_glass.approve",
        result="success",
        reason=payload.notes or "Approved by administrator",
        request=request,
        metadata={
            "grant_id": str(grant.id),
            "requester_id": str(grant.admin_id),
            "expires_at": grant.expires_at.isoformat()
        },
        sensitive_access_flag=True
    )

    # Single commit: approval + audit together
    await db.commit()

    return {
        "message": "Break-glass access grant approved. Access is now active.",
        "grant_id": str(grant.id),
        "expires_at": grant.expires_at.isoformat(),
        "approved_at": grant.approved_at.isoformat(),
    }


@router.get("/break-glass/grants")
async def list_break_glass_grants(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass.read"))
):
    """List break-glass grants. Auto-expires active-but-past-expiry grants."""
    stmt = select(SensitiveAccessGrant).order_by(desc(SensitiveAccessGrant.created_at)).limit(limit)
    if status_filter:
        stmt = stmt.where(SensitiveAccessGrant.status == status_filter)
    
    res = await db.execute(stmt)
    grants = res.scalars().all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    mutated = False

    # Lazy expiry enforcement
    for g in grants:
        if g.status == "active" and g.expires_at <= now:
            g.status = "expired"
            mutated = True

    admins_map = await _build_admins_map(grants, db)

    if mutated:
        await db.commit()

    return {"grants": [_serialize_grant(g, admins_map) for g in grants]}


@router.get("/break-glass/grants/{grant_id}")
async def get_break_glass_grant(
    grant_id: str,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass.read"))
):
    """Get a specific break-glass grant by ID."""
    try:
        g_uuid = uuid.UUID(grant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid grant ID format")

    res = await db.execute(select(SensitiveAccessGrant).where(SensitiveAccessGrant.id == g_uuid))
    grant = res.scalar_one_or_none()
    if not grant:
        raise HTTPException(status_code=404, detail="Sensitive access grant not found")

    # Lazy expiry
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if grant.status == "active" and grant.expires_at <= now:
        grant.status = "expired"
        await db.commit()

    admins_map = await _build_admins_map([grant], db)
    return {"grant": _serialize_grant(grant, admins_map)}


@router.post("/break-glass/grants/{grant_id}/revoke")
async def revoke_break_glass_grant(
    grant_id: str,
    payload: BreakGlassRevokePayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("break_glass.revoke"))
):
    """Revoke an active break-glass grant. Audit and revocation are atomic."""
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
    grant.revoker_id = admin_ctx.user_id
    grant.revoke_reason = payload.reason

    # Audit within same transaction — single commit ensures atomicity
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="break_glass_revoked",
        resource_type=grant.resource_type,
        resource_id=grant.resource_id,
        permission_used="break_glass.revoke",
        result="success",
        reason=payload.reason,
        request=request,
        metadata={"grant_id": str(grant.id), "original_requester_id": str(grant.admin_id)},
        sensitive_access_flag=True
    )

    await db.commit()

    return {"message": "Sensitive access grant revoked successfully", "grant_id": str(grant.id)}
