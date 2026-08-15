import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, Boolean
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.config import settings

_IS_PG = settings.DATABASE_URL.startswith("postgresql")

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False) # 'sent', 'failed'
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    sent_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
