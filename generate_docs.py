import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

docs = {
    "docs/audit/ADMIN_COMPLETE_FUNCTION_MATRIX.md": """# Admin Complete Function Matrix

| Feature | UI Exists? | Button Works? | Calls Backend? | Endpoint Exists? | Mutates Real Data? | Real Product Effect? | RBAC Protected? | Audited? | Tested? |
|---|---|---|---|---|---|---|---|---|---|
| Command Center | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Partial |
| Analytics | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Partial |
| Users | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Medical Reports | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Support Desk | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Incidents | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Admin Copilot | Yes | Yes | Yes | Yes | No | No (Placeholder) | Yes | Yes | Partial |
| AI Configuration | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Chat Operations | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Yes |
| RAG Knowledge Ops | Yes | Yes | Yes | Yes (Status/List) | Yes (Status change) | No (No upload) | Yes | Yes | Partial |
| Automation Ops | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Jobs | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Help Center | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Security | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Yes |
| Governance | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Admin Accounts | Yes | Yes | Yes | Yes | Yes (role_ids=[])| No (Unusable Admin) | Yes | Yes | Partial |
| Roles & Permissions | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Audit | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Yes |
| Break Glass | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Privacy | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Settings (Maintenance)| Yes | Yes | Yes | Yes | Yes | No (DB Row only)| Yes | Yes | Partial |
| Feature Flags | Yes | Yes | Yes | Yes (Bug on Update)| Yes | No (No Evaluator)| Yes | Yes | Partial |
| Announcements | Yes | Yes | Yes | Yes | Yes | No (No frontend fetch)| Yes | Yes | Partial |
| Health | Yes | Yes | Yes | Yes | No | N/A | Yes | No | Yes |
| Global Search | Yes | Yes | Yes | Yes | No | N/A | Yes | No | Partial |
""",
    "docs/audit/ADMIN_CONFIRMED_BUGS.md": """# Admin Confirmed Bugs

## P0 Bugs
1. **Admin Notification Enum Crash**: Dispatching notifications to audiences "doctors", "patients", "caregivers" crashes the backend because `admin_notifications.py` uses `UserRole.DOCTOR` which is invalid (the enum uses lower-case members like `UserRole.clinician`).
2. **Feature Flag Update Bug**: `update_feature_flag` in `admin_feature_flags.py` raises `ValueError` when passing a name (e.g. `enable_ocr`) to `uuid.UUID`, making name lookup completely unreachable.

## P1 Bugs
1. **Fake Notification Dispatch**: Admin notification dispatch simulates success without actually calling a push notification service (FCM/APNS). Retry also just flips the DB status.
2. **Admin Creation without Roles**: Creating a new Admin from the UI sends `role_ids: []`. The newly created Admin is effectively unusable until roles are manually assigned.

## P2 Bugs
1. **ESLint Disable Abuse**: Almost every file in `mednarrate-admin/src` begins with `/* eslint-disable */`, masking potential frontend issues.
""",
    "docs/audit/ADMIN_DEAD_FEATURES.md": """# Admin Dead Features

1. **Feature Flags**: Admin portal can manage feature flags, but they are never evaluated anywhere in the codebase.
2. **Maintenance Mode**: Admin portal can enable maintenance mode, but it only writes to the DB. No middleware or business logic blocks user requests based on this status.
3. **Announcements**: Announcements can be created in the Admin portal, but no Flutter frontend or mobile app endpoint ever fetches or displays them to the user.
4. **RAG Upload**: The RAG Ops UI exists, but backend lacks any ingestion, upload, chunking, or indexing endpoints. It only supports changing document status in the DB.
5. **Admin Copilot**: Uses keyword string matching ("user", "incident") instead of an LLM. It's a placeholder feature.
6. **Tauri Desktop**: The `mednarrate-admin-desktop` directory is an unmodified Tauri template application with no integration into MedNarrate.
""",
    "docs/audit/ADMIN_FRONTEND_BACKEND_CONTRACTS.md": """# Admin Frontend Backend Contracts

### Misalignments Found:
1. **Admin Creation**: Frontend sends `role_ids: []` but backend expects a valid list of roles for the admin to be functional.
2. **Notification Dispatch**: Frontend expects a real dispatch, backend mocks it out.
3. **Feature Flags**: Frontend allows updating by name, backend crashes on `uuid.UUID(name)`.
4. **RAG Ops**: Frontend has "Upload coming soon", backend is completely missing endpoints for actual document ingestion.
""",
    "docs/audit/ADMIN_SECURITY_GAPS.md": """# Admin Security Gaps

1. **Admin Creation Misconfiguration**: New admins receive zero roles upon creation, which is safe, but functionally broken.
2. **Tauri CSP**: The Tauri desktop app has default configuration, but it's a dead starter app.
3. **Prompt Injection Middleware**: (Needs deeper analysis, but likely keyword-based matching is too broad).
""",
    "docs/audit/ADMIN_TEST_COVERAGE_GAPS.md": """# Admin Test Coverage Gaps

1. **Fake Asserts / Placeholders**: Tests for features like Feature Flags and Announcements may not actually test end-to-end functionality since those features are functionally disconnected.
2. **Notifications**: Tests pass for notifications because the backend mocks the dispatch internally, hiding the lack of real delivery.
""",
    "docs/audit/REPOSITORY_HYGIENE.md": """# Repository Hygiene

1. **Committed Virtual Environment**: `.backend-venv/` is fully tracked in Git (488 files, 7.3MB). It should be removed and added to `.gitignore`.
2. **Dead Desktop App**: `mednarrate-admin-desktop/` is a completely unmodified Tauri starter app.
3. **Global Lint Disabling**: The `fix_tsx.py` script and the extensive use of `/* eslint-disable */` is poor hygiene.
4. **TODO Placeholders in Prod Config**: Flutter `AppConfig` uses `https://api.mednarrate.com` with a TODO comment to replace with a real deployed backend URL.
"""
}

for path, content in docs.items():
    create_file(path, content)
