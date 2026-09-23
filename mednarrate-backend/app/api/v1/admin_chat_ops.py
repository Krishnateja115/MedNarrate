from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, desc
from typing import Optional

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.chat import ChatSession
from app.models.chat_safety import ChatSafetyEvent

router = APIRouter()

@router.get("/sessions")
async def list_chat_sessions(
    search: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("chat.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSession).order_by(desc(ChatSession.created_at)).limit(50)
    
    if search:
        stmt = stmt.where(or_(
            ChatSession.title.ilike(f"%{search}%"),
            ChatSession.id.ilike(f"%{search}%"),
            ChatSession.user_id.ilike(f"%{search}%")
        ))
        
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    return {
        "status": "ok",
        "sessions": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "report_id": s.report_id,
                "title": s.title,
                "created_at": s.created_at
            } for s in sessions
        ]
    }

@router.get("/safety-events")
async def list_safety_events(
    admin_ctx: AdminContext = Depends(require_permission("chat.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSafetyEvent).order_by(desc(ChatSafetyEvent.created_at)).limit(50)
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    return {
        "status": "ok",
        "events": [
            {
                "id": e.id,
                "chat_session_id": e.chat_session_id,
                "user_id": e.user_id,
                "classification": e.classification,
                "action_taken": e.action_taken,
                "safe_summary": e.safe_summary,
                "created_at": e.created_at
            } for e in events
        ]
    }
