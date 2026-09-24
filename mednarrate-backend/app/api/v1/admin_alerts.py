from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, get_admin_context
from app.core.database import get_db
from app.models.incidents import Incident
from app.models.llm_telemetry import LLMDiagnosticEvent
from app.models.report import Report
from app.models.support import SupportTicket

router = APIRouter()

# In-memory acknowledged alerts tracker
_acknowledged_alerts = set()


@router.get("")
async def get_admin_alerts(
    request: Request,
    admin_ctx: AdminContext = Depends(get_admin_context),
    db: AsyncSession = Depends(get_db),
):
    alerts: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # 1. Critical Active Incidents
    inc_stmt = select(Incident).where(
        Incident.status.in_(["open", "investigating", "identified"])
    )
    incidents = (await db.execute(inc_stmt)).scalars().all()
    for inc in incidents:
        alert_id = f"inc_{inc.id}"
        sev_str = (
            inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity)
        )
        alerts.append(
            {
                "id": alert_id,
                "category": "Critical Incident",
                "severity": "critical"
                if sev_str in ["SEV-1", "SEV-2", "critical", "high"]
                else "warning",
                "title": f"Incident: {inc.title}",
                "message": f"Active {sev_str} incident on {inc.affected_service or 'core'} service.",
                "target_url": "/incidents",
                "timestamp": inc.created_at.isoformat()
                if inc.created_at
                else now.isoformat(),
                "acknowledged": alert_id in _acknowledged_alerts,
            }
        )

    # 2. Failed Reports Alert
    failed_rep_cnt = (
        await db.execute(
            select(func.count(Report.id)).where(
                Report.uploaded_at >= twenty_four_hours_ago,
                Report.processing_status.in_(["failed", "error"]),
            )
        )
    ).scalar_one_or_none() or 0
    if failed_rep_cnt > 0:
        alert_id = "failed_reports_24h"
        alerts.append(
            {
                "id": alert_id,
                "category": "Report Processing",
                "severity": "warning" if failed_rep_cnt < 5 else "critical",
                "title": "Failed Report Processing Spikes",
                "message": f"{failed_rep_cnt} medical report processing failure(s) detected in the last 24 hours.",
                "target_url": "/reports",
                "timestamp": now.isoformat(),
                "acknowledged": alert_id in _acknowledged_alerts,
            }
        )

    # 3. High Priority Open Support Tickets
    urgent_tkt_cnt = (
        await db.execute(
            select(func.count(SupportTicket.id)).where(
                SupportTicket.status == "open",
                SupportTicket.priority.in_(["p1", "p2", "urgent", "high"]),
            )
        )
    ).scalar_one_or_none() or 0
    if urgent_tkt_cnt > 0:
        alert_id = "urgent_tickets_open"
        alerts.append(
            {
                "id": alert_id,
                "category": "Support",
                "severity": "warning",
                "title": "Urgent Support Tickets",
                "message": f"{urgent_tkt_cnt} high/urgent priority support ticket(s) currently awaiting resolution.",
                "target_url": "/support",
                "timestamp": now.isoformat(),
                "acknowledged": alert_id in _acknowledged_alerts,
            }
        )

    # 4. AI LLM Telemetry Error Alert
    ai_errors_cnt = (
        await db.execute(
            select(func.count(LLMDiagnosticEvent.id)).where(
                LLMDiagnosticEvent.timestamp >= twenty_four_hours_ago,
                LLMDiagnosticEvent.status != "success",
            )
        )
    ).scalar_one_or_none() or 0
    if ai_errors_cnt > 0:
        alert_id = "ai_telemetry_errors_24h"
        alerts.append(
            {
                "id": alert_id,
                "category": "AI Operations",
                "severity": "warning",
                "title": "LLM Provider Errors",
                "message": f"{ai_errors_cnt} AI request failure(s) recorded in telemetry over past 24 hours.",
                "target_url": "/ai-ops",
                "timestamp": now.isoformat(),
                "acknowledged": alert_id in _acknowledged_alerts,
            }
        )

    # Sort alerts by severity & acknowledged status
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: (a["acknowledged"], severity_order.get(a["severity"], 3)))

    return {
        "status": "ok",
        "unread_count": sum(1 for a in alerts if not a["acknowledged"]),
        "total_count": len(alerts),
        "alerts": alerts,
    }


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str, admin_ctx: AdminContext = Depends(get_admin_context)
):
    _acknowledged_alerts.add(alert_id)
    return {
        "status": "ok",
        "message": f"Alert '{alert_id}' marked as acknowledged",
        "alert_id": alert_id,
    }
