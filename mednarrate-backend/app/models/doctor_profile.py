import uuid
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Integer
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialty: Mapped[str | None] = mapped_column(String, nullable=True)
    qualifications: Mapped[str | None] = mapped_column(String, nullable=True)
    license_number: Mapped[str | None] = mapped_column(String, nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hospital: Mapped[str | None] = mapped_column(String, nullable=True)
    professional_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
