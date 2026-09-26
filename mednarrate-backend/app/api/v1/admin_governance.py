"""Operational control-center snapshot backed by live MedNarrate data."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin_health import get_system_health
from app.core.admin_auth import AdminContext, require_any_permission
from app.core.database import get_db
from app.models.admin import AdminAuditLog, SensitiveAccessGrant
from app.models.incidents import Incident, IncidentStatus
from app.models.job_execution import JobExecution, JobStatus
from app.models.support import SupportTicket, TicketPriority, TicketStatus
from app.models.system_setting import MaintenanceMode
from app.models.user import User
from app.services.audit import log_admin_action

router = APIRouter()

OPEN_INCIDENT_STATUSES = (
    IncidentStatus.open,
    IncidentStatus.investigating,
    IncidentStatus.identified,
)
OPEN_TICKET_STATUSES = (
    TicketStatus.new,
    TicketStatus.triaged,
    TicketStatus.investigating,
    TicketStatus.waiting_user,
    TicketStatus.waiting_eng,
)
GOVERNANCE_ACTIONS = (
    "ROLE_CHANGE",
    "PERMISSION_CHANGE",
    "ai_config_update",
    "feature_flag_create",
    "feature_flag_update",
    "feature_flag_delete",
    "maintenance_mode_enable",
    "maintenance_mode_disable",
    "announcement_create",
    "announcement_update",
    "announcement_delete",
    "break_glass_requested",
    "break_glass_approved",
    "break_glass_revoked",
    "FORCE_LOGOUT_ADMIN",
    "DEACTIVATE_ADMIN",
    "REACTIVATE_ADMIN",
)


def _serialize_incident(incident: Incident) -> dict:
    return {
        "id": str(incident.id),
        "title": incident.title,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "affected_service": incident.affected_service,
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
    }


@router.get("/overview")
async def get_governance_overview(
    request: Request,
    admin_ctx: AdminContext = Depends(
        require_any_permission(
            ["dashboard.view", "security.view", "system.health.view"]
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Return live operational attention items and recent privileged activity."""
    health = await get_system_health(admin_ctx=admin_ctx, db=db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    failed_jobs_since = now - timedelta(hours=24)

    open_incidents = (
        (
            await db.execute(
                select(Incident)
                .where(Incident.status.in_(OPEN_INCIDENT_STATUSES))
                .order_by(Incident.severity, desc(Incident.created_at))
                .limit(10)
            )
        )
        .scalars()
        .all()
    )

    failed_jobs = (
        (
            await db.execute(
                select(JobExecution)
                .where(
                    JobExecution.status == JobStatus.failed,
                    JobExecution.started_at >= failed_jobs_since,
                )
                .order_by(desc(JobExecution.started_at))
                .limit(10)
            )
        )
        .scalars()
        .all()
    )

    pending_grants = (
        (
            await db.execute(
                select(SensitiveAccessGrant)
                .where(SensitiveAccessGrant.status == "requested")
                .order_by(desc(SensitiveAccessGrant.created_at))
                .limit(10)
            )
        )
        .scalars()
        .all()
    )

    critical_tickets = await db.scalar(
        select(func.count(SupportTicket.id)).where(
            SupportTicket.status.in_(OPEN_TICKET_STATUSES),
            SupportTicket.priority.in_([TicketPriority.p1, TicketPriority.p2]),
        )
    )

    maintenance = (
        (
            await db.execute(
                select(MaintenanceMode)
                .order_by(desc(MaintenanceMode.enabled_at))
                .limit(1)
            )
        )
        .scalars()
        .first()
    )

    activity = (
        (
            await db.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.action.in_(GOVERNANCE_ACTIONS))
                .order_by(desc(AdminAuditLog.timestamp))
                .limit(20)
            )
        )
        .scalars()
        .all()
    )
    actor_ids = {entry.actor_admin_id for entry in activity if entry.actor_admin_id}
    actor_emails: dict[str, str] = {}
    if actor_ids:
        actors = (
            await db.execute(select(User).where(User.id.in_(actor_ids)))
        ).scalars()
        actor_emails = {str(actor.id): actor.email for actor in actors}

    degraded_services = [
        {"name": name, **service}
        for name, service in health.get("services", {}).items()
        if service.get("status") != "healthy"
    ]
    services = health.get("services", {})
    services["notifications"] = {
        "status": "not_monitored",
        "last_checked": health.get("timestamp"),
        "error_summary": "No live notification-delivery probe is implemented.",
    }

    await log_admin_action(
        db=db,
        action="VIEW_GOVERNANCE_OVERVIEW",
        actor_admin_id=admin_ctx.user.id,
        permission_used="dashboard.view",
        request=request,
    )
    await db.commit()

    return {
        "status": health.get("status", "unknown"),
        "generated_at": health.get("timestamp"),
        "services": services,
        "active_incidents": [
            _serialize_incident(incident) for incident in open_incidents
        ],
        "pending_actions": {
            "critical_tickets": critical_tickets or 0,
            "failed_jobs_24h": [
                {
                    "id": str(job.id),
                    "name": job.job_name,
                    "failure_category": job.failure_category,
                    "started_at": (
                        job.started_at.isoformat() if job.started_at else None
                    ),
                }
                for job in failed_jobs
            ],
            "pending_sensitive_access": [
                {
                    "id": str(grant.id),
                    "resource_type": grant.resource_type,
                    "created_at": (
                        grant.created_at.isoformat() if grant.created_at else None
                    ),
                }
                for grant in pending_grants
            ],
            "degraded_services": degraded_services,
        },
        "maintenance": {
            "is_enabled": bool(maintenance and maintenance.is_enabled),
            "scope": maintenance.scope if maintenance else None,
            "enabled_at": (
                maintenance.enabled_at.isoformat()
                if maintenance and maintenance.enabled_at
                else None
            ),
        },
        "recent_activity": [
            {
                "id": str(entry.id),
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "action": entry.action,
                "result": entry.result,
                "actor_email": actor_emails.get(str(entry.actor_admin_id), "System"),
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "reason": entry.reason,
            }
            for entry in activity
        ],
    }
