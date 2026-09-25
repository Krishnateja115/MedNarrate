# Admin API Contract Audit

This audit tracks where frontend assumptions differ from actual backend API responses, focusing on mismatches and dangerous mappings.

## 1. Dangerous Assumptions Found

The audit searched for `.map(`, `.total`, `.data`, and `.items`.

### 1.1 Chat Operations (`/chat-ops`)
- **Frontend Path**: `src/app/(protected)/chat-ops/page.tsx`
- **Backend Route**: `GET /api/v1/admin/chat-ops/sessions`
- **Frontend Assumption**: Expects `{ sessions: [...] }` so it calls `sessionsData?.sessions.map(s => ...)`
- **Actual Backend Response**: Uses `build_pagination_response`, returning `{ items: [...], total: N, ... }`
- **Mismatch**: Frontend tries to map `.sessions`, which is undefined. Must be changed to `.items`.

### 1.2 RAG Operations (`/rag-ops`)
- **Frontend Path**: `src/app/(protected)/rag-ops/page.tsx`
- **Backend Route**: `GET /api/v1/admin/rag/documents`
- **Frontend Assumption**: Expects `{ documents: [...] }` so it calls `documentsData?.documents.map(d => ...)`
- **Actual Backend Response**: Uses `build_pagination_response`, returning `{ items: [...], total: N, ... }`
- **Mismatch**: Frontend tries to map `.documents`, which is undefined. Must be changed to `.items`.

### 1.3 Security Overview (`/security`)
- **Frontend Path**: `src/app/(protected)/security/page.tsx`
- **Backend Route**: `GET /api/v1/admin/security/overview`
- **Frontend Assumption**: Expects keys `active_admins_count`, `active_roles_count`, `active_sensitive_grants_count`, `recent_security_events_count`, `system_security_status`.
- **Actual Backend Response**: Returns `total_admins`, `active_breakglass_grants`, `total_audit_logs`, `pending_privacy_requests`, `total_security_events`. (Missing roles and status entirely).
- **Mismatch**: Total failure to map keys. Frontend metrics show empty/undefined.

### 1.4 Global Topbar Polling (`/components/layout/topbar.tsx`)
- **Frontend Path**: `src/components/layout/topbar.tsx`
- **Backend Routes**: `GET /api/v1/admin/alerts` & `GET /api/v1/admin/break-glass/grants`
- **Authentication Lifecycle Issue**: 
  - The `AuthContext` successfully validates the user once on load using `/api/v1/admin/me` (`suppressAuthError: true`).
  - `topbar.tsx` polls `/alerts` every 30 seconds.
  - If the token expires server-side, the next poll to `/alerts` returns `401 Unauthorized`.
  - `fetchApi` sees the 401, logs it, and dispatches an `auth:unauthorized` event which forcefully logs the user out.
  - The 401 in the screenshot is actually the *intended* session expiration behavior, accurately ending the admin session.

### 1.5 Safe Mappings Verified
- **Users**: `/users` correctly maps `data?.items`.
- **Reports**: `/reports` correctly maps `data?.items`.
- **AI Ops**: `/ai-ops` correctly expects `{ traces: [...] }` and `{ failures: [...] }` because the backend routes for `admin_ai_ops.py` manually return those keys instead of using `build_pagination_response`.
- **Dashboard**: `/` correctly expects `failure_categories` as a dictionary and uses `Object.entries(summary.analysis?.failure_categories || {}).map`.

## 2. Global Contract Verification

All other API calls strictly follow this lifecycle:
- HTTP Method aligns.
- Path aligns.
- Roles require validation via `get_admin_context`.
- Token uses `OAuth2PasswordBearerWithCookie`.
- Sensitive operations invoke `validate_access_grant` (Break-glass).
