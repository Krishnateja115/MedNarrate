# MedNarrate — Security Hardening Final Release Report

Branch: `security-hardening` (base commit `5f1d190`, plus uncommitted work — **nothing was committed or pushed**, per instruction).
PR #3 merged: **NO**

## 1. Executive Summary

The branch hardens authentication, token lifecycle, privacy controls, the LLM verification/translation pipeline, RAG, rate limiting, production API behaviour, mobile local storage, CI and the backend container. This pass started from the repository's *actual* state, which was behind the earlier summary: the previous run's 12 uncommitted edits existed (secure-storage migration, encrypted queue, lockout-migration cleanup, verifier/RAG/deletion/production-API changes), but there was **no** centralized rate limiter, **no** embedding-provider module, **no** CI expansion, scratch artifacts were still tracked, the offline queue was not user-scoped end to end, and the verifier status was never persisted. Those were implemented in this pass. Running the suite on **real PostgreSQL** also exposed several production-only bugs that SQLite hid (see §3 and §2).

**Release decision: NOT READY FOR PR REVIEW** (blockers in §8). All backend, PostgreSQL/Alembic and admin-portal gates pass; Flutter, Docker and GitHub Actions could not be verified.

## 2. Security Work Completed (what changed in this pass is marked **new**)

- **Authentication / lockout** — lockout migration `75dbea6aaf06` contains only the two column additions (`failed_login_attempts`, `locked_until`); verified on PostgreSQL including downgrade/upgrade round-trip.
- **Token lifecycle / MFA** — **new fix:** MFA challenge consumption (`consume_mfa_challenge`), password-reset token creation and admin-issued reset tokens wrote timezone-aware datetimes into naive `TIMESTAMP` columns → HTTP 500 on PostgreSQL for MFA login and password reset. Now naive UTC.
- **New fix: prompt-injection middleware false positives** — the regex matched the bare substring `dan` anywhere in a JSON body, so any request containing e.g. "Jordan", "Sudan", or a random MFA/JWT token with `dan` in it returned 400. This was the cause of the intermittent `test_totp_replay_is_rejected` failure. Now word-bounded and skipped for `/api/v1/auth/*`.
- **Rate limiting — new:** single shared limiter `app/core/rate_limit.py` (previously three module-local limiters that were disabled whenever `pytest` was imported). Covers signup, login, step-up, MFA verify/recover, MFA management, forgot/reset password (`RATE_LIMIT_SENSITIVE`, 5/min) and **`/auth/refresh` (new, `RATE_LIMIT_REFRESH`, 30/min)**; global default 100/min. Client key uses the resolved client IP; storage is memory by default, `RATE_LIMIT_STORAGE_URI` for shared counters.
- **CORS / docs / proxy** — docs/OpenAPI only in `development`; localhost CORS regex only in development; wildcard CORS, weak JWT secret and SQLite refused in production; `X-Forwarded-For` honoured only with `TRUSTED_PROXY=true`; audit logs use the resolved IP. Now covered by tests (**new**).
- **LLM verifier (fail-closed)** — timeout, HTTP error, exception, empty/malformed output and non-Ollama provider all yield `is_valid=None` (never `verified`). **New:** `verification_status` is now persisted on `ReportAnalysis` (it was computed but dropped); disabled verifier stays `unverified`.
- **Translation** — `translate_text_indic` raises `TranslationServiceError` on unconfigured/failed/timeout/wrong-script/number-mismatch; it never returns English as if translated. The stale test that asserted silent English fallback was corrected.
- **RAG privacy — new:** de-identification is pinned to `deidentified` mode inside RAG, so `LLM_SEND_MODE=full` can no longer disable it; embedding provider abstracted into `app/services/embedding_provider.py` (`EMBEDDING_PROVIDER`); pgvector retrieval bug fixed (`all(c.embedding_json …)` raised on numpy arrays → `is not None`); RAG chunks are deleted on user anonymization.
- **Deletion / anonymization** — the `users` row is retained in anonymized form (name/email/password/DOB/gender/MFA cleared, inactive); reports, files, refresh/reset tokens, MFA challenges, profiles, chats, push tokens, medication schedules, support tickets, privacy requests and RAG chunks are removed; file-deletion failure creates `OrphanFile`; audit rows are retained with email/name redacted. **New:** `ChatSafetyEvent` ids/FKs are now UUID (they were `String(36)` in the model but `uuid` in the migrations → `create_all` failed on PostgreSQL, and the deletion filter used `.hex`). `KnowledgeDocument.id` likewise.
- **Orphan files / retention / storage abstraction** — existing, regression-tested (`test_phase4_*`, `test_phase5_maintenance`). The file-deletion test was patching the wrong import target and only passed by test ordering; fixed.
- **FCM** — **new:** unconfigured Firebase in production no longer reports delivery success; device tokens are masked in logs.
- **Flutter** (static review only — see §4): tokens, Hive key, cached profile, doctor/caregiver profiles and **reminders (new)** in `flutter_secure_storage` with plaintext migration; offline queue encrypted; **new:** queue records are owned by `userId`, enqueue requires a signed-in owner, drain processes only the current user's records, unowned/legacy records are purged and never executed, logout clears the user's queue and reminders; the **profile-screen logout (new)** previously only cleared tokens — it now calls the full `ApiService.logout()`.
- **Dependencies — new:** removed unused `python-jose` (5 advisories); upgraded `pyjwt` 2.8.0→2.15.0, `python-multipart` 0.0.9→0.0.31, `python-dotenv` 1.0.0→1.2.2. `pip-audit` advisories fell from 112 (10 packages) to 74 (6 packages: transformers 43, torch 23, chromadb 3, sentencepiece 2, pytest 2, sentence-transformers 1).
- **Docker — new:** non-root user, `--no-install-recommends`, in-image `HEALTHCHECK`, `.dockerignore` (excludes `.env`, databases, uploads, tests, scratch, venvs). Root `docker-compose.yml`: DB/Redis bound to 127.0.0.1, `POSTGRES_PASSWORD` required, healthcheck path fixed to `/health`.
- **CI — new:** `.github/workflows/ci.yml` rewritten: SQLite backend suite, **PostgreSQL (pgvector) job with `alembic upgrade head`, single-head assertion, lockout round-trip and the full suite**, Flutter analyze+test, admin lint/typecheck/test/build, Docker build with non-root and no-secrets checks, gitleaks, `npm audit --audit-level=high`, and an advisory `pip-audit` (non-blocking because of the pinned ML stack).
- **Repository hygiene — new:** removed tracked artifacts (`tracked_files.txt`, `test_output*.pdf`, `mednarrate.db`, `pytest_output*.txt`, admin `lint_output.txt`/`test_output.txt`, `scratch/`, `scratch2.py`, `test_out.json`); `.gitignore` extended. Added `typecheck` script to the admin package.

