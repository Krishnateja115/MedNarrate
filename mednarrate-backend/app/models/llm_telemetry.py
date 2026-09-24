import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LLMDiagnosticEvent(Base):
    """
    Safely captures LLM telemetry.
    Does not store raw prompts, raw outputs, or PHI.
    """

    __tablename__ = "llm_diagnostic_events"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    provider: Mapped[str] = mapped_column(String, index=True, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    feature: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'success', 'error', 'timeout'
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String, nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
