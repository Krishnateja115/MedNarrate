import uuid
from datetime import datetime

from sqlalchemy import JSON as JSONB
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.database import Base

_IS_PG = settings.DATABASE_URL.startswith("postgresql")

if _IS_PG:

    def _json_col():
        return mapped_column(JSONB, default=list)
else:
    from sqlalchemy import JSON

    def _json_col():
        return mapped_column(JSON, default=list)


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    medication_name: Mapped[str] = mapped_column(String, nullable=False)
    dosage: Mapped[str] = mapped_column(String, nullable=True)
    frequency: Mapped[str] = mapped_column(String, nullable=True)
    times_of_day: Mapped[list] = _json_col()
    duration_days: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime, default=datetime.utcnow)
