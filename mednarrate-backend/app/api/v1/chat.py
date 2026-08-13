from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, ChatRole
from app.models.report_analysis import ReportAnalysis
from app.schemas.chat import ChatSessionCreate, ChatSessionOut, ChatMessageCreate, ChatMessageOut, ChatMessageResponse
from app.services.rag import retrieve_chunks
from app.services.llm_client import generate
from app.services.prompts import CHAT_PROMPT
import json

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_chat_session(
    req: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = ChatSession(
        user_id=current_user.id,
        report_id=req.report_id,
        title=req.title or "New Chat"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(desc(ChatSession.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/sessions/{id}/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(
    id: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify owner
    stmt_session = select(ChatSession).where(ChatSession.id == id, ChatSession.user_id == current_user.id)
    session = (await db.execute(stmt_session)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    stmt = select(ChatMessage).where(ChatMessage.chat_session_id == id).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/sessions/{id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    id: str,
    req: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify owner
    stmt_session = select(ChatSession).where(ChatSession.id == id, ChatSession.user_id == current_user.id)
    session = (await db.execute(stmt_session)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 1. Persist user message
    user_msg = ChatMessage(
        chat_session_id=session.id,
        role=ChatRole.user,
        content=req.content
    )
    db.add(user_msg)
    await db.commit()
    
    # 2. RAG retrieve chunks
    chunks = await retrieve_chunks(req.content, top_k=3)
    rag_context = "\n".join([f"{c.source}: {c.content}" for c in chunks])
    
    # 3. Report context if present
    report_context = ""
    if session.report_id:
        stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == session.report_id)
        analysis = (await db.execute(stmt_analysis)).scalars().first()
        if analysis:
            report_context = json.dumps(analysis.structured_lab_values, indent=2) + "\n" + (analysis.patient_summary or "")
            
    # 4. Generate response
    prompt = CHAT_PROMPT.format(
        rag_context=rag_context,
        report_context=report_context,
        user_query=req.content
    )
    
    ai_response = await generate(prompt)
    
    # 5. Persist assistant message
    assistant_msg = ChatMessage(
        chat_session_id=session.id,
        role=ChatRole.assistant,
        content=ai_response
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    
    sources = [{"source": c.source, "chunk_id": str(c.id)} for c in chunks]
    
    return ChatMessageResponse(
        message=ChatMessageOut.model_validate(assistant_msg),
        sources=sources
    )
