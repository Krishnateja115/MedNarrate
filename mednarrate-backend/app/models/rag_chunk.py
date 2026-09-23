from datetime import datetime
import uuid
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Integer
from sqlalchemy import Uuid as UUID, JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.config import settings

_IS_PG = settings.DATABASE_URL.startswith("postgresql")

if _IS_PG:
    from pgvector.sqlalchemy import Vector as _Vector
    _emb_col = lambda: mapped_column(_Vector(768), nullable=True)
else:
    _emb_col = lambda: mapped_column(JSON, nullable=True)

class RagChunk(Base):
    __tablename__ = "rag_chunks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True)
    knowledge_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[object] = _emb_col()
    created_at: Mapped[object] = mapped_column(DateTime, default=datetime.utcnow)
