import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy import Uuid as UUID, JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class AnalysisTranslation(Base):
    __tablename__ = "analysis_translations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("report_analyses.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    patient_summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings_json: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('report_analysis_id', 'language', name='_report_lang_uc'),
    )
