# Admin Account Security Audit

## Definitions

- Admin Account: `User` with `role == UserRole.admin`.
- Active Administrator: admin with `is_active == true`.
- Active Sessions: unrevoked, unexpired `RefreshToken` rows, counted separately.
- Last login: latest `ADMIN_LOGIN_SUCCESS` audit timestamp.
- Admin Detail IDs: `User.id` UUIDs. Assigned tickets use `SupportTicket.assigned_admin_id`.

## Controls

| Control | Backend | UI | Evidence |
|---|---|---|---|
| List/detail | batched roles, sessions, last login; safe serializer | status/roles/session table and direct detail | query-count/direct-detail tests |
| Create | validates role IDs and blocks non-Super escalation | permission-aware create | account tests |
| Deactivate | blocks self/higher privilege/final active Super; deletes refresh tokens; audits | confirmation names admin and consequence | lifecycle tests |
| Reactivate | target/hierarchy validation and audit | confirmation/cache refresh | lifecycle tests |
| Force logout | blocks self/higher privilege; deletes refresh tokens; audits | confirmation/cache refresh | lifecycle tests |
| Role assignment | validates IDs; blocks Super targeting and final-role removal | Admin Detail checkbox editor | hierarchy/role tests |
| Super Admin role | lower privilege cannot modify/rename; final active role protected | Roles UI disables built-in role | hierarchy tests |
| Access/refresh | inactive user rejected on every protected request and token refresh | session restoration cannot revive | token lifecycle tests |
| Audit | lifecycle actions use `ADMIN_CREATED`, `ADMIN_DEACTIVATED`, `ADMIN_REACTIVATED`, `ADMIN_FORCE_LOGOUT`, `ADMIN_ROLE_CHANGED` | detail/governance reads activity | audit assertions |

## Permission safety

Compatibility is directional. `break_glass.read` cannot satisfy `approve_sensitive_access` or `break_glass.revoke`; only the stronger canonical `breakglass.manage` can satisfy those compatible checks. This preserves legacy route names without granting privilege.

## Remaining security work

Automated tests cover 401/403/404, ID scoping, self-action, hierarchy, final-role protection, token revocation, and inactive enforcement. The final browser-level IDOR/RBAC matrix was blocked by the local browser-control usage-limit reviewer.
