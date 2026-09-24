# MedNarrate Admin - Test Matrix

## Backend Tests (FastAPI)
The backend leverages `pytest` combined with `aiosqlite` for fast, async, in-memory testing.

| Suite | Focus | Pass/Fail |
|-------|-------|-----------|
| `test_breakglass_security.py` | Validates SensitiveAccessGrant lifecycle, blocking self-approval. | **Pass** |
| `test_support_diagnostics.py` | Validates PHI redacting and safe snapshot generation for support. | **Pass** |
| `test_ai_config_security.py` | Validates `is_set` behavior and API Key protection. | **Pass** |
| `test_health_checks.py` | Validates stack traces are suppressed on dependency failures. | **Pass** |
| `test_analytics_correctness.py` | Validates time-series and real SQL aggregates against dummy data. | **Pass** |
| `test_security_regression.py` | Validates IDOR protection, generic exception handling, pagination limits. | **Pass** |
| `test_production_llm_architecture.py` | Validates fallback cascades and isolation. | **Pass** |

Total backend suite coverage: **170 passed, 4 skipped, 0 failed**.

## Frontend Tests (Next.js & Flutter)
- **Admin App**: Static typing is enforced strictly via `npm run typecheck` and `npm run lint`. The production build succeeds cleanly.
- **Mobile App**: `flutter analyze` passes, preventing regressions on the patient portal due to backend API enhancements. `flutter test` completes successfully.

## Security Test Vectors
The following attacks have been actively tested and safely mitigated:
- **IDOR**: Changing an unrelated report ID across namespaces safely returns a 404 or 403.
- **Privilege Escalation**: Support agents attempting to `POST` to `/break-glass/grants/approve` are rejected natively by the backend RBAC dependencies.
- **XSS / Parameter Injection**: `ExceptionHandlers` sterilize 500 logs, and Sort/Filter attributes are strictly whitelisted via Pydantic enums.
