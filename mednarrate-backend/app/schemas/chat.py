from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    # The app limits a question to 500 characters; the API allows some margin
    # but refuses blank or very long messages before they reach the AI.
    content: str = Field(max_length=2000)
    language: Optional[str] = None

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty.")
        return v


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
