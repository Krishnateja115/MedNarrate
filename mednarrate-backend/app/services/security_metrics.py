"""Database-backed Security Center metrics.

The Security Center deliberately distinguishes enabled administrator accounts from
currently valid sessions.  An "active administrator" is an account whose role is
``admin`` and whose ``is_active`` flag is true; it does not imply recent login.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAuditLog, SensitiveAccessGrant
from app.models.privacy import PrivacyDataRequest
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

SECURITY_EVENT_ACTIONS = (
    "ADMIN_LOGIN_SUCCESS",
    "FAILED_ADMIN_LOGIN",
    "ADMIN_LOGOUT",
    "SESSION_REVOCATION",
    "FORCE_LOGOUT_ADMIN",
    "CREATE_ADMIN",
    "DEACTIVATE_ADMIN",
    "REACTIVATE_ADMIN",
    "ROLE_CHANGE",
    "PERMISSION_CHANGE",
    "SUSPICIOUS_ACCESS",
    "BREAK_GLASS_ACCESS",
)


async def get_security_metrics(db: AsyncSession) -> dict[str, int]:
    """Return Security Center counts derived directly from current database rows."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    total_admins = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.admin)
    )
    active_admins = await db.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.admin,
            User.is_active.is_(True),
        )
    )
    suspended_admins = await db.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.admin,
            User.is_active.is_(False),
        )
    )
    active_sessions = await db.scalar(
        select(func.count(RefreshToken.id))
        .join(User, RefreshToken.user_id == User.id)
        .where(
            User.role == UserRole.admin,
            User.is_active.is_(True),
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
    )
    active_grants = await db.scalar(
        select(func.count(SensitiveAccessGrant.id)).where(
            SensitiveAccessGrant.status == "active"
        )
    )
    pending_privacy_requests = await db.scalar(
        select(func.count(PrivacyDataRequest.id)).where(
            PrivacyDataRequest.status.in_(["requested", "under_review"])
        )
    )
    total_security_events = await db.scalar(
        select(func.count(AdminAuditLog.id)).where(
            AdminAuditLog.action.in_(SECURITY_EVENT_ACTIONS)
        )
    )

    return {
        "total_admins": total_admins or 0,
        "active_admins": active_admins or 0,
        "suspended_admins": suspended_admins or 0,
        "active_sessions": active_sessions or 0,
        "active_breakglass_grants": active_grants or 0,
        "pending_privacy_requests": pending_privacy_requests or 0,
        "total_security_events": total_security_events or 0,
    }
