import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, Enum as SQLEnum
import enum
from app.core.database import Base

class JobStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"

class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_name = Column(String(100), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.running)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    failure_category = Column(String(100), nullable=True)  # e.g., 'network', 'timeout', 'database'
    request_id = Column(String(50), nullable=True) # Optional correlation ID
    error_details = Column(String, nullable=True)
