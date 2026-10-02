import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Integer
from app.core.database import Base

class OrphanFile(Base):
    __tablename__ = "orphan_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String(512), nullable=False, index=True)
    storage_backend = Column(String(50), nullable=False, default="local")
    status = Column(String(50), nullable=False, default="pending", index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
