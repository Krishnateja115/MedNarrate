# MedNarrate Admin Stability Audit

Date: 2026-09-27  
Audited commit: `8be76c2a8101c973b42d89139c5ba1cfcc25fdd5` (`main`)  
Release decision: **BLOCKED**

This document records the final Admin stability pass. It distinguishes verified behavior from inferred or unavailable behavior and does not claim regulatory certification.

## Audit scope

- Inventoried 72 authored Admin files under `mednarrate-admin/src` and `public`.
- Inventoried 181 authored backend application, migration, and test files.
- Inventoried 24 shared CI/documentation files.
- Machine-scanned all Admin TypeScript/TSX for API calls and unsafe rendering operations, including `.map`, `Object.*`, `.length`, `.reduce`, `.toFixed`, and `.toLocaleString` on API-derived values.
- Compared the Admin API literals with the live FastAPI OpenAPI document: 141 total OpenAPI paths, including 106 Admin paths. Dynamic record suffixes and the public auth paths account for the literal-prefix differences; no confirmed stale static endpoint remains.
- Inspected and tested authentication, RBAC dependencies, audit calls, pagination contracts, protected detail access, health probes, and the source files involved in every reproduced failure.

Generated dependencies, `.next`, Dart/Flutter build outputs, Python bytecode, uploaded documents, database contents, and binary assets were intentionally excluded from line-level source review. Supplied branding images were validated as runtime assets rather than source code.

## Original failures and root causes

| Surface | Reproduced failure | Root cause | Repair |
|---|---|---|---|
| Command Center | `GET /api/v1/admin/dashboard/summary` returned 500 | SQLite `CAST(timestamp AS DATE)` returned a value incompatible with SQLAlchemy's date processor; boolean predicates used Python identity tests and compiled to false SQL | Use portable `func.date`, SQLAlchemy `.is_(...)`, real completed-report counts, and timestamp-based processing duration |
| Analytics | `GET /api/v1/admin/analytics` returned 500 | Route queried nonexistent `LLMDiagnosticEvent.failure_category`; duration calculation used SQLite-only SQL | Use `error_category` and portable timestamp duration calculation; render unavailable metrics explicitly |
| Jobs | `GET /api/v1/admin/jobs` returned 500 | Route read nonexistent `JobExecution.error_message` | Return safe derived error summaries plus real category/request ID without exposing raw error details |
| RAG Operations | `GET /api/v1/admin/rag-ops/status` returned 500 | Route referenced nonexistent `DocLifecycleStatus.failed` | Remove unsupported failed-document metric and retain model-backed lifecycle metrics |
| Authentication/browser | Login appeared as a network/not-authenticated loop | Browser used an absolute cross-origin API URL and dev-origin handling was inconsistent; protected global requests could overlap restoration | Use same-origin API proxying, allow the explicit local dev origin, and preserve auth-initialization gating |
| Admin Copilot | Always returned a fabricated placeholder response; POST body was malformed for the shared client | Backend contained explicit placeholder text and frontend passed `body` instead of the client's `data` option | Added a permission-scoped read-only query allowlist backed by live account, incident, audit, and health data; corrected request shape |
| Command Center rendering | Empty `ms` suffix and derived negative completed count | Nullable latency was treated as defined; completed count was inferred from incompatible windows | Hide absent latency and consume the backend's real completed count |

## Route and UI smoke matrix

All checks below used the local Admin at `http://127.0.0.1:3002` and FastAPI at `http://127.0.0.1:8000` with a fresh authenticated session.

