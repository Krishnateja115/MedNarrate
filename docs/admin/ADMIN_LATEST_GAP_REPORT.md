# Admin Gap Report

This document classifies gaps in the MedNarrate Admin ecosystem after the latest audit.

## 1. Confirmed Bugs (Frontend/Backend Contract Mismatches)
- **Chat Operations**: `chat-ops/page.tsx` maps `.sessions` instead of `.items` from the paginated `/api/v1/admin/chat-ops/sessions` endpoint.
- **RAG Operations**: `rag-ops/page.tsx` maps `.documents` instead of `.items` from the paginated `/api/v1/admin/rag/documents` endpoint.
- **Security Stats**: `security/page.tsx` expects `active_admins_count`, `active_roles_count`, `active_sensitive_grants_count` but `admin_security.py` returns `total_admins`, `active_breakglass_grants`, `total_audit_logs`.

## 2. Missing Seed Data
- **Help Center**: The frontend correctly hits the backend, but the DB table `help_articles` has exactly `0` rows. The UI correctly renders "No articles found."

## 3. UI/UX "Fake" Elements
- **Governance Badge**: The "Governance Operational" tag in the `topbar.tsx` is completely nonfunctional UI. It is conditionally rendered simply if break-glass is not active.

## 4. Completely Missing Frontend Modules
- **Notifications Dispatch**: The backend has `admin_notifications.py` (which supports dispatching global/targeted pushes), but the frontend completely lacks a `/notifications` page or UI routing for it.

## 5. Security Gaps
- **IDOR Protection**: The API relies heavily on `AdminContext` enforcing roles, which is sound. However, fetching sensitive records strictly depends on `validate_access_grant()`.
- **Top Bar 401 Polling**: While technically functioning correctly (ending sessions upon token expiration), polling 401s generate console/network spam before the frontend resolves the logout.

## 6. Performance Gaps
- **Global Polling**: `topbar.tsx` runs `fetchAlerts()` and `fetchBreakGlass()` every 30 seconds. In a scaled deployment, this will generate significant database load just from idle admin tabs.
- **Missing Pagination Caching**: `TanStack Query` caching is standard, but the global search debounce searches linearly across multiple DB tables on every keystroke (`admin_search.py`).

## 7. Recommended Execution Order

1. **Fix the Contract Mismatches**: Immediately repair `chat-ops/page.tsx`, `rag-ops/page.tsx`, and `security/page.tsx` by aligning the frontend TypeScript interfaces to the true backend schemas.
2. **Resolve DEGRADED Health**: Start the APScheduler and generate successful LLM telemetry to restore system health from DEGRADED to HEALTHY.
3. **Build the Notifications UI**: Create the missing `/notifications` view to interface with the existing backend dispatch endpoints.
4. **Seed Database**: Add default knowledge base articles for the Help Center.
5. **Optimize Topbar Polling**: Move topbar polling to a WebSockets approach or increase the interval to 2 minutes, minimizing aggressive DB hits.
