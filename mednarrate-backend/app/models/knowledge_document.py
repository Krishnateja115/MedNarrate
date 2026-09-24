import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String, Text

from app.core.database import Base


class DocLifecycleStatus(str, enum.Enum):
    draft = "Draft"
    review = "Review"
    approved = "Approved"
    published = "Published"
    archived = "Archived"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    status = Column(
        Enum(DocLifecycleStatus), nullable=False, default=DocLifecycleStatus.draft
    )
    approval_state = Column(
        String(100), nullable=True
    )  # E.g., 'pending_dr_smith', 'approved'
    source_metadata = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
