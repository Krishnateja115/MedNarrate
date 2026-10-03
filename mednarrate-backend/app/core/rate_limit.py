"""Centralized rate limiter.

A single slowapi ``Limiter`` instance is shared by the application and every
router so that limits, client-IP resolution and the enable switch are defined
in exactly one place.

Client identity: ``request.state.client_ip`` is resolved by the
``resolve_client_ip`` middleware in ``app.main`` (it honours X-Forwarded-For
only when TRUSTED_PROXY=true).  We fall back to the socket peer address, so a
spoofed X-Forwarded-For header cannot be used to dodge limits.

Note: storage is in-process memory.  For multi-worker / multi-replica
deployments set ``RATE_LIMIT_STORAGE_URI`` (e.g. redis://...) so counters are
shared.
"""
import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

SENSITIVE_LIMIT = settings.RATE_LIMIT_SENSITIVE
REFRESH_LIMIT = settings.RATE_LIMIT_REFRESH


def client_key(request: Request) -> str:
    ip = getattr(request.state, "client_ip", None)
    return ip or get_remote_address(request)


limiter = Limiter(
    key_func=client_key,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=os.environ.get("RATE_LIMIT_STORAGE_URI") or "memory://",
)
