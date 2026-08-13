from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ChatSessionCreate(BaseModel):
    report_id: Optional[UUID] = None
    title: Optional[str] = None

class ChatSessionOut(BaseModel):
    id: UUID
    user_id: UUID
    report_id: Optional[UUID] = None
    title: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageOut(BaseModel):
    id: UUID
    chat_session_id: UUID
    role: str
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageResponse(BaseModel):
    message: ChatMessageOut
    sources: List[Dict[str, Any]] = []
