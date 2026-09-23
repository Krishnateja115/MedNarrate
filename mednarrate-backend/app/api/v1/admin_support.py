from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.admin_auth import AdminContext, get_admin_context, require_permission, require_any_permission
from app.models.support import SupportTicket, SupportTicketMessage, SupportTicketEvent, TicketCategory, TicketPriority, TicketStatus
from app.models.incidents import Incident, IncidentSeverity, IncidentStatus, IncidentEvent
from app.services.audit import log_admin_action

router = APIRouter()

class AdminReplyPayload(BaseModel):
    content: str
    is_internal: bool = False
    
class AdminUpdateTicketPayload(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_admin_id: Optional[str] = None

class AdminEscalatePayload(BaseModel):
    escalation_type: str # "incident", "engineering", "security"
    reason: str

@router.get("")
async def list_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_admin_id: Optional[str] = None,
    unassigned: Optional[bool] = False,
    search: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SupportTicket).order_by(SupportTicket.updated_at.desc())
    
    if status:
        stmt = stmt.where(SupportTicket.status == status)
    if priority:
        stmt = stmt.where(SupportTicket.priority == priority)
    if unassigned:
        stmt = stmt.where(SupportTicket.assigned_admin_id == None)
    elif assigned_admin_id:
        stmt = stmt.where(SupportTicket.assigned_admin_id == assigned_admin_id)
        
    if search:
        # Simple search across title or ID
        stmt = stmt.where(
            or_(
                SupportTicket.title.ilike(f"%{search}%"),
                SupportTicket.id.ilike(f"%{search}%"),
                SupportTicket.user_id.ilike(f"%{search}%")
            )
        )
        
    result = await db.execute(stmt.options(selectinload(SupportTicket.user)))
    tickets = result.scalars().all()
    
    return {
        "status": "ok",
        "tickets": [
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
                "updated_at": t.updated_at
            } for t in tickets
        ]
    }

@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    admin_ctx: AdminContext = Depends(require_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SupportTicket).where(SupportTicket.id == ticket_id).options(
        selectinload(SupportTicket.user),
        selectinload(SupportTicket.messages),
        selectinload(SupportTicket.events)
    )
    ticket = (await db.execute(stmt)).scalars().first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Build automatic diagnostic snapshot if related_report_id exists and not yet snapshotted
    if ticket.related_report_id:
        # Just fetching basic info for diagnostic, ideally we would generate a snapshot here if it doesn't exist
        pass

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
            "updated_at": ticket.updated_at
        },
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "is_internal": m.is_internal,
                "content": m.content,
                "created_at": m.created_at
            } for m in sorted(ticket.messages, key=lambda x: x.created_at)
        ],
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "content": e.content,
                "created_at": e.created_at
            } for e in sorted(ticket.events, key=lambda x: x.created_at)
        ]
    }

@router.post("/{ticket_id}/reply")
async def reply_ticket(
    ticket_id: str,
    payload: AdminReplyPayload,
    admin_ctx: AdminContext = Depends(require_permission("support.manage")),
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    msg = SupportTicketMessage(
        ticket_id=ticket.id,
        sender_id=str(admin_ctx.user.id),
        is_internal=payload.is_internal,
        content=payload.content
    )
    db.add(msg)
    
    # Auto transition state if it's a public reply
    if not payload.is_internal and ticket.status in [TicketStatus.new, TicketStatus.investigating]:
        ticket.status = TicketStatus.waiting_user
        
    await log_admin_action(
        db=db,
        action="SUPPORT_REPLY" if not payload.is_internal else "SUPPORT_INTERNAL_NOTE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="SupportTicket",
        resource_id=ticket.id
    )
    
    await db.commit()
    return {"status": "ok", "message_id": msg.id}

@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    payload: AdminUpdateTicketPayload,
    admin_ctx: AdminContext = Depends(require_permission("support.manage")),
    db: AsyncSession = Depends(get_db)
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
        ticket.assigned_admin_id = payload.assigned_admin_id if payload.assigned_admin_id else None
        changes.append(f"Reassigned to {payload.assigned_admin_id}")

    if changes:
        evt = SupportTicketEvent(
            ticket_id=ticket.id,
            event_type="update",
            content=", ".join(changes)
        )
        db.add(evt)
        
        await log_admin_action(
            db=db,
            action="SUPPORT_TICKET_UPDATE",
            actor_admin_id=admin_ctx.user.id,
            resource_type="SupportTicket",
            resource_id=ticket.id,
            metadata={"changes": changes}
        )
        await db.commit()
        
    return {"status": "ok", "changes": changes}

@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: str,
    payload: AdminEscalatePayload,
    admin_ctx: AdminContext = Depends(require_permission("support.escalate")),
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    evt = SupportTicketEvent(
        ticket_id=ticket.id,
        event_type="escalation",
        content=f"Escalated to {payload.escalation_type}: {payload.reason}"
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
            created_by_id=admin_ctx.user.id
        )
        db.add(incident)
        await db.flush()
        ticket.related_incident_id = incident.id
        incident_id = incident.id
        
        db.add(IncidentEvent(
            incident_id=incident.id,
            actor_id=admin_ctx.user.id,
            event_type="CREATED_FROM_TICKET",
            message=f"Created from Support Ticket {ticket.id}"
        ))

    await log_admin_action(
        db=db,
        action="SUPPORT_TICKET_ESCALATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="SupportTicket",
        resource_id=ticket.id,
        metadata={"escalation_type": payload.escalation_type}
    )
    await db.commit()
    
    return {"status": "ok", "incident_id": incident_id}
