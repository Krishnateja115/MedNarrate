import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.config import settings

_IS_PG = settings.DATABASE_URL.startswith("postgresql")

class ReportTranslation(Base):
    __tablename__ = "report_translations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('report_id', 'language_code', name='_report_translation_lang_uc'),
    )
