"""
Admin Chat Operations API.

Provides operational diagnostics for chat sessions — no raw message content by default.
Sensitive content requires chat.sensitive_view + active break-glass grant.

Paginated endpoints with server-side filtering.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_permission, validate_access_grant
from app.core.database import get_db
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset
from app.models.chat import ChatMessage, ChatSession
from app.models.chat_safety import ChatSafetyEvent

router = APIRouter()


@router.get("/sessions")
async def list_chat_sessions(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("chat.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    List chat sessions with pagination. Returns session metadata only — no message content.
    """
    limit = clamp_limit(limit)
    stmt = select(ChatSession)

    if search:
        stmt = stmt.where(
            or_(
                ChatSession.title.ilike(f"%{search}%"),
            )
        )

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    stmt = (
        stmt.order_by(desc(ChatSession.created_at))
        .offset(page_to_offset(page, limit))
        .limit(limit)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "report_id": str(s.report_id) if s.report_id else None,
            "title": s.title,
            "created_at": s.created_at,
            # Message content intentionally excluded — use /sessions/{id} with break-glass for content
        }
        for s in sessions
    ]

    return build_pagination_response(items, total, page, limit)


@router.get("/sessions/{session_id}")
async def get_chat_session_detail(
    session_id: str,
    admin_ctx: AdminContext = Depends(require_permission("chat.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns session metadata + safety events for a specific chat session.
    Message content is NOT included — requires chat.sensitive_view + break-glass grant.
    """
    try:
        s_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session_res = await db.execute(select(ChatSession).where(ChatSession.id == s_uuid))
    session = session_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Message count (not content)
    msg_count_res = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.chat_session_id == s_uuid)
    )
    message_count = msg_count_res.scalar_one_or_none() or 0

    # Safety events for this session
    safety_res = await db.execute(
        select(ChatSafetyEvent)
        .where(ChatSafetyEvent.chat_session_id == s_uuid)
        .order_by(desc(ChatSafetyEvent.created_at))
    )
    safety_events = safety_res.scalars().all()

    return {
        "session": {
            "id": str(session.id),
            "user_id": str(session.user_id),
            "report_id": str(session.report_id) if session.report_id else None,
            "title": session.title,
            "created_at": session.created_at,
            "message_count": message_count,
            # Raw message content excluded — use sensitive endpoint with break-glass
            "sensitive_content_available": message_count > 0,
        },
        "safety_events": [
            {
                "id": str(e.id),
                "classification": e.classification,
                "action_taken": e.action_taken,
                "safe_summary": e.safe_summary,  # This is the pre-redacted safe summary
                "created_at": e.created_at,
                # raw_content intentionally excluded
            }
            for e in safety_events
        ],
    }


@router.get("/sessions/{session_id}/messages")
async def get_chat_session_messages(
    session_id: str,
    request: object = None,
    admin_ctx: AdminContext = Depends(require_permission("chat.sensitive_view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns actual chat messages for a session.
    Requires: chat.sensitive_view permission + active break-glass grant.
    Every access is audited.
    """
    try:
        s_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Enforce break-glass grant
    grant = await validate_access_grant(
        admin_ctx=admin_ctx, resource_type="chat_session", resource_id=session_id, db=db
    )

    session_res = await db.execute(select(ChatSession).where(ChatSession.id == s_uuid))
    session = session_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages_res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == s_uuid)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_res.scalars().all()

    from app.services.audit import log_admin_action

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="SENSITIVE_CHAT_ACCESS",
        resource_type="chat_session",
        resource_id=session_id,
        permission_used="chat.sensitive_view",
        result="success",
        reason=f"Break-glass grant {grant.id}",
        metadata={"grant_id": str(grant.id), "message_count": len(messages)},
        sensitive_access_flag=True,
    )
    await db.commit()

    return {
        "grant_id": str(grant.id),
        "grant_expires_at": grant.expires_at.isoformat(),
        "session_id": session_id,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value if hasattr(m.role, "value") else m.role,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.get("/safety-events")
async def list_safety_events(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin_ctx: AdminContext = Depends(require_permission("chat.view")),
    db: AsyncSession = Depends(get_db),
):
    """List chat safety events with pagination. safe_summary only — no raw content."""
    limit = clamp_limit(limit)
    stmt = select(ChatSafetyEvent)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        stmt.order_by(desc(ChatSafetyEvent.created_at))
        .offset(page_to_offset(page, limit))
        .limit(limit)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    items = [
        {
            "id": str(e.id),
            "chat_session_id": str(e.chat_session_id),
            "user_id": str(e.user_id),
            "classification": e.classification,
            "action_taken": e.action_taken,
            "safe_summary": e.safe_summary,
            "created_at": e.created_at,
            # raw_content intentionally excluded
        }
        for e in events
    ]

    return build_pagination_response(items, total, page, limit)
