import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class ChatSafetyEvent(Base):
    __tablename__ = "chat_safety_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    classification = Column(
        String(100), nullable=False
    )  # e.g., 'prompt_injection', 'emergency', 'self_harm'
    action_taken = Column(
        String(100), nullable=False
    )  # e.g., 'blocked', 'flagged', 'alerted'
    safe_summary = Column(Text, nullable=True)  # Non-PHI summary of the event

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
