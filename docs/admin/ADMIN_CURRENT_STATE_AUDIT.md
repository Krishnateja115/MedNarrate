# Admin Current State Audit

## 1. Current Commit
`9fa874f`

## 2. Files Inspected
- **Frontend**: `mednarrate-admin/src/app/(protected)/*`, `mednarrate-admin/src/components/layout/topbar.tsx`, `mednarrate-admin/next.config.ts`, `mednarrate-admin/package.json`
- **Backend**: `mednarrate-backend/app/api/v1/admin*.py`, `mednarrate-backend/app/models/*.py`, `mednarrate-backend/app/services/rag.py`
- **Tests**: `mednarrate-backend/tests/test_admin_endpoints.py`

## 3. Admin Completion Percentage
Approximately **80%**. The vast majority of the admin endpoints and UI pages are fully wired to the backend. The core gap resides in advanced AI tooling (Copilot) and granular medical profile viewing.

## 4. Confirmed Missing Functionality
- **Admin Copilot**: UI menus exist, but the feature is entirely unimplemented on both frontend and backend.
- **Medical Profile Viewer**: Admin cannot directly view a user's PHI `MedicalProfile` natively through the dashboard.
- **Global Push Notification Dispatch**: Push tokens exist, but there is no global dispatch center in the admin.
- **Doctor/Caregiver Verification**: Models exist, but verification UI is absent.

## 5. Confirmed Bugs
- RAG service attempts to import `chromadb` which is failing: `Could not initialize ChromaDB: No module named 'chromadb'`.
- `google.generativeai` deprecation warnings in `rag.py`.

## 6. Exact Degraded-Status Root Cause
**DEGRADED ROOT CAUSE:**
LLM Provider health probe failed because `dev_gemini` is marked as `configured: false` and `reachable: false` (returning status `unknown`). The backend `admin_health.py` strictly requires a fully functional LLM test request and a success rate >= 80% to be marked as healthy.

## 7. Backend Capabilities Not Yet Covered by Admin
- Global Translation Management (`analysis_translation.py`, `report_translation.py`).
- System-wide Push Notifications.
- Doctor & Caregiver specific profile viewing/verification.
- Full text PHI break-glass viewer (break-glass grants exist, but the direct PHI viewer UI is not implemented).

## 8. Security Blockers
- None currently blocking deployment, but Break-glass requires a rigorous UI audit to ensure `MedicalProfile` data isn't exposed unintentionally.

## 9. Performance Blockers
- **Minor**: The users list endpoint and report list endpoint perform full count queries (`SELECT COUNT(*)`) which will slow down as the tables scale.

## 10. Testing Gaps
- **Severe**: Only 11 tests exist in `tests/test_admin_endpoints.py` for over 25+ administrative routers. Missing RBAC, integration, and workflow tests for almost all endpoints.

## 11. Exact Recommended Next Implementation Order
1. **Fix Backend RAG ChromaDB Dependency**: Resolve the `chromadb` import failure.
2. **Implement Admin Copilot API**: Build the actual LangChain/Gemini backend for the Copilot.
3. **Build Admin Copilot Frontend**: Wire the chat interface.
4. **Expand Test Coverage**: Write Pytest cases for `admin_users`, `admin_roles`, `admin_reports`.
5. **Doctor/Caregiver Verification UI**: Build the review queues for specialized roles.
