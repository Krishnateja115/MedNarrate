import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class HelpArticle(Base):
    __tablename__ = "help_articles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    summary = Column(Text, nullable=False, default="")
    content = Column(Text, nullable=False)
    status = Column(Enum(ArticleStatus), nullable=False, default=ArticleStatus.draft)

    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    published_at = Column(DateTime, nullable=True)

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

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id = Column(
        String(36), ForeignKey("help_articles.id", ondelete="CASCADE"), nullable=False
    )
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False, default="")
    content = Column(Text, nullable=False)
    status = Column(Enum(ArticleStatus), nullable=False)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("HelpArticle", back_populates="versions")
