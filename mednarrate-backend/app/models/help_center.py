import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String, Text

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
    content = Column(Text, nullable=False)
    status = Column(Enum(ArticleStatus), nullable=False, default=ArticleStatus.draft)

    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
