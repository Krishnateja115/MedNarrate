# ADMIN_REMEDIATION_BASELINE

## 1. Current Architecture
- **Backend:** FastAPI, SQLAlchemy (asyncpg), PostgreSQL/SQLite.
- **Admin Frontend:** Next.js application, Tailwind CSS, Shadcn UI components.
- **Client App:** Flutter Mobile Application.
- **Security:** Token-based access for admins. RBAC modeled via `AdminRole`, `AdminPermission`, and `AdminRoleAssignment`.

## 2. Current Implementation Inventory & Verified Working Features
- Admin dashboard APIs exist (e.g., `/api/v1/admin/dashboard/summary`).
- Admin endpoints are mapped to underlying operational models (`User`, `Report`, `JobExecution`, `Incident`, `KnowledgeDocument`, `RagChunk`, `NotificationLog`).
- Basic RBAC structure exists in the database and is enforced on some backend endpoints via `require_permission`.
- Next.js frontend has a `Sidebar`, `AuthContext`, and scaffolding for various admin pages.

## 3. Defects Found & Classification

### Dashboard Placeholder Chart & Analytics Failure-Category Calculations
- **Classification:** PLACEHOLDER / FABRICATED
- **Severity:** High (Misleading Data)
- **Affected Files:** `mednarrate-admin/src/app/(dashboard)/page.tsx`, `mednarrate-backend/app/api/v1/admin_dashboard.py`
- **Root Cause:** `analysis_success_rate` uses `reports_failed / (reports_failed + reports_completed)` globally rather than for a specific time window, incorrectly mixing aggregations. Failure category breakdown is missing or fabricated.
- **Required Fix:** Compute success rates grouped by `failure_category` with proper time window filtering in the backend; wire real frontend charts.

### Incorrect Dashboard Health & LLM Health Semantics
- **Classification:** INCORRECT
- **Severity:** Medium
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_health.py`
- **Root Cause:** `is_healthy` is `True` if `provider_health.get("configured", False)` is True. This reports "healthy" merely if an API key is configured, even if unreachable.
- **Required Fix:** Actively probe LLM provider health; distinguish "configured" from "healthy" and "reachable".

### Notification Retry Not Actually Resending
- **Classification:** PLACEHOLDER
- **Severity:** High (Core functionality failure)
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_automation_ops.py`
- **Root Cause:** The `/notifications/{log_id}/retry` endpoint only sets `log.status = "retrying"` with a comment `# In a real implementation...`.
- **Required Fix:** Implement actual task enqueueing to resend the notification.

### Weak RAG Health Check
- **Classification:** INCOMPLETE
- **Severity:** Medium
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_rag_ops.py`
- **Root Cause:** Assumes RAG index is healthy if `total_chunks > 0`. 
- **Required Fix:** Implement a real vector index health probe (e.g., executing a lightweight test query).

### Admin Token Stored in localStorage
- **Classification:** INSECURE
- **Severity:** High
- **Affected Files:** `mednarrate-admin/src/contexts/AuthContext.tsx`
- **Root Cause:** Session tokens and user context are saved directly to `localStorage`, exposing them to XSS.
- **Required Fix:** Migrate to `HttpOnly` cookies, or harden the existing system if architecture constraints apply.

### Missing Frontend Pagination & Fixed Arbitrary Backend Result Limits
- **Classification:** INCOMPLETE
- **Severity:** Medium (Scalability Risk)
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_automation_ops.py`, `admin_diagnostics.py`, `admin_users.py`, `admin_jobs.py`, and frontend tables.
- **Root Cause:** Endpoints use hardcoded `.limit(50)` without offset support. Frontend tables lack actual pagination controls.
- **Required Fix:** Implement standard pagination (offset/limit or cursors) across all list endpoints and wire frontend tables.

### Frontend Navigation Not Permission-Aware
- **Classification:** INCOMPLETE (UX)
- **Severity:** Medium
- **Affected Files:** `mednarrate-admin/src/components/layout/sidebar.tsx`
- **Root Cause:** The `NAV_ITEMS` sidebar array is statically defined for all users without checking `AuthContext` or permissions.
- **Required Fix:** Retrieve user permissions in frontend context; conditionally render sidebar sections.

### Break-Glass Access Model & Audit Immutability
- **Classification:** MISSING / INCOMPLETE
- **Severity:** Critical
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_users.py`, `mednarrate-backend/app/services/audit.py`
- **Root Cause:** No explicit break-glass workflow (Request -> Approval -> Expiry) for accessing sensitive PHI/reports. Audit logs exist but lack atomic boundaries with privileged mutations.
- **Required Fix:** Introduce `SensitiveAccessGrant` modeling and enforce atomicity for audit logs.

### Incomplete Job Operations
- **Classification:** INCOMPLETE
- **Severity:** Low
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_jobs.py`
- **Root Cause:** Returns a flat list of 20 historical jobs. Missing proper job operations, filtering, or detailed diagnostics.
- **Required Fix:** Add filtering by job status, pagination, and failure diagnostics.

### Missing/Weak Support Diagnostic Snapshot
- **Classification:** INCOMPLETE
- **Severity:** High (Operational block)
- **Affected Files:** `mednarrate-backend/app/api/v1/admin_diagnostics.py`
- **Root Cause:** System infers stages indirectly from DB rows (e.g., `rag: True if NLP ran`). Lacks deterministic telemetry correlation.
- **Required Fix:** Provide a concrete snapshot correlating user, ticket, request ID, app version, LLM models, and explicit job state. Enable deterministic remediation.

## 4. Test Results Baseline
- **Frontend Tests:** `11 test suites, 23 tests` passed successfully via Jest.
- **Backend Tests:** Encountered `ModuleNotFoundError` by default. Ran using `PYTHONPATH=. pytest tests/`. Preliminary results indicate some existing baseline failures in `test_admin_endpoints.py` endpoints, indicating that current admin tests do not 100% pass on the current architecture.

## 5. Dependencies Between Fixes & Recommended Execution Order
To minimize risk and build iteratively, the following order is strictly recommended (aligning with prompts 2-10):

1. **Phase 2: Admin Session Security + Frontend RBAC** (Prerequisite for securing all other UI actions).
2. **Phase 3: Break-Glass + Audit Integrity + Privileged Actions** (Prerequisite for safe diagnostic inspection).
3. **Phase 4: Support Desk Diagnostic Automation** (Leverages break-glass models to troubleshoot safely).
4. **Phase 5: Real System Health + Jobs + Notification Retry + RAG Health** (Repairs placeholders for actual operational visibility).
5. **Phase 6: Analytics Correction + Command Center** (Consolidates real metrics without fabricating data).
6. **Phase 7: Pagination + Scalability** (Hardens all list endpoints established in prior phases).
7. **Phase 8: AI Configuration Secret Management + Chat/RAG Hardening** (Secures remaining sensitive telemetry).
8. **Phase 9: Privacy, Security Regression, Admin Action Integrity** (Holistic security review).
9. **Phase 10: Full System Integration, E2E Verification, CI/CD** (Final release gate).

## 6. Final Release Gates
- No placeholder functions or fabricated data logic remaining in the `admin/` codebase.
- `AuthContext` uses hardened secure state without exposing secrets to XSS.
- All backend admin endpoints strictly require RBAC via `AdminContext`.
- Sensitive operations require a validated `SensitiveAccessGrant`.
- Test suite (both frontend and backend) executes 100% cleanly.
