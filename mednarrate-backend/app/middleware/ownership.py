from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from app.models.report import Report
from app.models.chat import ChatSession

async def verify_report_ownership(report_id: str, user_id: str, db: AsyncSession) -> Report:
    try:
        report_uuid = uuid.UUID(report_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    stmt = select(Report).where(Report.id == report_uuid)
    result = await db.execute(stmt)
    report = result.scalars().first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != user_uuid:
        raise HTTPException(status_code=403, detail="Not authorized to access this report")
        
    return report

async def verify_chat_session_ownership(session_id: str, user_id: str, db: AsyncSession) -> ChatSession:
    try:
        session_uuid = uuid.UUID(session_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    stmt = select(ChatSession).where(ChatSession.id == session_uuid)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
        
    if session.user_id != user_uuid:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat session")
        
    return session
