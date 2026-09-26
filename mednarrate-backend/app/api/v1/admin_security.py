from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_any_permission
from app.core.database import get_db
from app.models.admin import AdminAuditLog
from app.models.user import User
from app.services.audit import log_admin_action
from app.services.security_metrics import SECURITY_EVENT_ACTIONS, get_security_metrics

router = APIRouter()


@router.get("/overview")
async def get_security_overview(
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["security.view", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    await log_admin_action(
        db=db,
        action="VIEW_SECURITY_OVERVIEW",
        actor_admin_id=admin_ctx.user.id,
        permission_used="security.view",
        request=request,
    )
    await db.commit()

    return {"status": "ok", **await get_security_metrics(db)}


@router.get("/events")
async def get_security_events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    admin_ctx: AdminContext = Depends(
        require_any_permission(["security.view", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AdminAuditLog).order_by(desc(AdminAuditLog.timestamp))

    if event_type:
        stmt = stmt.where(AdminAuditLog.action == event_type)
    else:
        # Default to security-relevant event types
        stmt = stmt.where(AdminAuditLog.action.in_(SECURITY_EVENT_ACTIONS))

    if result:
        stmt = stmt.where(AdminAuditLog.result == result)

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    actor_ids = {log.actor_admin_id for log in logs if log.actor_admin_id}
    actor_emails: dict[str, str] = {}
    if actor_ids:
        users = (await db.execute(select(User).where(User.id.in_(actor_ids)))).scalars()
        actor_emails = {str(user.id): user.email for user in users}

    events_out = []
    for log in logs:
        # Never expose secrets/passwords/tokens/secrets in events
        events_out.append(
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "actor_admin_id": (
                    str(log.actor_admin_id) if log.actor_admin_id else "System"
                ),
                "actor_email": (
                    actor_emails.get(str(log.actor_admin_id))
                    if log.actor_admin_id
                    else "System"
                ),
                "event": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "result": log.result,
                "reason": log.reason,
                "request_id": log.request_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "metadata": log.metadata_payload or {},
            }
        )

    await log_admin_action(
        db=db,
        action="VIEW_SECURITY_EVENTS",
        actor_admin_id=admin_ctx.user.id,
        permission_used="security.view",
        request=request,
    )
    await db.commit()

    return events_out
