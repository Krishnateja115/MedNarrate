from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.models.help_center import ArticleStatus, HelpArticle
from app.services.audit import log_admin_action

router = APIRouter()


class HelpArticleCreate(BaseModel):
    title: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255)
    category: str = Field(..., max_length=100)
    content: str
    status: ArticleStatus = ArticleStatus.draft


class HelpArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    status: Optional[ArticleStatus] = None


@router.get("")
async def list_articles(
    status: Optional[ArticleStatus] = None,
    category: Optional[str] = None,
    admin_ctx: AdminContext = Depends(require_permission("help_center.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(HelpArticle).order_by(HelpArticle.updated_at.desc())
    if status:
        stmt = stmt.where(HelpArticle.status == status)
    if category:
        stmt = stmt.where(HelpArticle.category == category)

    result = await db.execute(stmt)
    articles = result.scalars().all()

    return {
        "status": "ok",
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "slug": a.slug,
                "category": a.category,
                "status": a.status,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
            }
            for a in articles
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: HelpArticleCreate,
    admin_ctx: AdminContext = Depends(require_permission("help_center.manage")),
    db: AsyncSession = Depends(get_db),
):
    # Check if slug exists
    exists = (
        (await db.execute(select(HelpArticle).where(HelpArticle.slug == payload.slug)))
        .scalars()
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Slug already exists")

    article = HelpArticle(
        title=payload.title,
        slug=payload.slug,
        category=payload.category,
        content=payload.content,
        status=payload.status,
        created_by=str(admin_ctx.user.id),
    )
    db.add(article)

    await log_admin_action(
        db=db,
        action="HELP_ARTICLE_CREATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="HelpArticle",
        resource_id=article.id,
        metadata={"slug": article.slug},
    )
    await db.commit()
    return {"status": "ok", "article_id": article.id}


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    admin_ctx: AdminContext = Depends(require_permission("help_center.view")),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "status": "ok",
        "article": {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "category": article.category,
            "content": article.content,
            "status": article.status,
            "created_by": article.created_by,
            "updated_by": article.updated_by,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        },
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

    if payload.title is not None:
        article.title = payload.title
    if payload.slug is not None:
        article.slug = payload.slug
    if payload.category is not None:
        article.category = payload.category
    if payload.content is not None:
        article.content = payload.content
    if payload.status is not None:
        article.status = payload.status

    article.updated_by = str(admin_ctx.user.id)

    await log_admin_action(
        db=db,
        action="HELP_ARTICLE_UPDATE",
        actor_admin_id=admin_ctx.user.id,
        resource_type="HelpArticle",
        resource_id=article.id,
    )
    await db.commit()
    return {"status": "ok"}