| Route | Result | Evidence |
|---|---|---|
| `/login` | PASS | Fresh sign-in succeeded; protected navigation restored |
| `/` | PASS | Summary, health, alerts, and real completed-report count rendered |
| `/analytics` | PASS | 7-day telemetry rendered; unavailable retention displayed as unavailable |
| `/users` | PASS | Paginated list loaded |
| `/users/detail?id=...` | PASS | Real user profile and tabs loaded |
| `/reports` | PASS | Paginated list loaded |
| `/reports/detail?id=...` | PASS | Real failed-report diagnostic loaded; PHI remained hidden behind sensitive access |
| `/support` | PASS | Empty state loaded |
| `/support/detail` | PASS | Missing-ID state handled without crash |
| `/incidents` | PASS | Empty state loaded |
| `/incidents/detail` | PASS | Missing-ID state handled without crash |
| `/admin-copilot` | PASS | Real account-count prompt returned database-backed counts and generated audit activity |
| `/ai-ops` | PASS | Page and API data loaded |
| `/chat-ops` | PASS | Page and API data loaded |
| `/rag-ops` | PASS | Live status returned 200; healthy index, 4 chunks, and supported document counts rendered |
| `/automation-ops` | PASS | Page loaded |
| `/jobs` | PASS | Live endpoint returned 200 and execution rows rendered |
| `/help-center` | PASS | Seeded article-backed page loaded |
| `/security` | PASS | Database-backed metrics loaded |
| `/governance` | PASS | Operational overview loaded |
| `/admins` | PASS | Real admin records loaded |
| `/admins/detail?id=...` | PASS | Real admin detail loaded |
| `/roles` | PASS | Roles and permissions loaded |
| `/audit` | PASS | Audit data loaded |
| `/breakglass` | PASS | Permission-gated page loaded; Topbar used summary only |
| `/privacy` | PASS | Page loaded |
| `/feature-flags` | PASS | Page loaded |
| `/ai-config` | PASS | Page loaded |
| `/health` | PASS | Real service probes loaded |
| `/settings` | PASS | Page loaded |
| `/announcements` | PASS | Page loaded after deliberate session-expiry/re-login check |
| `/_not-found` | PASS (build) | Static route generated by production build |

Automated endpoint tests cover RBAC, 401/403 behavior, pagination, filtering, mutations, audit creation, break-glass, security metrics, support/article linkage, and sensitive-access restrictions. Destructive production-like mutations were not performed against the developer's persistent database during browser smoke testing.

## Authentication and authorization

- Login, session restoration, expiry redirect, re-login, logout code path, protected route gating, Topbar alerts, and break-glass summary were traced.
- Unauthenticated protected endpoints return 401; permission dependencies produce 403 for authenticated principals without the required permission.
- The observed 15-minute local access-token expiry redirected to login once and re-login restored access without a loop.
- Topbar does not request complete break-glass records.
- Admin Copilot has no shell, unrestricted database, or raw clinical-data access.

## Data and performance findings

- Dashboard and analytics aggregates now use model-backed fields and portable queries.
- Nullable or untracked telemetry is rendered as unavailable rather than zero or malformed units.
- Job errors return categorized, non-secret summaries; raw error details are not sent to the global list.
- RAG does not fabricate a failure count unsupported by the document lifecycle schema.
- Shared React Query caching remains in use; no confirmed duplicate-request loop remains.
- System health is genuinely degraded in the local database because the recent LLM success rate is below its configured 80% threshold; API, database, storage, scheduler, and RAG probes are healthy. This was not converted to a false green state.

## Verification results

### Admin frontend

- ESLint: 0 errors, 1 existing performance warning for the supplied Topbar raster logo.
- TypeScript: PASS (`tsc --noEmit`).
- Jest: 16 suites, 66 tests passed.
- Production build: PASS; 35 static routes generated with webpack.

### Backend

- Pytest: **195 passed, 4 skipped, 0 failed**.
- Alembic: current `a21f77430a92 (head)`; one head; no migration added by this repair.
- Live repaired endpoints: dashboard 200, analytics for every supported timeframe 200, jobs 200, RAG status 200.

### Flutter/shared application

- `flutter test`: BLOCKED because the repository has no `test/` directory.
- `flutter analyze --no-pub`: completed with 11 informational lint findings and a non-zero exit (production `print` calls plus deprecated `dart:html` usage). The initial dependency-enabled run stalled at analysis-server startup; the no-pub rerun provided the actionable result.

## Remaining blockers

1. The broader repository cannot meet the requested full-release gate until Flutter has a runnable test directory and its 11 analyzer findings are resolved.
2. This working tree contains unrelated pre-existing modifications. They were preserved and not bundled into this repair.
3. Git commit/push is blocked by `.git/index.lock`, currently held open by the long-running `language_` process (PID 32573). The lock was not deleted while owned, so the verified repair remains uncommitted at the time of this report.
4. Deprecation warnings remain for Pydantic v2 compatibility, naive UTC datetimes, `google.generativeai`, PyMuPDF's old import, and SWIG types. They do not fail the current suites but should be scheduled before their upstream removals.

## Release decision

**BLOCKED.** The Admin application itself passed its frontend build/tests, full backend suite, live authentication, repaired API checks, and page smoke matrix. The repository-wide release gate is still blocked by unavailable Flutter tests, Flutter analyzer findings, and the externally held Git index lock preventing the mandatory commit/push.