## 3. Database / Alembic

- Current/only head: **`75dbea6aaf06`** (31 revisions in history; `alembic heads` = 1).
- PostgreSQL 16 + pgvector, fresh database, `alembic upgrade head`: **PASS after fixing a pre-existing bug** — revision `a21f77430a92` bulk-inserted string IDs into UUID columns (`DatatypeMismatchError`), so a fresh PostgreSQL migration had never completed. Fixed with UUID-typed columns/values.
- Lockout migration `75dbea6aaf06`: adds exactly `failed_login_attempts INTEGER NOT NULL DEFAULT 0` and `locked_until TIMESTAMP NULL`; downgrade removes both; re-upgrade OK.
- `alembic check` still reports **pre-existing model/DB drift** (e.g. `TIMESTAMPTZ` vs `DateTime`, `JSONB` vs `JSON` on `report_analyses`/`reports`). Not changed in this pass (see §6).

## 4. Validation Results

| Component | Command | Result | Counts |
|---|---|---|---|
| Backend (SQLite) | `pytest` (Python 3.11.x, `pip check` clean) | PASS | 324 passed, 0 failed, 3 skipped, 25 warnings, 140.9 s |
| Backend (PostgreSQL 16 + pgvector) | `DATABASE_URL=postgresql+asyncpg://… pytest` | PASS | 324 passed, 0 failed, 3 skipped, 25 warnings, 279.4 s |
| Alembic | `upgrade head`, `current`, `heads`, `history`, lockout round-trip | PASS | head `75dbea6aaf06`, 1 head |
| Admin | `npm ci` | PASS | — |
| Admin | `npm run lint` | PASS | exit 0 |
| Admin | `npm run typecheck` (`tsc --noEmit`, script added) | PASS | exit 0 |
| Admin | `npm test` | PASS | 20 suites, 78 tests |
| Admin | `npm run build` | PASS | Next build OK |
| Admin | `npm audit --omit=dev` | PASS | 0 vulnerabilities |
| Flutter | `pub get` / `format` / `analyze` / `test` | **NOT RUN** | No Flutter/Dart SDK reachable (SDK host and pub.dev blocked by network policy; none on the user's machine VM) |
| Docker | `docker build -t mednarrate-backend-security-final ./mednarrate-backend` | **NOT RUN** | Docker Hub (base image) blocked by egress policy; Dockerfile/.dockerignore reviewed statically only |
| GitHub Actions | final SHA | **NOT VERIFIED** | Nothing committed/pushed (user instruction); workflow YAML parses |

Skipped tests: MRAD dataset not present (2), live Gemini key not present (1). Warnings: pydantic `model_` protected-namespace, `pytest-asyncio` event_loop-fixture deprecation, unknown `asyncio_default_*` options in `pytest.ini`; none introduced by this work.

Test-harness changes: conftest honours `DATABASE_URL` for PostgreSQL runs and re-installs the session event loop after `unittest.IsolatedAsyncioTestCase` (which cleared it); `app/core/database.py` no longer passes pool arguments to `NullPool` under pytest (this made PostgreSQL test runs impossible); several fixtures wrote timezone-aware datetimes / bytes / 3-dim vectors that SQLite tolerated and PostgreSQL rejects.

Static Flutter review: `rg SharedPreferences lib` — remaining uses are non-sensitive preferences (language, theme, notification/biometric flags, units, announcements, macOS backend path) and one-time legacy-migration reads of `jwt_token`, `hive_encryption_key`, `cached_user`, profiles and reminders, each removed after migration. **The Dart edits made in this pass have not been compiled or tested.**

## 5. Adversarial Tests (executed unless noted)

- **Verifier failure:** timeout, generic exception, HTTP 500, empty/garbled output (`""`, `valid`, `VALIDATED`, free text), non-Ollama provider → never `verified`; pipeline persists `verifier_unavailable`/`malformed_response`/`invalid`/`unverified`.
- **Rate-limit abuse:** login (401×5 then 429), forgot-password, refresh; rotating spoofed `X-Forwarded-For` does not bypass the limit. Mutation-checked: removing the login decorator fails the tests.
- **RAG privacy:** PII (name, MRN, DOB, phone, email) absent from every embedder call and from stored chunks with `LLM_SEND_MODE` = `full` and `deidentified`; queries de-identified; cross-report retrieval scoped; embedder failure falls back to BM25. Mutation-checked: unpinning the mode fails the tests.
- **Deletion failure / orphan file:** storage failure creates exactly one pending `OrphanFile` with a sanitized error code; traversal/foreign paths skipped; user anonymization removes RAG chunks (SQLite and PostgreSQL).
- **Prompt-injection middleware:** "Jordan/Sudan/dandelion" pass; real injection phrases blocked; auth endpoints exempt.
- **Production API:** subprocess probes — production hides docs, no localhost CORS, evil origin rejected, wildcard CORS refuses startup; development unchanged.
- **PostgreSQL migration:** full chain + round-trip (§3).
- **Cross-user offline queue:** tests written (`test/offline_queue_test.dart`: other account's actions never executed, legacy records purged, null user processes nothing, per-user clear) — **NOT EXECUTED** (no Flutter SDK).

## 6. Remaining Risks

1. **Flutter changes unverified** (analyze/format/test not run); `dart format --set-exit-if-changed` was not added to CI because formatting state could not be checked.
2. **Docker image not built here;** CI docker job will be the first real build.
3. **Known advisories in pinned ML packages** (torch 2.4.1, transformers 4.44.2, chromadb 0.5.5, sentencepiece 0.1.99, sentence-transformers 3.0.1; dev-only pytest 8.3.2). Upgrading needs model-compatibility testing; `pip-audit` runs as advisory in CI.
4. **Model/migration drift** (`alembic check`: `TIMESTAMPTZ`/`JSONB` vs model types). Application code now writes naive UTC consistently, which works against both, but the schemas should be reconciled in a dedicated migration.
5. **Rate-limit counters are per-process** unless `RATE_LIMIT_STORAGE_URI` points at a shared store.
6. **Anonymization deletes files before the caller commits** the DB transaction; a failed commit would leave rows referencing deleted files. Failure of a single file deletion is handled (`OrphanFile`).
7. External service availability (verifier/translation/embedding providers) degrades features by design (fail-closed / BM25 fallback).
8. Stale developer scripts remain tracked at the root and in `mednarrate-backend/` (`check_*.py`, `fix_migration.py`, `test_*.py` outside `tests/`, `debug-*.md`, `bandit_results.json`); they are not packaged into the image (`.dockerignore`) but should be reviewed and removed by the owner.
9. The intermittent TOTP test failure observed during this work was traced to the prompt-injection regex and fixed; no further intermittent failures were seen in the final SQLite and PostgreSQL runs (single run each).

## 7. Manual Production Actions

- Set `ENVIRONMENT=production`, a strong `JWT_SECRET`, explicit `CORS_ORIGINS`, PostgreSQL `DATABASE_URL`; `TRUSTED_PROXY=true` only behind a proxy that overwrites `X-Forwarded-For`; `RATE_LIMIT_STORAGE_URI` for multi-worker deployments.
- Deploy with `alembic upgrade head` on a pgvector-enabled PostgreSQL (the help-center revision fix means a previously half-migrated database should be checked with `alembic current`).
- Rotate any secrets listed in `SECURITY_SECRET_ROTATION_PLAN.md`.
- After merging to a branch, confirm the new CI jobs (PostgreSQL, Flutter, Docker, gitleaks) pass; the Flutter and Docker jobs are the first execution of those gates for this work.

## 8. Release Decision

```text
NOT READY FOR PR REVIEW
```

Blockers: (1) `flutter analyze` / `flutter test` / `dart format` not executed; (2) Docker image build not executed; (3) GitHub Actions not verified for a final SHA (nothing was committed or pushed, as instructed). All backend (SQLite + PostgreSQL), Alembic and admin-portal gates passed.

PR #3 merged: **NO**
