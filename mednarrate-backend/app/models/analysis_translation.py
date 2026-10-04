import uuid
from datetime import datetime

from sqlalchemy import JSON as JSONB
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

TRANSLATION_SCHEMA_VERSION: int = 3


class AnalysisTranslation(Base):
    __tablename__ = "analysis_translations"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("report_analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    clinician_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    patient_summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings_json: Mapped[list] = mapped_column(JSONB, default=list)
    medications_json: Mapped[list] = mapped_column(JSONB, default=list)
    doctor_discussion_points: Mapped[list] = mapped_column(JSONB, default=list)
    ui_labels: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("report_analysis_id", "language", name="_report_lang_uc"),
    )
