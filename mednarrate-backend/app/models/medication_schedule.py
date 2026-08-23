import uuid
from sqlalchemy import String, Text, DateTime, Boolean, func, ForeignKey, Integer
from sqlalchemy import Uuid as UUID, JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.config import settings

_IS_PG = settings.DATABASE_URL.startswith("postgresql")

if _IS_PG:
    _json_col = lambda: mapped_column(JSONB, default=list)
else:
    from sqlalchemy import JSON
    _json_col = lambda: mapped_column(JSON, default=list)

class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    medication_name: Mapped[str] = mapped_column(String, nullable=False)
    dosage: Mapped[str] = mapped_column(String, nullable=True)
    frequency: Mapped[str] = mapped_column(String, nullable=True)
    times_of_day: Mapped[list] = _json_col()
    duration_days: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
