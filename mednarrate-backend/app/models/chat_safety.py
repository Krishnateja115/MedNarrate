import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class ChatSafetyEvent(Base):
    __tablename__ = "chat_safety_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    classification = Column(String(100), nullable=False) # e.g., 'prompt_injection', 'emergency', 'self_harm'
    action_taken = Column(String(100), nullable=False) # e.g., 'blocked', 'flagged', 'alerted'
    safe_summary = Column(Text, nullable=True) # Non-PHI summary of the event
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
