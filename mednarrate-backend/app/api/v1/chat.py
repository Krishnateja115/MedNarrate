import asyncio
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.maintenance import check_maintenance
from app.middleware.ownership import verify_chat_session_ownership
from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageOut,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionOut,
)
from app.services.translation_validation import TranslationVerifier
from app.services.llm_client import generate
from app.models.report import Report
from app.services.prompts import (
    CHAT_EMERGENCY_RESPONSE,
    CHAT_REFUSAL_RESPONSE,
    GENERAL_CHAT_PROMPT,
    GENERAL_CHAT_SYSTEM,
    RAG_SYSTEM_PROMPT,
)
from app.services.rag import retrieve_chunks
from app.services.rag_safety import verify_response_against_source
from app.services.feature_flags import evaluate_flag


logger = logging.getLogger(__name__)

# Whole-word / whole-phrase matching: plain substring checks flagged harmless
# text such as "studying" ("dying") or "keystroke" ("stroke").
_EMERGENCY_RE = re.compile(
    r"\b("
    r"emergency|911|heart attack|bleeding|stroke|suicide|suicidal|dying|"
    r"chest pain|difficulty breathing|trouble breathing|can'?t breathe|cannot breathe|"
    r"overdose|kill myself|end my life|want to die|unconscious|seizure|anaphylaxis"
    r")\b",
    re.IGNORECASE,
)


def local_classify_intent(query: str) -> str:
    """
    Deterministic intent classification to avoid LLM quota usage.
    """
    query_lower = query.lower()

    # Emergency keywords
    if _EMERGENCY_RE.search(query_lower):
        return "emergency"

    # Diagnosis/Treatment keywords
    medical_advice_patterns = [
        "do i have",
        "am i diagnosed",
        "what should i take",
        "how do i treat",
        "cure my",
        "prescribe",
        "dosage",
        "treatment for",
    ]
    if any(p in query_lower for p in medical_advice_patterns):
        return "diagnosis"

    return "general"


