from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.support import SupportTicket, SupportTicketMessage, TicketCategory, TicketPriority, TicketStatus

router = APIRouter()

class SupportTicketCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.p3
    related_report_id: Optional[str] = None

class SupportTicketReply(BaseModel):
    content: str

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ticket = SupportTicket(
        user_id=str(current_user.id),
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        related_report_id=payload.related_report_id,
        status=TicketStatus.new
    )
    db.add(ticket)
    await db.flush()

    # Initial message
    message = SupportTicketMessage(
        ticket_id=ticket.id,
        sender_id=str(current_user.id),
        is_internal=False,
        content=payload.description
    )
    db.add(message)
    await db.commit()
    return {"status": "ok", "ticket_id": ticket.id}

@router.get("")
async def list_user_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SupportTicket).where(SupportTicket.user_id == str(current_user.id)).order_by(SupportTicket.updated_at.desc())
    result = await db.execute(stmt)
    tickets = result.scalars().all()
    
    return {
        "status": "ok",
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "status": t.status,
                "priority": t.priority,
                "updated_at": t.updated_at
            }
            for t in tickets
        ]
    }

@router.get("/{ticket_id}")
async def get_user_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SupportTicket).where(SupportTicket.id == ticket_id, SupportTicket.user_id == str(current_user.id))
    ticket = (await db.execute(stmt)).scalars().first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    msg_stmt = select(SupportTicketMessage).where(
        SupportTicketMessage.ticket_id == ticket_id,
        SupportTicketMessage.is_internal == False
    ).order_by(SupportTicketMessage.created_at.asc())
    
    messages = (await db.execute(msg_stmt)).scalars().all()
    
    return {
        "status": "ok",
        "ticket": {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "status": ticket.status,
            "created_at": ticket.created_at,
            "messages": [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "content": m.content,
                    "created_at": m.created_at
                }
                for m in messages
            ]
        }
    }

@router.post("/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: str,
    payload: SupportTicketReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SupportTicket).where(SupportTicket.id == ticket_id, SupportTicket.user_id == str(current_user.id))
    ticket = (await db.execute(stmt)).scalars().first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    message = SupportTicketMessage(
        ticket_id=ticket.id,
        sender_id=str(current_user.id),
        is_internal=False,
        content=payload.content
    )
    db.add(message)
    
    ticket.status = TicketStatus.waiting_eng
    
    await db.commit()
    return {"status": "ok", "message_id": message.id}
