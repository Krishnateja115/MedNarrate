# Admin Latest File Audit

This document records the exact files inspected during the deep forensic audit of the current MedNarrate Admin state.

| Path | Type | Purpose | Admin Relevance | Status / Issues Discovered |
| :--- | :--- | :--- | :--- | :--- |
| `/mednarrate-admin/src/app/(protected)/chat-ops/page.tsx` | Frontend View | Chat Operations UI | Renders admin session list. | **Bug**: Mapped `.sessions` instead of `.items`. |
| `/mednarrate-admin/src/app/(protected)/rag-ops/page.tsx` | Frontend View | RAG Operations UI | Renders vector DB document list. | **Bug**: Mapped `.documents` instead of `.items`. |
| `/mednarrate-admin/src/app/(protected)/security/page.tsx` | Frontend View | Security Operations UI | Renders admin roles, events. | **Bug**: Metrics keys mismatch the backend entirely. |
| `/mednarrate-admin/src/app/(protected)/help-center/page.tsx` | Frontend View | Help Center UI | Renders KB articles. | **Stable**: Works correctly, DB is just empty. |
| `/mednarrate-admin/src/components/layout/topbar.tsx` | Frontend Component | Global Topbar | Handles alerts & break-glass. | **Stable**: "Governance Operational" is a placeholder UI only. |
| `/mednarrate-admin/src/components/layout/sidebar.tsx` | Frontend Component | Main Navigation | Routing map for all admin modules. | **Stable**: Uses Lucide icon for branding instead of actual logo file. |
| `/mednarrate-admin/src/lib/api.ts` | Frontend Service | API Fetch Wrapper | Centralizes auth header & error handling. | **Stable**: 401s trigger local session teardown accurately. |
| `/mednarrate-admin/src/contexts/AuthContext.tsx` | Frontend Context | Auth State | Preserves user auth boundary. | **Stable**: Re-authenticates gracefully. |
| `/mednarrate-backend/app/api/v1/admin_chat_ops.py` | Backend Router | Chat Diagnostics | Provides paginated chat sessions. | **Stable**: Uses `build_pagination_response`. |
| `/mednarrate-backend/app/api/v1/admin_rag_ops.py` | Backend Router | RAG Diagnostics | Provides paginated docs. | **Stable**: Uses `build_pagination_response`. |
| `/mednarrate-backend/app/api/v1/admin_security.py` | Backend Router | Security Stats | Provides security summary keys. | **Stable**: Uses different key naming than frontend expected. |
| `/mednarrate-backend/app/api/v1/admin_health.py` | Backend Router | Health Probes | Dictates system health logic. | **Stable**: Requires 80% LLM telemetry success rate. |
| `/mednarrate-backend/app/api/v1/admin_alerts.py` | Backend Router | Notification Feed | Provides unacknowledged system alerts. | **Stable**. |
| `/mednarrate-backend/app/api/v1/admin_breakglass.py` | Backend Router | Sensitive Grants | Enforces emergency access grants. | **Stable**. |
| `/mednarrate-backend/app/api/v1/admin_help_center.py` | Backend Router | KB Management | Provides articles array. | **Stable**. |
| `/mednarrate-backend/app/api/v1/admin.py` | Backend Core | Root Admin Router | Mounts all sub-routers. | **Stable**. |
| `/mednarrate-backend/app/core/admin_auth.py` | Backend Core | RBAC Enforcement | Extracts AdminContext and checks scopes. | **Stable**. |
| `/mednarrate-backend/app/core/security.py` | Backend Core | JWT & Encryption | Uses OAuth2 bearer + cookies. | **Stable**: `get_current_user` rejects expired tokens properly. |
| `/mednarrate-backend/app/core/pagination.py` | Backend Core | Paginator | Wraps arrays in `items`, `total`, `page`, `limit`. | **Stable**. |
