# MedNarrate Admin RBAC Architecture

This document describes the role-based access control (RBAC) and session architecture for the MedNarrate Admin portal. 
The system ensures secure, granular control over administrative operations.

## Core Principles
1. **Backend as the Authority**: The backend is the ultimate source of truth for all authorization checks. The frontend UI reflects permissions for user experience but does not enforce them.
2. **Ephemeral Sessions**: Admin tokens are stored strictly in `sessionStorage` (living only for the duration of the browser tab). We do not persist sensitive `admin_token` credentials across tabs in `localStorage` to reduce exposure risk.
3. **No Implicit Escalation**: Administrators cannot elevate their own roles, nor can lower-tier admins grant higher-tier privileges.

## Session Lifecycle

### Login Flow
1. Admin authenticates via `POST /api/v1/auth/login`.
2. Backend validates credentials and issues an `access_token` and `refresh_token`.
3. Frontend automatically calls `GET /api/v1/admin/me` passing the `access_token`.
4. Backend evaluates `get_admin_context` and returns the admin profile, including their `permissions` list.
5. Frontend stores the `access_token`, `refresh_token`, and user profile (with permissions) in `sessionStorage`.

### Request Authorization
- The frontend `fetchApi` client reads `sessionStorage` and attaches the `Bearer` token to all requests.
- Backend dependencies (`require_permission`, `require_any_permission`) validate the token, extract the user ID, query the `AdminRoleAssignment` table, and authorize the action.
- If the token expires or is invalid (401), the frontend clears `sessionStorage` and forces a logout.
- If the token is valid but lacks permissions (403), the frontend renders a `<Forbidden />` component or throws an `ApiError`.

### Logout Flow
1. Admin triggers logout.
2. Frontend sends `POST /api/v1/auth/logout` with the `refresh_token` from `sessionStorage`.
3. Backend marks the refresh token as revoked.
4. Frontend completely clears `sessionStorage` and redirects to the login page.

## Canonical Permission Registry

The backend dynamically assigns permissions via roles, but the system expects the following canonical permission strings:

| Permission String | Description | Used In |
| :--- | :--- | :--- |
| `super_admin` | Unrestricted access to all resources. Bypasses all specific permission checks. | All endpoints |
| `dashboard.view` | View the top-level overview dashboard and aggregate stats. | Dashboard UI |
| `support.view` | View support tickets. | `/support` |
| `support.manage` | Resolve or update support tickets. | `/support/{id}` |
| `users.view` | View the user directory and individual profiles. | `/users` |
| `users.manage` | Modify user accounts, suspend users, and change roles. | `/users/{id}` |
| `reports.view` | View medical reports and clinical metrics. | `/reports` |
| `reports.manage` | Edit, regenerate, or annotate medical reports. | `/reports/{id}` |
| `ai.view` | View LLM status, provider health, and inference metrics. | `/ai-ops` |
| `ai.manage` | Change LLM providers, modify prompts, and update cost guardrails. | `/ai-ops` |
| `chat.view` | View anonymized chat session telemetry (requires de-identification). | `/chat-ops` |
| `knowledge_base.view` | View RAG knowledge base stats. | `/rag-ops` |
| `system.health.view`| View backend API and DB health diagnostics. | `/health` |
| `incidents.view` | View system incidents. | `/incidents` |
| `security.view` | View the security posture and RBAC audit logs. | `/security` |
| `roles.view` | View configured admin roles. | `/security` |
| `privacy.view` | View privacy settings and data governance metrics. | `/privacy` |
| `configuration.view`| View system configuration and feature flags. | `/config` |

## Privilege Escalation Protections

- **Role Management**: Modifying admin roles via `/users/{user_id}/actions/change_role` explicitly requires `users.manage` AND `super_admin` permissions (`require_all_permissions`).
- **Self-Escalation**: The `change_role` endpoint blocks a user from attempting to change their own role ID (`if user.id == admin_ctx.user.id`).
- **Break-Glass**: Sensitive actions (e.g., viewing raw un-anonymized medical data) require an approved `SensitiveAccessGrant`. (See prompt 3 for details).

## Cross-Origin Resource Sharing (CORS)

- **Production Security**: The application utilizes `validate_production_security()` at startup to ensure `CORS_ORIGINS` is not set to `*` in production environments.
- **Client Configuration**: The Next.js admin frontend communicates with the backend via a configurable `API_BASE_URL`.
