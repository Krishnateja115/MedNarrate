import uuid, enum
from datetime import date
from sqlalchemy import String, Text, Boolean, Date, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class FileType(str, enum.Enum):
    pdf = "pdf"
    image = "image"

class ReportType(str, enum.Enum):
    blood = "blood"
    pathology = "pathology"
    health = "health"
    other = "other"

class ProcessingStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    hospital: Mapped[str | None] = mapped_column(String, nullable=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.uploaded)
    is_favourite: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
