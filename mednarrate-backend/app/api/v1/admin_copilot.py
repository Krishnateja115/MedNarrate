import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.services.audit import log_admin_action

router = APIRouter()

class CopilotMessage(BaseModel):
    role: str
    content: str

class CopilotRequest(BaseModel):
    messages: List[CopilotMessage]

class CopilotResponse(BaseModel):
    status: str = "ok"
    reply: str

@router.post("/chat", response_model=CopilotResponse)
async def chat_with_copilot(
    request: Request,
    payload: CopilotRequest,
    admin_ctx: AdminContext = Depends(require_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin Copilot chat endpoint. Allows administrators to query system data or docs.
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # In a real implementation, this would connect to LangChain or GenAI using 
    # the existing models. Since we don't have the explicit prompt context, 
    # we return a simulated response based on the actual system state.
    
    last_msg = payload.messages[-1].content
    
    reply_content = "I am the MedNarrate Admin Copilot. I can assist you with system operations, user management, and report analysis. (Implementation is a placeholder pending full LangChain agent deployment)."
    
    # Audit log the copilot interaction
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
