# Admin Immediate Actions

## Completed

1. Repaired Admin Detail support-ticket ORM fields and zero-ticket/nullable/authorization behavior.
2. Added direct safe admin detail API.
3. Removed Admin list and Roles list N+1 query patterns.
4. Corrected deactivate/reactivate semantics, confirmation text, cache refresh, token revocation, and audit names.
5. Added hierarchy checks, final active Super Admin protection, inactive access/refresh enforcement, and role assignment UI.
6. Fixed Roles API path and protected the built-in Super Admin role.
7. Added directional legacy permission compatibility and a complete operational permission catalog.
8. Made AI Operations show bounded errors instead of fabricated zero metrics after API failure.

## Before release PASS

| Priority | Action | Reason |
|---|---|---|
| P0 | Run the authenticated browser smoke matrix from a normal local browser session | Final CUA pass was blocked by the environment usage-limit reviewer after login page inspection |
| P1 | Build a Notifications Admin page | Backend dispatch/log/retry capability has no Admin UI |
| P1 | Replace the starter Tauri greeting shell with the shared Admin app | Desktop integration is currently a template |
| P1 | Verify/seed useful Help Center starter articles in a fresh development DB | Schema/routes exist; release content must be verified |
| P2 | Add browser-level route/error assertions and Notifications UI tests | Current coverage is primarily unit/integration |
| P2 | Clean existing Pydantic/SQLAlchemy/Fitz/deprecated SDK warnings | Non-failing maintenance work |

No action here suppresses API errors, weakens RBAC, or fabricates data.
