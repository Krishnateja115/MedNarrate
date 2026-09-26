import re
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_any_permission, require_permission
from app.core.database import get_db
from app.models.help_center import ArticleStatus, HelpArticle, HelpArticleVersion
from app.models.user import User
from app.services.audit import log_admin_action

router = APIRouter()

HELP_ARTICLE_CATEGORIES = (
    "Account",
    "Reports",
    "Report Analysis",
    "AI/Chat",
    "RAG",
    "Notifications",
    "Medication Reminders",
    "Security",
    "Privacy",
    "Troubleshooting",
)
HelpArticleCategory = Literal[
    "Account",
    "Reports",
    "Report Analysis",
    "AI/Chat",
    "RAG",
    "Notifications",
    "Medication Reminders",
    "Security",
    "Privacy",
    "Troubleshooting",
]
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class HelpArticleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=255)
    category: HelpArticleCategory
    summary: str = Field(..., min_length=10, max_length=500)
    content: str = Field(..., min_length=20)
    status: ArticleStatus = ArticleStatus.draft

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not SLUG_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Slug must contain lowercase letters, numbers, and hyphens"
            )
        return normalized


class HelpArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    slug: Optional[str] = Field(None, min_length=3, max_length=255)
    category: Optional[HelpArticleCategory] = None
    summary: Optional[str] = Field(None, min_length=10, max_length=500)
    content: Optional[str] = Field(None, min_length=20)
    status: Optional[ArticleStatus] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if not SLUG_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Slug must contain lowercase letters, numbers, and hyphens"
            )
        return normalized


def _serialize_article(article: HelpArticle, author: Optional[User] = None) -> dict:
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "category": article.category,
        "summary": article.summary,
        "content": article.content,
        "status": article.status,
        "author": author.full_name if author else "MedNarrate",
        "author_id": article.created_by,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "published_at": article.published_at,
    }


async def _load_authors(
    articles: list[HelpArticle], db: AsyncSession
) -> dict[str, User]:
    author_ids: list[uuid.UUID] = []
    for article in articles:
        try:
            author_ids.append(uuid.UUID(article.created_by))
        except (TypeError, ValueError):
            continue
    if not author_ids:
        return {}
    authors = (
        (await db.execute(select(User).where(User.id.in_(author_ids)))).scalars().all()
    )
    return {str(author.id): author for author in authors}


@router.get("")
async def list_articles(
    article_status: Optional[ArticleStatus] = Query(None, alias="status"),
    category: Optional[HelpArticleCategory] = None,
    search: Optional[str] = Query(None, min_length=1, max_length=200),
    admin_ctx: AdminContext = Depends(
        require_any_permission(["help_center.view", "support.manage"])
    ),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(HelpArticle).order_by(HelpArticle.updated_at.desc())
    if article_status:
        stmt = stmt.where(HelpArticle.status == article_status)
    if category:
        stmt = stmt.where(HelpArticle.category == category)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                HelpArticle.title.ilike(term),
                HelpArticle.slug.ilike(term),
                HelpArticle.summary.ilike(term),
                HelpArticle.content.ilike(term),
            )
        )

    articles = (await db.execute(stmt)).scalars().all()
    authors = await _load_authors(articles, db)
    return {
        "status": "ok",
        "categories": list(HELP_ARTICLE_CATEGORIES),
        "articles": [
            _serialize_article(article, authors.get(article.created_by))
            for article in articles
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: HelpArticleCreate,
    admin_ctx: AdminContext = Depends(require_permission("help_center.manage")),
    db: AsyncSession = Depends(get_db),
):
    exists = (
        await db.execute(select(HelpArticle.id).where(HelpArticle.slug == payload.slug))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Slug already exists")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    article = HelpArticle(
        **payload.model_dump(),
        created_by=str(admin_ctx.user.id),
        published_at=now if payload.status == ArticleStatus.published else None,
    )
    db.add(article)
    await db.flush()
    await log_admin_action(
        db=db,
        action="HELP_ARTICLE_CREATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="HelpArticle",
        resource_id=article.id,
        permission_used="help_center.manage",
        metadata={"slug": article.slug, "status": article.status.value},
    )
    await db.commit()
    await db.refresh(article)
    return {"status": "ok", "article": _serialize_article(article, admin_ctx.user)}


@router.get("/{article_id}/versions")
async def list_article_versions(
    article_id: str,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["help_center.view", "support.manage"])
    ),
    db: AsyncSession = Depends(get_db),
):
    if not await db.get(HelpArticle, article_id):
        raise HTTPException(status_code=404, detail="Article not found")
    versions = (
        (
            await db.execute(
                select(HelpArticleVersion)
                .where(HelpArticleVersion.article_id == article_id)
                .order_by(HelpArticleVersion.version.desc())
            )
        )
        .scalars()
        .all()
    )
    return {
        "status": "ok",
        "versions": [
            {
                "id": version.id,
                "version": version.version,
                "title": version.title,
                "slug": version.slug,
                "category": version.category,
                "summary": version.summary,
                "content": version.content,
                "status": version.status,
                "created_by": version.created_by,
                "created_at": version.created_at,
            }
            for version in versions
        ],
    }


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    admin_ctx: AdminContext = Depends(
        require_any_permission(["help_center.view", "support.manage"])
    ),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    authors = await _load_authors([article], db)
    return {
        "status": "ok",
        "article": _serialize_article(article, authors.get(article.created_by)),
    }


@router.patch("/{article_id}")
async def update_article(
    article_id: str,
    payload: HelpArticleUpdate,
    admin_ctx: AdminContext = Depends(require_permission("help_center.manage")),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return {"status": "ok", "article": _serialize_article(article)}
    if "slug" in changes and changes["slug"] != article.slug:
        slug_exists = (
            await db.execute(
                select(HelpArticle.id).where(HelpArticle.slug == changes["slug"])
            )
        ).scalar_one_or_none()
        if slug_exists:
            raise HTTPException(status_code=409, detail="Slug already exists")

    next_version = (
        await db.execute(
            select(func.coalesce(func.max(HelpArticleVersion.version), 0) + 1).where(
                HelpArticleVersion.article_id == article.id
            )
        )
    ).scalar_one()
    db.add(
        HelpArticleVersion(
            article_id=article.id,
            version=next_version,
            title=article.title,
            slug=article.slug,
            category=article.category,
            summary=article.summary,
            content=article.content,
            status=article.status,
            created_by=str(admin_ctx.user.id),
        )
    )

    previous_status = article.status
    for field, value in changes.items():
        setattr(article, field, value)
    if "status" in changes:
        if (
            changes["status"] == ArticleStatus.published
            and previous_status != ArticleStatus.published
        ):
            article.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        elif changes["status"] != ArticleStatus.published:
            article.published_at = None
    article.updated_by = str(admin_ctx.user.id)

    await log_admin_action(
        db=db,
        action="HELP_ARTICLE_UPDATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="HelpArticle",
        resource_id=article.id,
        permission_used="help_center.manage",
        metadata={"fields": sorted(changes.keys())},
    )
    await db.commit()
    await db.refresh(article)
    return {"status": "ok", "article": _serialize_article(article, admin_ctx.user)}
