import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from app.core.database import Base

class OrphanFile(Base):
    __tablename__ = "orphan_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String(512), nullable=False, index=True)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
