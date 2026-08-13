import uuid
from sqlalchemy import String, Text, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.config import settings
from app.core.database import Base

# Use PostgreSQL-native UUID+JSONB+Vector when connected to Postgres;
# fall back to generic String/JSON for SQLite dev.
_IS_PG = settings.DATABASE_URL.startswith("postgresql")

if _IS_PG:
    from sqlalchemy.dialects.postgresql import UUID as _UUID, JSONB as _JSONB
    from pgvector.sqlalchemy import Vector as _Vector
    _id_col   = lambda: mapped_column(_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    _emb_col  = lambda: mapped_column(_Vector(768), nullable=True)
    _meta_col = lambda: mapped_column(_JSONB, default=dict)
else:
    _id_col   = lambda: mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    _emb_col  = lambda: mapped_column(JSON, nullable=True)
    _meta_col = lambda: mapped_column(JSON, default=dict)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id:            Mapped[str]   = _id_col()
    source:        Mapped[str]   = mapped_column(String)
    content:       Mapped[str]   = mapped_column(Text)
    content_hash:  Mapped[str]   = mapped_column(String, unique=True, index=True)
    embedding:     Mapped[object] = _emb_col()
    metadata_json: Mapped[object] = _meta_col()
    created_at:    Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
