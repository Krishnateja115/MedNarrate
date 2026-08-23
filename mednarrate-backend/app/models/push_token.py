import uuid
from sqlalchemy import String, Text, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.config import settings

_IS_PG = settings.DATABASE_URL.startswith("postgresql")

class PushToken(Base):
    __tablename__ = "push_tokens"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) if _IS_PG else String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_token: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False) # 'ios' or 'android'
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'device_token', name='_user_device_token_uc'),
    )
