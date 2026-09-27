from typing import List

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin_health import get_system_health
from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.models.admin import AdminAuditLog
from app.models.incidents import Incident, IncidentStatus
from app.models.user import User
from app.services.audit import log_admin_action

router = APIRouter()


class CopilotMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=2000)


class CopilotRequest(BaseModel):
    messages: List[CopilotMessage] = Field(min_length=1, max_length=20)


class CopilotResponse(BaseModel):
    status: str = "ok"
    reply: str


async def _grounded_reply(query: str, admin_ctx: AdminContext, db: AsyncSession) -> str:
    """Answer only the small set of read-only operational queries we can ground."""
    normalized = query.casefold()

    if any(
        term in normalized for term in ("user", "account", "administrator", "admin")
    ):
        total = (await db.execute(select(func.count(User.id)))).scalar_one()
        active = (
            await db.execute(
                select(func.count(User.id)).where(User.is_active.is_(True))
            )
        ).scalar_one()
        suspended = total - active
        return (
            f"Current account data: {total} total accounts, {active} active accounts, "
            f"and {suspended} suspended or disabled accounts."
        )

    if any(term in normalized for term in ("incident", "outage")):
        incidents = (
            (
                await db.execute(
                    select(Incident)
                    .where(
                        Incident.status.in_(
                            [
                                IncidentStatus.open,
                                IncidentStatus.investigating,
                                IncidentStatus.identified,
                            ]
                        )
                    )
                    .order_by(desc(Incident.started_at))
                    .limit(5)
                )
            )
            .scalars()
            .all()
        )
        if not incidents:
            return "There are no active incidents in the incident register."
        lines = [f"There are {len(incidents)} active incidents (showing up to 5):"]
        lines.extend(
            f"- {item.severity.value}: {item.title} ({item.status.value})"
            for item in incidents
        )
        return "\n".join(lines)

    if any(
        term in normalized for term in ("audit", "security", "privileged", "change")
    ):
        events = (
            (
                await db.execute(
                    select(AdminAuditLog)
                    .order_by(desc(AdminAuditLog.timestamp))
                    .limit(5)
                )
            )
            .scalars()
            .all()
        )
        if not events:
            return "There are no administrative audit events recorded."
        lines = ["Most recent administrative audit activity (up to 5 events):"]
        lines.extend(
            f"- {event.timestamp.isoformat()}: {event.action} ({event.result})"
            for event in events
        )
        return "\n".join(lines)

    if any(term in normalized for term in ("health", "status", "service", "degraded")):
        health = await get_system_health(admin_ctx=admin_ctx, db=db)
        service_summary = ", ".join(
            f"{name.replace('_', ' ')}: {details.get('status', 'unknown')}"
            for name, details in health["services"].items()
        )
        return f"Overall platform status is {health['status']}. Services: {service_summary}."

    return (
        "I can answer read-only questions about current account counts, system health, "
        "active incidents, and recent administrative audit activity. I cannot run shell "
        "commands, access raw clinical data, or answer outside those verified sources."
    )


@router.post("/chat", response_model=CopilotResponse)
async def chat_with_copilot(
    request: Request,
    payload: CopilotRequest,
    admin_ctx: AdminContext = Depends(require_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db),
):
    """Answer permission-scoped operational questions from verified backend data."""
    last_msg = payload.messages[-1].content
    reply_content = await _grounded_reply(last_msg, admin_ctx, db)

    await log_admin_action(
        db=db,
        action="COPILOT_CHAT",
        actor_admin_id=admin_ctx.user.id,
        resource_type="system",
        resource_id="copilot",
        metadata={"query_length": len(last_msg)},
        request=request,
    )
    await db.commit()

    return {"status": "ok", "reply": reply_content}
