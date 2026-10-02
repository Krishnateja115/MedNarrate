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
    """Answer permission-scoped operational questions using LLM tool calling."""
    from app.core.config import settings
    import httpx
    import json

    async def get_user_summary() -> str:
        total = (await db.execute(select(func.count(User.id)))).scalar_one()
        active = (
            await db.execute(
                select(func.count(User.id)).where(User.is_active.is_(True))
            )
        ).scalar_one()
        suspended = total - active
        return f"{total} total accounts, {active} active, {suspended} suspended."

    async def get_incident_summary() -> str:
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
            return "No active incidents."
        return "\n".join(f"- {item.severity.value}: {item.title} ({item.status.value})" for item in incidents)

    async def get_audit_summary() -> str:
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
            return "No recent audit events."
        return "\n".join(f"- {event.timestamp.isoformat()}: {event.action} ({event.result})" for event in events)

    async def get_health_summary() -> str:
        health = await get_system_health(admin_ctx=admin_ctx, db=db)
        service_summary = ", ".join(
            f"{name}: {details.get('status', 'unknown')}"
            for name, details in health["services"].items()
        )
        return f"Overall: {health['status']}. Services: {service_summary}."

    functions = {
        "get_user_summary": get_user_summary,
        "get_incident_summary": get_incident_summary,
        "get_audit_summary": get_audit_summary,
        "get_health_summary": get_health_summary,
    }

    tools_schema = [
        {
            "function_declarations": [
                {"name": "get_user_summary", "description": "Get a summary of total, active, and suspended users."},
                {"name": "get_incident_summary", "description": "Get a summary of currently active incidents."},
                {"name": "get_audit_summary", "description": "Get a summary of recent administrative audit activity."},
                {"name": "get_health_summary", "description": "Get a summary of current system health and service status."},
            ]
        }
    ]

    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key or api_key == "your_gemini_api_key_here":
        # Fallback to old behavior if no API key
        normalized = query.casefold()
        if any(term in normalized for term in ("user", "account")):
            return await get_user_summary()
        if any(term in normalized for term in ("incident", "outage")):
            return await get_incident_summary()
        if any(term in normalized for term in ("audit", "security", "privileged")):
            return await get_audit_summary()
        if any(term in normalized for term in ("health", "status", "service")):
            return await get_health_summary()
        return "I can answer read-only questions about users, incidents, audits, and health."

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    payload = {
        "contents": [{"parts": [{"text": query}]}],
        "tools": tools_schema,
        "systemInstruction": {
            "parts": [{"text": "You are MedNarrate Admin Copilot. You can use tools to fetch system health, user counts, incidents, and audits. Answer concisely using the tool results."}]
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers={"x-goog-api-key": api_key.strip()})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"I encountered an error trying to process your request. Service might be unavailable."

    candidates = data.get("candidates", [])
    if not candidates:
        return "I encountered an error trying to process your request."

    parts = candidates[0].get("content", {}).get("parts", [])

    # Process function calls if any
    tool_results = []
    for part in parts:
        if "functionCall" in part:
            fc = part["functionCall"]
            name = fc.get("name")
            if name in functions:
                result = await functions[name]()
                tool_results.append({
                    "functionResponse": {
                        "name": name,
                        "response": {"result": result}
                    }
                })

    if not tool_results:
        # Just text response
        return "".join(p.get("text", "") for p in parts if "text" in p).strip()

    # Second pass with tool results
    payload["contents"].append(candidates[0].get("content"))
    payload["contents"].append({"parts": tool_results})

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers={"x-goog-api-key": api_key.strip()})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"I encountered an error trying to process your request. Service might be unavailable."

    candidates = data.get("candidates", [])
    if not candidates:
        return "I encountered an error after fetching the data."

    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if "text" in p).strip()


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
