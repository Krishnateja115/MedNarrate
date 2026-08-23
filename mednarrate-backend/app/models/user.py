import uuid, enum
from sqlalchemy import String, Boolean, Enum, DateTime, func
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class UserRole(str, enum.Enum):
    patient = "patient"
    clinician = "clinician"
    caregiver = "caregiver"

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.patient)
    preferred_language: Mapped[str] = mapped_column(String, default="en")
    date_of_birth: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
