from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import String, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import AdminContext, get_admin_context
from app.core.database import get_db
from app.models.admin import AdminAuditLog
from app.models.incidents import Incident
from app.models.report import Report
from app.models.support import SupportTicket
from app.models.user import User

router = APIRouter()


@router.get("")
async def global_admin_search(
    request: Request,
    q: str = Query(
        ...,
        min_length=1,
        description="Search term across users, reports, tickets, incidents, audit logs",
    ),
    limit: int = Query(20, ge=1, le=50),
    admin_ctx: AdminContext = Depends(get_admin_context),
    db: AsyncSession = Depends(get_db),
):
    query_str = q.strip()
    results: List[Dict[str, Any]] = []

    # 1. Users Search (if authorized)
    if admin_ctx.has_permission("users.view") or admin_ctx.has_permission("admin"):
        user_stmt = (
            select(User)
            .where(
                or_(
                    User.email.ilike(f"%{query_str}%"),
                    User.full_name.ilike(f"%{query_str}%"),
                    cast(User.id, String) == query_str,
                )
            )
            .limit(limit)
        )
        users = (await db.execute(user_stmt)).scalars().all()
        for u in users:
            results.append(
                {
                    "type": "user",
                    "id": str(u.id),
                    "title": u.full_name or u.email,
                    "subtitle": u.email,
                    "status": u.role.value if hasattr(u.role, "value") else str(u.role),
                    "timestamp": u.created_at.isoformat() if u.created_at else None,
                    "url": f"/users/{u.id}",
                }
            )

    # 2. Reports Search (if authorized)
    if admin_ctx.has_permission("reports.view") or admin_ctx.has_permission("admin"):
        rep_stmt = (
            select(Report)
            .where(
                or_(
                    Report.title.ilike(f"%{query_str}%"),
                    Report.file_name.ilike(f"%{query_str}%"),
                    cast(Report.id, String) == query_str,
                )
            )
            .limit(limit)
        )
        reports = (await db.execute(rep_stmt)).scalars().all()
        for r in reports:
            p_status = (
                r.processing_status.value
                if hasattr(r.processing_status, "value")
                else str(r.processing_status)
            )
            r_type = (
                r.report_type.value
                if hasattr(r.report_type, "value")
                else str(r.report_type)
            )
            results.append(
                {
                    "type": "report",
                    "id": str(r.id),
                    "title": r.title or r.file_name or f"Report #{r.id}",
                    "subtitle": f"Type: {r_type}",
                    "status": p_status,
                    "timestamp": r.uploaded_at.isoformat() if r.uploaded_at else None,
                    "url": f"/reports/{r.id}",
                }
            )

    # 3. Support Tickets Search (if authorized)
    if admin_ctx.has_permission("support.view") or admin_ctx.has_permission("admin"):
        tkt_stmt = (
            select(SupportTicket)
            .where(
                or_(
                    SupportTicket.title.ilike(f"%{query_str}%"),
                    SupportTicket.description.ilike(f"%{query_str}%"),
                    cast(SupportTicket.id, String) == query_str,
                )
            )
            .limit(limit)
        )
        tickets = (await db.execute(tkt_stmt)).scalars().all()
        for t in tickets:
            t_status = t.status.value if hasattr(t.status, "value") else str(t.status)
            results.append(
                {
                    "type": "ticket",
                    "id": str(t.id),
                    "title": t.title,
                    "subtitle": f"Ticket #{str(t.id)[:8]}",
                    "status": t_status,
                    "timestamp": t.created_at.isoformat() if t.created_at else None,
                    "url": f"/support/{t.id}",
                }
            )

    # 4. Incidents Search (if authorized)
    if admin_ctx.has_permission("system.view") or admin_ctx.has_permission("admin"):
        inc_stmt = (
            select(Incident)
            .where(
                or_(
                    Incident.title.ilike(f"%{query_str}%"),
                    Incident.affected_service.ilike(f"%{query_str}%"),
                    cast(Incident.id, String) == query_str,
                )
            )
            .limit(limit)
        )
        incidents = (await db.execute(inc_stmt)).scalars().all()
        for inc in incidents:
            inc_status = (
                inc.status.value if hasattr(inc.status, "value") else str(inc.status)
            )
            results.append(
                {
                    "type": "incident",
                    "id": str(inc.id),
                    "title": inc.title,
                    "subtitle": f"Service: {inc.affected_service or 'N/A'}",
                    "status": inc_status,
                    "timestamp": inc.created_at.isoformat() if inc.created_at else None,
                    "url": "/incidents",
                }
            )

    # 5. Audit Logs Search (if authorized)
    if admin_ctx.has_permission("audit.view") or admin_ctx.has_permission("admin"):
        audit_stmt = (
            select(AdminAuditLog)
            .where(
                or_(
                    AdminAuditLog.action.ilike(f"%{query_str}%"),
                    AdminAuditLog.request_id == query_str,
                )
            )
            .limit(limit)
        )
        logs = (await db.execute(audit_stmt)).scalars().all()
        for log in logs:
            results.append(
                {
                    "type": "audit",
                    "id": str(log.id),
                    "title": log.action,
                    "subtitle": f"Request ID: {log.request_id or 'N/A'}",
                    "status": log.severity,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "url": "/audit",
                }
            )

    return {
        "status": "ok",
        "query": query_str,
        "total_results": len(results),
        "results": results[:limit],
    }