router = APIRouter()


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_chat_session(
    req: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.report_id:
        from app.middleware.ownership import verify_report_ownership

        await verify_report_ownership(str(req.report_id), str(current_user.id), db)

    session = ChatSession(
        user_id=current_user.id, report_id=req.report_id, title=req.title or "New Chat"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.created_at))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/sessions/{id}/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(
    id: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await verify_chat_session_ownership(id, str(current_user.id), db)

    # offset counts back from the NEWEST message so the default page is the
    # most recent conversation (previously the oldest 20 were returned and
    # newer messages in long chats were never shown). Output stays
    # chronological (oldest -> newest) for the client.
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == session.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(reversed(result.scalars().all()))


_HISTORY_MESSAGES = 6
_HISTORY_CHARS = 700


async def _recent_history(req, session, db: AsyncSession) -> str:
    """The last few turns of this chat, so follow-up questions make sense."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == session.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(_HISTORY_MESSAGES + 1)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    # The question being answered was already saved; do not repeat it.
    if rows and rows[0].role == ChatRole.user and rows[0].content == req.content:
        rows = rows[1:]
    lines = []
    for m in reversed(rows[:_HISTORY_MESSAGES]):
        who = "User" if m.role == ChatRole.user else "Assistant"
        text = (m.content or "").strip().replace("\n", " ")
        lines.append(f"{who}: {text[:_HISTORY_CHARS]}")
    return "\n".join(lines) if lines else "(none)"


async def _reports_overview(user_id, db: AsyncSession) -> str:
    """Titles, dates and types of the user's reports. No lab values."""
    stmt = (
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(desc(Report.report_date))
        .limit(10)
    )
    reports = (await db.execute(stmt)).scalars().all()
    if not reports:
        return "The user has not uploaded any reports yet."
    lines = []
    for r in reports:
        rtype = getattr(r.report_type, "value", r.report_type)
        lines.append(f"- {str(r.title)[:80]} ({r.report_date}, {rtype})")
    return "\n".join(lines)


async def _generate_rag_answer(req, session, db: AsyncSession) -> tuple[str, str]:
    """Generate and verify the assistant reply.

    A chat opened from a report answers from that report. A chat opened from
    the assistant screen (no report) is a general health assistant.
    """
    context = ""
    history = await _recent_history(req, session, db)
    if session.report_id:
        context = await retrieve_chunks(req.content, session.report_id, db, top_k=5)
        prompt = RAG_SYSTEM_PROMPT.format(
            context=context, history=history, question=req.content
        )
        chat_sys = (
            "You are a helpful medical AI assistant. Answer conversationally, concisely and clearly. "
            "Do not offer diagnoses or prescribe medication."
        )
    else:
        overview = await _reports_overview(session.user_id, db)
        prompt = GENERAL_CHAT_PROMPT.format(
            reports_overview=overview, history=history, question=req.content
        )
        chat_sys = GENERAL_CHAT_SYSTEM

    language = (getattr(req, "language", None) or "en").strip() or "en"
    if language != "en":
        chat_sys += f" You MUST reply in the language with ISO code: {language}."

    ai_response = await generate(
        prompt, system_instruction=chat_sys, thinking_level="LOW"
    )

    # Lightweight verification of language / meta-text
    verifier = TranslationVerifier()
    verify_result = verifier.verify({"content": req.content}, {"content": ai_response}, language)
    if not verify_result["ok"]:
        retry_prompt = prompt + f"\n\nYOUR PREVIOUS RESPONSE FAILED: {'; '.join(f['reason'] for f in verify_result['failures'])}. PLEASE REPLY IN {language} WITHOUT META-TEXT."
        ai_response_retry = await generate(
            retry_prompt, system_instruction=chat_sys, thinking_level="LOW"
        )
        verify_result_retry = verifier.verify({"content": req.content}, {"content": ai_response_retry}, language)
        if verify_result_retry["ok"] or len(verify_result_retry["failures"]) < len(verify_result["failures"]):
            ai_response = ai_response_retry
        else:
            ai_response = ai_response + "\n\n(Translation note: The system encountered difficulty formatting this response in your language.)"

    # 5. Hallucination guard
    if context:
        use_guard = await evaluate_flag(db, "rag_hallucination_guard")
        if use_guard:
            ai_response, _ = verify_response_against_source(ai_response, context)

    return ai_response, context


@router.post("/sessions/{id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    id: str,
    req: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    maintenance = Depends(check_maintenance("chat")),
):
    session = await verify_chat_session_ownership(id, str(current_user.id), db)

    # 1. Persist user message
    user_msg = ChatMessage(
        chat_session_id=session.id, role=ChatRole.user, content=req.content
    )
    db.add(user_msg)
    await db.commit()
    user_msg_id = user_msg.id
    session_id = session.id
    # 2. Run Safety Classifier (Local/Deterministic)
    classification = local_classify_intent(req.content)
    allowed_categories = {"emergency", "diagnosis", "treatment", "report", "general"}
    if classification not in allowed_categories:
        classification = "general"

    sources = []

    if "emergency" in classification:
        ai_response = CHAT_EMERGENCY_RESPONSE
    elif "diagnosis" in classification or "treatment" in classification:
        ai_response = CHAT_REFUSAL_RESPONSE
    else:
        try:
            ai_response, context = await asyncio.wait_for(
                _generate_rag_answer(req, session, db),
                timeout=float(getattr(settings, "CHAT_TIMEOUT_SECONDS", 75.0)),
            )
        except HTTPException:
            raise
        except Exception:
            # The user's message was already committed; remove it so a client
            # retry does not leave an orphan/duplicate question in the history.
            logger.exception("Chat generation failed for session %s", session_id)
            try:
                from sqlalchemy import delete as sa_delete

                await db.rollback()
                await db.execute(
                    sa_delete(ChatMessage).where(ChatMessage.id == user_msg_id)
                )
                await db.commit()
            except Exception:
                await db.rollback()
            raise HTTPException(
                status_code=503,
                detail="The AI assistant is temporarily unavailable. Please try again.",
            )

    # 6. Persist assistant message
    assistant_msg = ChatMessage(
        chat_session_id=session.id, role=ChatRole.assistant, content=ai_response
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatMessageResponse(
        message=ChatMessageOut.model_validate(assistant_msg), sources=sources
    )
