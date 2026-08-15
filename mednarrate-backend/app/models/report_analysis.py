import uuid
from sqlalchemy import ForeignKey, DateTime, Text, func
from sqlalchemy import Uuid as UUID, JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class ReportAnalysis(Base):
    __tablename__ = "report_analyses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    structured_lab_values: Mapped[list] = mapped_column(JSONB, default=list)
    entities: Mapped[list] = mapped_column(JSONB, default=list)
    abnormal_findings: Mapped[list] = mapped_column(JSONB, default=list)
    evidence_sources: Mapped[list] = mapped_column(JSONB, default=list)
    clinician_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    patient_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_versions: Mapped[dict] = mapped_column(JSONB, default=dict)
    processed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
