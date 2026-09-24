"""
Reusable pagination utilities for MedNarrate admin endpoints.

All list endpoints should use these helpers for a consistent pagination contract:
{
    "items": [...],
    "total": N,
    "page": P,
    "limit": L,
    "has_next": bool,
    "has_previous": bool
}
"""

from typing import Any, Dict, List

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


def clamp_limit(limit: int) -> int:
    """Ensure limit is within safe bounds."""
    return min(max(1, limit), MAX_LIMIT)


def build_pagination_response(
    items: List[Any], total: int, page: int, limit: int
) -> Dict[str, Any]:
    """Build a consistent pagination response envelope."""
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "has_next": (page * limit) < total,
        "has_previous": page > 1,
    }


def page_to_offset(page: int, limit: int) -> int:
    """Convert 1-indexed page number to SQL offset."""
    return (page - 1) * limit
