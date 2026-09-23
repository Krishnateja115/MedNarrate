from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.admin_auth import AdminContext, require_permission
from app.models.incidents import Incident, IncidentStatus, IncidentSeverity, IncidentEvent

router = APIRouter()

class IncidentCreate(BaseModel):
    title: str
    severity: IncidentSeverity
    affected_service: Optional[str] = None
    summary: Optional[str] = None

class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    resolution: Optional[str] = None
    message: Optional[str] = None

@router.get("")
async def get_incidents(
    admin_ctx: AdminContext = Depends(require_permission("incidents.view")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    stmt = select(Incident).order_by(desc(Incident.started_at)).offset(offset).limit(limit)
    incidents = (await db.execute(stmt)).scalars().all()
    
    return {
        "status": "ok",
        "incidents": [
            {
                "id": i.id,
                "title": i.title,
                "severity": i.severity,
                "status": i.status,
                "affected_service": i.affected_service,
                "started_at": i.started_at.isoformat(),
                "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
                "created_by_id": i.created_by_id,
                "assigned_to_id": i.assigned_to_id,
                "summary": i.summary,
                "resolution": i.resolution
            } for i in incidents
        ],
        "pagination": {
            "limit": limit,
            "offset": offset
        }
    }

@router.get("/{incident_id}")
async def get_incident(
    incident_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("incidents.view")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = (await db.execute(stmt)).scalars().first()
    
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
        
    events_stmt = select(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.timestamp)
    events = (await db.execute(events_stmt)).scalars().all()
    
    return {
        "status": "ok",
        "incident": {
            "id": incident.id,
            "title": incident.title,
            "severity": incident.severity,
            "status": incident.status,
            "affected_service": incident.affected_service,
            "started_at": incident.started_at.isoformat(),
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "created_by_id": incident.created_by_id,
            "assigned_to_id": incident.assigned_to_id,
            "summary": incident.summary,
            "resolution": incident.resolution
        },
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "message": e.message,
                "actor_id": e.actor_id,
                "timestamp": e.timestamp.isoformat()
            } for e in events
        ]
    }

@router.post("")
async def create_incident(
    payload: IncidentCreate,
    admin_ctx: AdminContext = Depends(require_permission("incidents.manage")),
    db: AsyncSession = Depends(get_db)
):
    incident = Incident(
        title=payload.title,
        severity=payload.severity,
        affected_service=payload.affected_service,
        summary=payload.summary,
        created_by_id=admin_ctx.user.id
    )
    db.add(incident)
    await db.flush()
    
    event = IncidentEvent(
        incident_id=incident.id,
        actor_id=admin_ctx.user.id,
        event_type="CREATED",
        message="Incident created."
    )
    db.add(event)
    await db.commit()
    
    return {"status": "ok", "incident_id": incident.id}

@router.patch("/{incident_id}")
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    admin_ctx: AdminContext = Depends(require_permission("incidents.manage")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = (await db.execute(stmt)).scalars().first()
    
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
        
    messages = []
    if payload.status and incident.status != payload.status:
        incident.status = payload.status
        messages.append(f"Status changed to {payload.status.value}")
        from datetime import datetime, timezone
        if payload.status == IncidentStatus.resolved:
            incident.resolved_at = datetime.now(timezone.utc)
            
    if payload.severity and incident.severity != payload.severity:
        incident.severity = payload.severity
        messages.append(f"Severity changed to {payload.severity.value}")
        
    if payload.resolution:
        incident.resolution = payload.resolution
        messages.append("Resolution updated")
        
    if payload.message:
        messages.append(payload.message)
        
    if messages:
        event = IncidentEvent(
            incident_id=incident.id,
            actor_id=admin_ctx.user.id,
            event_type="UPDATED",
            message=" | ".join(messages)
        )
        db.add(event)
        
    await db.commit()
    return {"status": "ok"}
