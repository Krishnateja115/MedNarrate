import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class HelpArticle(Base):
    __tablename__ = "help_articles"

    # DB column is uuid type — use SQLAlchemy UUID so asyncpg returns python uuid.UUID,
    # not asyncpg.pgproto.pgproto.UUID which breaks str() and uuid.UUID() calls downstream.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus), nullable=False, default=ArticleStatus.draft
    )

    # DB columns are uuid type — must use UUID(as_uuid=True) so the ORM returns
    # python uuid.UUID objects, not raw asyncpg UUID objects.
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    versions = relationship(
        "HelpArticleVersion", back_populates="article", cascade="all, delete-orphan"
    )
    ticket_links = relationship(
        "SupportTicketHelpArticle",
        back_populates="article",
        cascade="all, delete-orphan",
    )


class HelpArticleVersion(Base):
    __tablename__ = "help_article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version", name="uq_help_article_version"),
    )

    # DB column is uuid — align ORM
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("help_articles.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ArticleStatus] = mapped_column(Enum(ArticleStatus), nullable=False)
    # DB column is uuid
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("HelpArticle", back_populates="versions")
