import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Integer
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    patient = "patient"
    clinician = "clinician"
    caregiver = "caregiver"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.patient)
    preferred_language: Mapped[str] = mapped_column(String, default="en")
    date_of_birth: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    mfa_recovery_codes: Mapped[str | None] = mapped_column(String, nullable=True)
    session_version: Mapped[int] = mapped_column(Integer, default=1, server_default='1', nullable=False)
    last_totp_counter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default='0', nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    support_tickets = relationship(
        "SupportTicket",
        back_populates="user",
        foreign_keys="[SupportTicket.user_id]",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
