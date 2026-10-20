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


# Columns that must never drive an ordering, because the resulting order leaks them.
_UNSORTABLE_COLUMNS = frozenset(
    {"hashed_password", "mfa_secret", "mfa_recovery_codes", "encrypted_value", "api_key", "token_hash", "secret"}
)


def resolve_sort_column(model: Any, sort_by: str | None, default: Any) -> Any:
    """Return the model column named by ``sort_by`` or ``default``.

    Only real table columns qualify. Anything else (``metadata``, ``registry``, dunder names,
    relationships) falls back to ``default`` instead of raising, and secret columns are refused.
    """
    columns = getattr(getattr(model, "__table__", None), "columns", None)
    if not sort_by or columns is None or sort_by not in columns or sort_by in _UNSORTABLE_COLUMNS:
        return default
    return getattr(model, sort_by)


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
