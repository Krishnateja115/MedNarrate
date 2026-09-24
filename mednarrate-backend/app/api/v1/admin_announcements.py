import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, require_permission
from app.core.database import get_db
from app.models.announcement import Announcement
from app.services.audit import log_admin_action

router = APIRouter()


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=3)
    message: str = Field(..., min_length=5)
    audience: str = Field(
        default="all", example="patients"
    )  # all, patients, doctors, caregivers
    language: str = Field(default="en", example="en")
    start_time: datetime
    end_time: datetime
    status: str = Field(
        default="published", example="published"
    )  # draft, scheduled, published, expired


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    audience: Optional[str] = None
    language: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None


@router.get("/announcements")
async def list_announcements(
    request: Request,
    audience: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("announcements:read")),
):
    query = select(Announcement).order_by(desc(Announcement.created_at))
    if audience:
        query = query.where(Announcement.audience == audience)
    if status:
        query = query.where(Announcement.status == status)

    res = await db.execute(query)
    announcements = res.scalars().all()

    items = []
    for a in announcements:
        items.append(
            {
                "id": str(a.id),
                "title": a.title,
                "message": a.message,
                "audience": a.audience,
                "language": a.language,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )

    return {"announcements": items}


@router.post("/announcements")
async def create_announcement(
    payload: AnnouncementCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("announcements:manage")),
):
    start = (
        payload.start_time.replace(tzinfo=None)
        if payload.start_time.tzinfo
        else payload.start_time
    )
    end = (
        payload.end_time.replace(tzinfo=None)
        if payload.end_time.tzinfo
        else payload.end_time
    )

    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    ann = Announcement(
        id=uuid.uuid4(),
        title=payload.title,
        message=payload.message,
        audience=payload.audience,
        language=payload.language,
        start_time=start,
        end_time=end,
        status=payload.status,
        created_by_id=admin_ctx.user_id,
    )

    db.add(ann)
    await db.commit()
    await db.refresh(ann)

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="announcement_create",
        resource_type="announcement",
        resource_id=str(ann.id),
        permission_used="announcements:manage",
        result="success",
        reason=f"Created announcement '{ann.title}'",
        request=request,
        metadata={"title": ann.title, "audience": ann.audience, "status": ann.status},
    )

    return {
        "message": "Announcement created successfully",
        "announcement": {"id": str(ann.id), "title": ann.title},
    }


@router.put("/announcements/{ann_id}")
async def update_announcement(
    ann_id: str,
    payload: AnnouncementUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("announcements:manage")),
):
    try:
        a_uuid = uuid.UUID(ann_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid announcement ID format")

    res = await db.execute(select(Announcement).where(Announcement.id == a_uuid))
    ann = res.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if payload.title is not None:
        ann.title = payload.title
    if payload.message is not None:
        ann.message = payload.message
    if payload.audience is not None:
        ann.audience = payload.audience
    if payload.language is not None:
        ann.language = payload.language
    if payload.start_time is not None:
        ann.start_time = (
            payload.start_time.replace(tzinfo=None)
            if payload.start_time.tzinfo
            else payload.start_time
        )
    if payload.end_time is not None:
        ann.end_time = (
            payload.end_time.replace(tzinfo=None)
            if payload.end_time.tzinfo
            else payload.end_time
        )
    if payload.status is not None:
        ann.status = payload.status

    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="announcement_update",
        resource_type="announcement",
        resource_id=str(ann.id),
        permission_used="announcements:manage",
        result="success",
        reason=f"Updated announcement '{ann.title}'",
        request=request,
        metadata={"title": ann.title, "status": ann.status},
    )

    return {
        "message": "Announcement updated successfully",
        "announcement": {"id": str(ann.id), "title": ann.title},
    }


@router.delete("/announcements/{ann_id}")
async def delete_announcement(
    ann_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("announcements:manage")),
):
    try:
        a_uuid = uuid.UUID(ann_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid announcement ID format")

    res = await db.execute(select(Announcement).where(Announcement.id == a_uuid))
    ann = res.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")

    title = ann.title
    await db.delete(ann)
    await db.commit()

    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="announcement_delete",
        resource_type="announcement",
        resource_id=ann_id,
        permission_used="announcements:manage",
        result="success",
        reason=f"Deleted announcement '{title}'",
        request=request,
        metadata={"title": title},
    )

    return {"message": f"Announcement '{title}' deleted successfully"}


# Public Active Announcements Endpoint for App / Mobile Users
@router.get("/announcements/active/public")
async def get_active_public_announcements(
    audience: Optional[str] = Query("all"),
    language: Optional[str] = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = (
        select(Announcement)
        .where(
            and_(
                Announcement.status == "published",
                Announcement.start_time <= now,
                Announcement.end_time >= now,
                Announcement.audience.in_(["all", audience]),
                Announcement.language == language,
            )
        )
        .order_by(desc(Announcement.start_time))
    )

    res = await db.execute(stmt)
    announcements = res.scalars().all()

    return {
        "active_announcements": [
            {
                "id": str(a.id),
                "title": a.title,
                "message": a.message,
                "audience": a.audience,
                "language": a.language,
                "start_time": a.start_time.isoformat(),
                "end_time": a.end_time.isoformat(),
            }
            for a in announcements
        ]
    }
