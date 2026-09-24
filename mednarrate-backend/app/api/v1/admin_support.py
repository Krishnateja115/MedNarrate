from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset
from app.models.incidents import (
    Incident,
    IncidentEvent,
    IncidentSeverity,
    IncidentStatus,
)
from app.models.support import (
    SupportTicket,
    SupportTicketEvent,
    SupportTicketMessage,
    TicketPriority,
    TicketStatus,
)
from app.services.audit import log_admin_action
from app.services.support_diagnostics import build_diagnostic_snapshot

router = APIRouter()


class AdminReplyPayload(BaseModel):
    content: str
    is_internal: bool = False


class AdminUpdateTicketPayload(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_admin_id: Optional[str] = None


class AdminEscalatePayload(BaseModel):
    escalation_type: str  # "incident", "engineering", "security"
    reason: str


@router.get("")
async def list_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_admin_id: Optional[str] = None,
    unassigned: Optional[bool] = False,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("support.view")),
    db: AsyncSession = Depends(get_db),
):
    limit = clamp_limit(limit)
    stmt = select(SupportTicket)

    if status:
        stmt = stmt.where(SupportTicket.status == status)
    if priority:
        stmt = stmt.where(SupportTicket.priority == priority)
    if unassigned:
        stmt = stmt.where(SupportTicket.assigned_admin_id is None)
    elif assigned_admin_id:
        stmt = stmt.where(SupportTicket.assigned_admin_id == assigned_admin_id)

    if search:
        stmt = stmt.where(
            or_(
                SupportTicket.title.ilike(f"%{search}%"),
                SupportTicket.id.ilike(f"%{search}%"),
                SupportTicket.user_id.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = page_to_offset(page, limit)
    stmt = stmt.order_by(SupportTicket.updated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt.options(selectinload(SupportTicket.user)))
    tickets = result.scalars().all()

    items = [
        {
            "id": t.id,
            "user_id": t.user_id,
            "user_email": t.user.email if t.user else None,
            "title": t.title,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "assigned_admin_id": t.assigned_admin_id,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in tickets
    ]

    return build_pagination_response(items, total, page, limit)


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    admin_ctx: AdminContext = Depends(require_permission("support.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SupportTicket)
        .where(SupportTicket.id == ticket_id)
        .options(
            selectinload(SupportTicket.user),
            selectinload(SupportTicket.messages),
            selectinload(SupportTicket.events),
        )
    )
    ticket = (await db.execute(stmt)).scalars().first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Build real diagnostic snapshot for any ticket with a related resource
    diagnostic_snapshot = await build_diagnostic_snapshot(
        ticket=ticket,
        db=db,
        admin_can_manage_reports=admin_ctx.has_permission("reports.manage"),
        admin_can_manage_support=admin_ctx.has_permission("support.manage"),
    )

    return {
        "status": "ok",
        "ticket": {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "user_email": ticket.user.email if ticket.user else None,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "assigned_admin_id": ticket.assigned_admin_id,
            "related_report_id": ticket.related_report_id,
            "related_incident_id": ticket.related_incident_id,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
        },
        "diagnostic_snapshot": diagnostic_snapshot,
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "is_internal": m.is_internal,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in sorted(ticket.messages, key=lambda x: x.created_at)
        ],
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "content": e.content,
                "created_at": e.created_at,
            }
            for e in sorted(ticket.events, key=lambda x: x.created_at)
        ],
    }


@router.post("/{ticket_id}/reply")
async def reply_ticket(
    ticket_id: str,
    payload: AdminReplyPayload,
    admin_ctx: AdminContext = Depends(require_permission("support.manage")),
    db: AsyncSession = Depends(get_db),
):
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    msg = SupportTicketMessage(
        ticket_id=ticket.id,
        sender_id=str(admin_ctx.user.id),
        is_internal=payload.is_internal,
        content=payload.content,
    )
    db.add(msg)

    # Auto transition state if it's a public reply
    if not payload.is_internal and ticket.status in [
        TicketStatus.new,
        TicketStatus.investigating,
    ]:
        ticket.status = TicketStatus.waiting_user

    await log_admin_action(
        db=db,
        action="SUPPORT_REPLY" if not payload.is_internal else "SUPPORT_INTERNAL_NOTE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="SupportTicket",
        resource_id=ticket.id,
    )

    await db.commit()
    return {"status": "ok", "message_id": msg.id}


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    payload: AdminUpdateTicketPayload,
    admin_ctx: AdminContext = Depends(require_permission("support.manage")),
    db: AsyncSession = Depends(get_db),
):
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    changes = []

    if payload.status and payload.status != ticket.status:
        ticket.status = payload.status
        changes.append(f"Status changed to {payload.status}")

    if payload.priority and payload.priority != ticket.priority:
        ticket.priority = payload.priority
        changes.append(f"Priority changed to {payload.priority}")

    if payload.assigned_admin_id is not None:
        ticket.assigned_admin_id = (
            payload.assigned_admin_id if payload.assigned_admin_id else None
        )
        changes.append(f"Reassigned to {payload.assigned_admin_id}")

    if changes:
        evt = SupportTicketEvent(
            ticket_id=ticket.id, event_type="update", content=", ".join(changes)
        )
        db.add(evt)

        await log_admin_action(
            db=db,
            action="SUPPORT_TICKET_UPDATE",
            actor_admin_id=admin_ctx.user.id,
            resource_type="SupportTicket",
            resource_id=ticket.id,
            metadata={"changes": changes},
        )
        await db.commit()

    return {"status": "ok", "changes": changes}


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: str,
    payload: AdminEscalatePayload,
    admin_ctx: AdminContext = Depends(require_permission("support.escalate")),
    db: AsyncSession = Depends(get_db),
):
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    evt = SupportTicketEvent(
        ticket_id=ticket.id,
        event_type="escalation",
        content=f"Escalated to {payload.escalation_type}: {payload.reason}",
    )
    db.add(evt)

    ticket.status = TicketStatus.waiting_eng

    incident_id = None
    if payload.escalation_type == "incident":
        # Create an incident automatically
        incident = Incident(
            title=f"Escalated: {ticket.title}",
            description=f"Escalated from Ticket {ticket.id}\nReason: {payload.reason}",
            severity=IncidentSeverity.sev3,
            status=IncidentStatus.investigating,
            created_by_id=admin_ctx.user.id,
        )
        db.add(incident)
        await db.flush()
        ticket.related_incident_id = incident.id
        incident_id = incident.id

        db.add(
            IncidentEvent(
                incident_id=incident.id,
                actor_id=admin_ctx.user.id,
                event_type="CREATED_FROM_TICKET",
                message=f"Created from Support Ticket {ticket.id}",
            )
        )

    await log_admin_action(
        db=db,
        action="SUPPORT_TICKET_ESCALATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="SupportTicket",
        resource_id=ticket.id,
        metadata={"escalation_type": payload.escalation_type},
    )
    await db.commit()

    return {"status": "ok", "incident_id": incident_id}
