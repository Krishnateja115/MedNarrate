# MedNarrate Admin — Final Operational Status

Date: 2026-09-26  
Status: **BLOCKED**

This is the release-QA record for the current Admin application. It records what was verified by source inspection, automated tests, and production build checks. It does not certify production deployment or claim compliance certification.

## Implemented

- Admin route inventory covers 31 generated routes, including Login, Command Center, Users and User Detail, Admins and Admin Detail, AI/Chat/RAG Operations, Reports and Report Detail, Support and Support Detail, Help Center, Notifications/Medication Operations (`/automation-ops`), Jobs, Incidents, Health, Analytics, Security, Audit, Break-glass, Privacy, Settings, Governance, Feature Flags, Announcements, AI Configuration, and Admin Copilot.
- Protected-page authentication is provided by the shared AuthContext and protected layout. Topbar protected requests are gated until authentication is initialized and do not load complete break-glass records globally.
- Security metrics are database-backed and distinguish enabled administrator accounts from currently valid sessions.
- Governance overview and operational status are backed by admin APIs rather than decorative or hardcoded scores.
- Help Center, support article attachment, RAG document lifecycle, audit surfaces, and branded Admin shell are present in the current implementation.

## Fixed in this pass

- Command Center now renders an explicit error state when summary, health, or alert requests fail; it no longer silently renders an empty page.
- Frontend regression fixtures now use the current paginated `{items, total, page, limit}` contracts for users, reports, chat sessions, and RAG documents.
- RAG tests now exercise the current Documents tab and safe empty/error rendering.
- Pytest discovery is scoped to `tests/` so optional exploratory OCR scripts under `scratch/` are not collected as release tests.

## Tested

Frontend (`mednarrate-admin`):

- Jest: **16 suites passed, 67 tests passed**.
- ESLint: 0 errors, 1 warning (`<img>` performance warning in Topbar for the supplied logo asset).
- TypeScript: passed (`tsc --noEmit`).
- Production webpack build: passed; 35 static routes generated.

Backend (`mednarrate-backend`):

- Full configured pytest run: **190 passed, 4 skipped, 3 failed**.
- The three failures are listed below and prevent a PASS release status.

## Broken / blocked

1. `tests/test_final_release_matrix.py::test_break_glass_summary_exposes_count_without_grant_details` observed three active grants instead of the fixture's expected one. The endpoint correctly filters active, non-expired grants; the shared in-memory test database is not isolated between tests.
2. `tests/test_security_metrics.py::test_security_metrics_are_exact_for_admin_status_and_sessions` observed pre-existing active break-glass grants in its zero-admin baseline. This is the same fixture-isolation problem and means the controlled metric baseline is not reproducible in the full suite.
3. `tests/test_pipeline_integration.py::test_llm_client_missing_config_fails_cleanly` expected `LLMConfigurationError`, but auto-provider mode with fallback disabled currently raises a generic runtime error. This is an actual error-contract defect requiring a code fix.

The local API and frontend dev servers were not running at the end of QA, so live browser verification of every route and navigation path was not claimed here.

## Missing / remaining work

- Isolate each backend test's in-memory database state (or explicitly clean all relevant tables) while preserving within-test request state.
- Make no-provider/disabled-fallback LLM failure consistently raise the documented `LLMConfigurationError` and add a regression test.
- Re-run the complete backend suite after those fixes.
- Re-run a live authenticated route matrix against a running backend/frontend instance, including expiry, 401, 403, network-failure, and mutation/audit flows.
- Resolve or consciously accept the Topbar raster-image ESLint performance warning after measuring the supplied branding asset.

## Performance

- Frontend production build succeeds.
- Topbar uses lightweight alert and break-glass summary requests; complete break-glass records remain scoped to Security.
- React Query is used for shared page data and polling is bounded on operational pages.
- No additional duplicate-request or polling regression was proven by this static/build pass.

## Security

- Protected routes use shared authentication and permission checks.
- Break-glass global data is summary-only; details remain permission-gated in Security.
- Security and governance metrics are sourced from database queries.
- Full RBAC/IDOR/audit behavior was not marked fully verified because the backend release suite is not green and live route verification was unavailable.

## Final decision

**BLOCKED** — frontend checks are green, but the backend release suite has three failures and live route verification was unavailable. Do not promote this Admin build as a release PASS until the listed blockers are fixed and the complete matrix is rerun.
