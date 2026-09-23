import logging
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.admin import AdminAuditLog
from app.core.config import settings

logger = logging.getLogger(__name__)

# Keys that should never be stored in the audit log metadata
SENSITIVE_KEYS = {"password", "secret", "token", "key", "authorization", "ssn", "medical_record"}

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively strip sensitive data from metadata."""
    if not isinstance(metadata, dict):
        return metadata

    sanitized = {}
    for k, v in metadata.items():
        if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_metadata(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_metadata(i) if isinstance(i, dict) else i for i in v]
        else:
            sanitized[k] = v
    return sanitized

async def log_admin_action(
    db: AsyncSession,
    action: str,
    actor_admin_id: Optional[uuid.UUID],
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    permission_used: Optional[str] = None,
    result: str = "success",
    reason: Optional[str] = None,
    request: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None,
    sensitive_access_flag: bool = False
) -> AdminAuditLog:
    """
    Append an immutable audit log entry.
    """
    ip_address = None
    user_agent = None
    request_id = None

    if request:
        ip_address = request.client.host if request.client else None
        # Forwarded for header
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
            
        user_agent = request.headers.get("user-agent")
        # Support common request ID patterns if middleware injects them
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    safe_metadata = sanitize_metadata(metadata or {})

    audit_entry = AdminAuditLog(
        actor_admin_id=actor_admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        permission_used=permission_used,
        result=result,
        reason=reason,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_payload=safe_metadata,
        sensitive_access_flag=sensitive_access_flag,
        timestamp=datetime.now(timezone.utc)
    )

    db.add(audit_entry)
    
    # We purposefully don't commit here so that the audit log is committed
    # atomically with the action itself in the endpoint. If the endpoint fails and rolls back,
    # the success log rolls back. The endpoint should explicitly catch errors and log failures.
    
    return audit_entry
