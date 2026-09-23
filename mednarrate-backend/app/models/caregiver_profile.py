from datetime import datetime
import uuid
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class CaregiverProfile(Base):
    __tablename__ = "caregiver_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    relationship: Mapped[str | None] = mapped_column(String, nullable=True)
    caregiver_role: Mapped[str | None] = mapped_column(String, nullable=True)
    supported_patient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    organization: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
