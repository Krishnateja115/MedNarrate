# MedNarrate — Pre-Deployment Audit Report

Scope: Flutter app (`lib/`), FastAPI backend (`mednarrate-backend/`), Next.js admin portal
(`mednarrate-admin/`), Docker/compose, CI. Date: 2026-10-12.
Nothing was committed or pushed. Your `.env` / `.env.backup` files were never read or copied.

---

## 1. Verdict

The project was already in good shape (strong auth, RBAC, audit logging, 374 passing backend tests).
The audit found **36 items**, of which **24 are fixed in code with regression tests** and 12 are
documented below with concrete solutions because they need your decision, infrastructure or a
database migration.

"Zero errors" can be claimed only for what could be executed here:

| Area | Result |
|---|---|
| Backend tests (pytest, SQLite) | **Baseline 374 passed → now 425 passed, 3 skipped, 0 failed** (51 new tests) |
| Backend lint (ruff E9/F63/F7/F82) | clean |
| Alembic | single head `110ba6a7df09` = `EXPECTED_SCHEMA_REVISION` (no schema change was needed) |
| Admin portal (eslint, tsc, jest 78 tests, `next build`) | all green (baseline; no admin files changed) |
| Flutter | **Not compilable here** (Flutter SDK download is blocked by the sandbox network policy). 4 Dart files + 1 Dart test were edited. **You must run `flutter analyze` and `flutter test`** (commands in §6). |
| PostgreSQL-only paths, docker compose | Not executable here. CI's Postgres job and `docker compose config` on your machine cover them. |

### Coverage honesty
You asked for every line to be read. Backend request paths, security, pipeline, LLM client, chat,
reports, notifications, reminders, auth and config were read in detail, and the entire backend and admin
test suites were executed. The 24k-line Flutter app was reviewed through its networking/offline/alerts/auth
layers and a systematic contract check (every one of the 34 endpoints the app calls was matched against
the backend's route table; every one of the 97 admin-portal URLs likewise). The UI-only screens
(profile, settings, insights, export formatting) were scanned for risk patterns (hard-coded URLs, TODOs,
prints: none found) rather than read line by line. Treat Flutter UI as "unverified by execution".

---

## 2. Findings and status

Severity: **H** high (broken feature / security / deploy blocker), **M** medium, **L** low.

### Fixed in code (with tests)

| ID | Sev | Problem | Fix |
|---|---|---|---|
| B1 | H | Prompt-injection middleware matched bare words (`dan`, `bypass`, `system prompt`) on **every** JSON POST/PUT, so a contact named "Dan" or "bypass surgery" returned 400. | Only multi-word attack phrases are matched. Tests for legit and malicious text. |
| B2 | H | Root `docker-compose.yml` defaulted to production but passed no CORS list, no `ANALYSIS_EXECUTION_MODE=worker` and had no worker, so the API refused to boot and, if it had, reports would never process. Redis was unused. | Added `worker` service, shared uploads volume, required `CORS_ORIGINS`, Redis-backed rate limits, email/encryption/storage variables. `redis` client added to requirements. |
| B3 | H | Password reset created tokens but **no code ever e-mailed them** (SendGrid was in requirements but unused). Users could not reset passwords. | New `services/email_service.py` (SendGrid REST / SMTP / dev-log), sent in a background task so response time doesn't reveal if an address exists. Production refuses the `log` provider. |
| B4 | M | Signup compared e-mail case-sensitively; login/forgot did not → duplicate accounts, unreachable reset. | Normalised to lower-case everywhere. |
| B5 | H | Name/allergy validators required ASCII letters: a Telugu/Hindi/Tamil full name or emergency contact was rejected, in an app that ships 8 Indian languages. | Unicode-aware validation (letters + combining marks). |
| B6 | M | Lab and medication LLM extraction sent **raw** report text (names, phone) to the LLM even in "deidentified" mode. | De-identified before both prompts. |
| B7 | M | De-identification missed plain `Name:`, `Mr./Dr. X`, bare phone numbers, Aadhaar, UHID/reg numbers. | Added conservative patterns; clinical values and `Test Name:` are preserved (tested). |
| B8 | M | Re-analysis duplicated medication rows. | Old rows for the report are replaced. |
| B9 | M | Pipeline error handlers didn't roll back, so a failed DB state could leave a report stuck in `processing`; `str(exception)` (SQL, hostnames, paths) was stored and returned to users by `/status`. | Single `_record_failure` helper (rollback, re-load, mark failed, never raises); sanitised message for unexpected errors; details stay in logs. |
| B10 | M | `/reports/trend`, `/compare`, `/{id}/compare-previous` returned 500 on null/string lab values, missing keys, malformed or duplicate UUIDs, or an LLM outage. | None-safe numeric coercion, 400 for bad IDs, LLM failures degrade to a message. |
| B11 | M | `FallbackAIProvider` fabricated answers ("There are 42 active users.") and a fake "Mocked translation" that the planner skipped validating — users could be shown English placeholder text as a translation. | Translation now fails visibly; the 42-users path is removed. |
| B12 | M | Chat: LLM failure → 500 and an orphan user message; the messages endpoint returned the **oldest** 20 so newer messages in long chats never appeared; missing `language` produced "reply in language None"; intent matching used substrings ("studying" ⊃ "dying"). | 503 with cleanup; newest page first (chronological output); language default; word-boundary matching plus more emergency phrases. Emergency text now mentions 112 (India). |
| B13 | L | Reminders had no length/format limits and accepted another user's `report_id`; support replies, push tokens, `/health/sync` unbounded; `/health/sync` reported "success" while discarding data. | Limits + ownership check; `/health/sync` is bounded and now says `persisted:false`. |
| B14 | M | The encryption key (MFA secrets, stored AI keys) was derived from `JWT_SECRET`, so rotating the JWT secret bricked MFA. | Optional `ENCRYPTION_KEY` (+`ENCRYPTION_KEY_PREVIOUS`) via MultiFernet; legacy data still decrypts. |
| B15 | L | Account export failed entirely if one stored file was missing. | Missing originals are listed in `MISSING_FILES.txt`; export succeeds. |
| B16 | M | `requirements.txt` lacked direct imports (cryptography, Pillow, dateutil, bcrypt, google-auth, huggingface-hub) and shipped pytest/ruff/mypy to production. | Added explicit ranges; dev tools moved to `requirements-dev.txt`; CI updated. |
| B18 | L | Duplicate field definitions in `config.py`. | Removed. |
| B20 | L | CSV exports vulnerable to formula injection (`=HYPERLINK(...)` in a ticket title or OCR'd test name). | `csv_safe` applied to every export; real numbers untouched. |
| B24 | H | Admin **"AI failures" CSV export always 500'd** (queried non-existent `status` / `error_message` columns). | Fixed query and columns; test added. |
| B25 | M | The app POSTs `/notifications/unregister-token`, the API only had DELETE → 405 swallowed silently, so logged-out devices kept receiving push notifications. | Server accepts POST and DELETE; registering a device token now detaches it from any previous account. |
| B26 | H | Medication alerts extracted from reports use times like "08:00 AM", but the app only parsed 24-hour `HH:MM`, so those alerts **silently never fired**. | Server normalises to 24h at extraction; app parser (`parseClockTime`) accepts AM/PM for existing data. Tests on both sides. |
| B27 | M | Offline-queued actions synced only on an offline→online *change*, never at app start or after login. | Drain at startup and after login (guarded against concurrent runs). |
| B28 | M | Admin "Retry/Reprocess report" set `uploaded`, which the worker never claims → nothing happened in production. | In worker mode it sets `processing` (what the worker claims). |
| B30 | L | Forgot-password screen only checked length ≥ 8; the server requires upper/lower/digit/special. | Client now shows the full rule before the request; copy says "e-mail you a reset code". |

### Not changed — needs your decision, infrastructure or a migration

| ID | Sev | Issue | Recommended solution |
|---|---|---|---|
| B17 | L | ~85 scratch/debug scripts and captures tracked at `mednarrate-backend/` root (`test_groq*.py`, `debug_*.py`, `qwen_capture*.json`, `llm_out*.txt`, `groq_resp.txt`); `scripts/patch_*.py` hard-code `C:\Users\manas\...`; admin root has one-off `convert_pages.py`, `fix_tsx.py` etc. | `git rm` them (they are not imported by `app/` and pytest only collects `tests/`). Not done automatically because deletions are irreversible and only you know what is still used. |
| B19 | L | CORS headers are missing on early 413/400 responses from middleware and on the global 500 handler, so browser clients see an opaque CORS error. | Add the CORS middleware outermost or set the headers in those responses. |
| B21 | L | Translation route holds a DB session across long LLM calls (pool 5+10). | Release the session before the LLM call or raise the pool size. |
| B22 | L | Worker has no max-attempt / poison-pill handling: a report that crashes the worker process (OOM) is re-claimed forever. | Add `analysis_attempts` column + Alembic migration + cap. |
| B23 | M | Behind a reverse proxy without `TRUSTED_PROXY=true` all clients share one IP and the 5/min login limit becomes global. | Set `TRUSTED_PROXY=true` only when your proxy overwrites `X-Forwarded-For` (compose passes it through). |
| B31 | L | Account deletion removes files before the DB commit; a failed commit loses files but keeps rows. | Move file deletion to a post-commit step (the `OrphanFile` mechanism already exists). |
| B32 | L | `/health` is unauthenticated and exposes schema revision/commit; report downloads use `Cache-Control: private, max-age=3600` for PHI. | Return only `ok` publicly; use `no-store` for downloads. |
| B33 | L | `app/ml/` (scikit-learn classifier + tracked model artifacts, `test_accuracy=1.0`) is not used at runtime. | Remove or document as research code. |
| B34 | M | Model IDs `gemini-3.8-flash`, `gpt-6.1-sol`, `mistral-large-2512`, `medgemma-1.5:4b`, `qwen3:14b` could not be verified from here. | Confirm each in your provider console; wrong IDs make that provider fail and fall through. |
| B35 | L | Emergency copy `disclaimerEmergency` in the 8 `.arb` files still says "911". | Add India's 112 in all languages (needs native-language review). |
| B36 | L | `torch` resolves to CUDA wheels (multi-GB image). | Use the CPU index in the Dockerfile unless you run GPU. |
| B37 | Info | Wearable sync (`/health/sync`) has no storage and the app doesn't call it. | Needs a `health_metrics` table + Alembic migration + an app screen — product decision. Not built. |

---

## 3. Missing features / backend gaps

* **E-mail delivery** — was entirely missing (B3). Added.
* **Worker deployment** — the code existed but nothing in compose ran it (B2). Added.
* **Wearable/health-data persistence** — frontend-less and storage-less (B37). Left as a documented stub.
* **Server-side medication push** — correctly disabled in production (needs per-user timezones); local alerts remain the mechanism.
* **Observability** — Sentry is a dependency; confirm `SENTRY_DSN` and alerting before launch.

## 4. What I kept working (functionality preserved)

All 374 pre-existing backend tests still pass unchanged (existing test files only gained new cases). No database schema change. Public API shapes are unchanged: the only
response changes are `/health/sync` (now explicit `persisted:false`), the `ai_failures` CSV columns
(it never worked before) and the chat messages endpoint paging window (newest first).

## 5. Files changed

Backend: `main.py`, `core/{config,encryption,csv_safety}.py`, `api/v1/{auth,password_reset,chat,reports,
reminders,notifications,support,health,admin_reports}.py`, `schemas/{user,notification}.py`,
`services/{email_service,privacy,lab_value_extractor,analysis_pipeline,llm_client,account_export,prompts}.py`,
`requirements*.txt`, `.env.example`, tests (`test_audit_fixes.py` new, two existing extended).
Infra: `docker-compose.yml`, `.github/workflows/ci.yml`.
Flutter: `connectivity_service.dart`, `api_service.dart`, `medication_alert_service.dart`,
`forgot_password_screen.dart`, `test/medication_alert_service_test.dart`.

## 6. Your pre-deployment checklist

1. Apply the patch (`git apply mednarrate-audit-fixes.patch`), review `git diff`, then on your Mac:
   `flutter pub get && flutter analyze --no-fatal-infos && flutter test`
2. Backend: `cd mednarrate-backend && pip install -r requirements-dev.txt && pytest -q`
3. Production environment: strong `JWT_SECRET`; a separate `ENCRYPTION_KEY`; explicit `CORS_ORIGINS`;
   `EMAIL_PROVIDER=sendgrid` + `SENDGRID_API_KEY` + a verified sender domain; `TRUSTED_PROXY` if behind a proxy;
   Redis for rate limits; `STORAGE_BACKEND` (S3/GCS) instead of local disk for multiple replicas.
4. `docker compose up --build -d` with `POSTGRES_PASSWORD`, `JWT_SECRET` and `CORS_ORIGINS` set (all required). **Verified on macOS/Colima:** db, redis and backend healthy, `/health` shows `schema_revision == schema_expected`, worker sweeping. If host ports clash with services already on your machine, set `API_HOST_PORT`, `POSTGRES_HOST_PORT`, `REDIS_HOST_PORT`. Postgres only applies `POSTGRES_PASSWORD` when its volume is first created, so after changing it either use a new project name (`-p name`) or remove the old volume deliberately (`docker compose down -v` deletes data). Still to try: upload a report and confirm the worker completes it.
5. Verify LLM model IDs (B34), Firebase/APNs credentials, app signing, privacy policy and data-retention copy.
6. Run Postgres CI (`backend-postgres` job) — it exercises the migrations and Postgres-only code I could not run.
7. Delete the temporary archive `.audit_src_tmp.tgz` from your project folder if it is still there.
8. Optionally tackle §2 "Not changed" items, starting with B23, B34, B17.

## Addendum - found while running the app (2026-10-12)

Verified on macOS + Docker with `scripts/smoke_report_flow.py scripts/sample_reports/report3.pdf`.

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| B38 | H | CBC PDFs that extract one cell per line (name / result / range / unit) lost reference ranges and units, dropped Hemoglobin and Total Leucocyte Count, and turned section headings ("RBC Indices") into tests. Every value showed "Not classified". | New column-layout parser in `lab_value_extractor.py` (also handles one-row-per-line `Name 15 13 - 17 g/dL`). Ranges come from the report itself; values with no printed range stay unclassified. Regression tests + fixture. |
| B39 | H | Fallback summarizer treated any report containing the word "pathology" (e.g. "MD Pathology" in a signature) as a biopsy report and pasted raw prompt text into the summary. | Header regex now matches both prompt styles; keyword fallback removed; prompt scaffolding stripped; glossary expanded to ~20 tests. |
| B40 | M | Grounding check flagged the extracted-test count ("22 results") as an unsupported claim, adding a "clinician review required" warning to a correct summary. | Counts derived from the structured results are accepted; invented numbers are still rejected. |
| B41 | M | Report screen showed Flutter overflow stripes (status chips, Source & Validation rows). | `Wrap` for chips; flexible label/value rows. |
| B42 | L | Settings screen threw a `ListTile`/`DecoratedBox` assertion on every build. | Transparent `Material` inside the card. |
| B43 | L | Acronyms rendered as "Mcv", "Rdw-Cv". | Acronym-aware naming. |
| B44 | L | Worker container inherited the API's HTTP healthcheck and would report unhealthy. | Healthcheck disabled for the worker; Chroma telemetry off. |

Still open: the "Validation: PASSED" chip in the report header is a fixed label, not tied to the grounding result.

## Addendum 2 - AI chat / translation "unavailable" (2026-10-12)

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| B45 | H | LLM API keys in `mednarrate-backend/.env` never reached the Docker containers (compose did not pass them through), so every provider reported "not configured". | `docker-compose.yml` passes all LLM variables through from the shell / root `.env` and also reads `mednarrate-backend/.env` at runtime (optional `env_file`). |
| B46 | H | `GEMINI_API_KEY` is refused when `ENVIRONMENT=production` (compose default). A Gemini key therefore never worked in Docker. | Documented; `python -m app.llm_check` states this explicitly. Run with `ENVIRONMENT=development` for local Gemini keys, or use OpenAI / Anthropic / Mistral / Vertex. |
| B47 | H | Chat and summaries used one provider plus an unreachable Ollama fallback, so the other configured keys were never used and one exhausted key meant "AI unavailable". | New ordered chain (`LLM_PROVIDER_CHAIN`, default vertex_ai, gemini, openai, anthropic, mistral) containing only providers that have working credentials. |
| B48 | H | Translation retried every failing provider twice per chunk and lost the HTTP status, so one bad key or one exhausted daily quota was hammered repeatedly, burning the other keys' allowance as well. | `provider_health.py` circuit breaker: persistent failures (auth, quota, unknown model) put a provider on cool-down; the planner skips cooling providers and no longer retries persistent errors. Status and reason are preserved. |
| B49 | M | No way to see why a provider fails (a wrong model name looks like a "limit"). | `python -m app.llm_check` probes every provider and prints the real reason (never the key). |
| B50 | H | When no provider worked, the chat saved "AI service is temporarily unavailable" as a genuine assistant reply. | The offline provider now raises; the chat endpoint answers 503, removes the orphan question and stores nothing; the app shows an error toast. |
| B51 | M | Chat input: Enter inserted a new line (multi-line field), and the theme's input border drew a second outline inside the pill. | `Focus(onKeyEvent)` sends on Enter (Shift+Enter = newline, IME composition respected); `textInputAction: send`; all theme borders neutralised inside the pill. |
| B52 | L | Exception messages now never contain the provider's raw error text (kept in `error_detail`, used only by logs and `llm_check`). Tests isolate provider cool-down state. | - |

## Addendum 3 - translation redesign, UI polish, backend sweep (2026-10-17)

Nothing in this addendum has been pushed or deployed. Backend suite: 469 passed, 3 skipped. Flutter could not be compiled in the sandbox: run `flutter analyze` before relying on the UI changes.

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| B53 | H | The first translation call had to return all 78 interface labels in the right script. One missing or English label failed the whole translation and wasted quota on retries. | Labels and the standard "discuss with your doctor" bullets now come from a fixed table (`translation_ui_labels.json`, `translation_labels.py`) for hi, ta, te, kn, ml, bn, mr. The model only translates report content. The table was drafted by me and needs native-speaker review before a public release. |
| B54 | H | The Gemini response schema contained `OBJECT` types with no properties, which the Gemini API rejects. Every Gemini translation request could fail. | Free-form maps are now sent as arrays of `{name, translated}`. A test walks the schema for empty objects. |
| B55 | H | Units were translated one after another with a 240 s total deadline, the same as the app's HTTP timeout. | The first unit runs alone as a probe, the rest run in parallel (`TRANSLATION_CONCURRENCY`, default 3). Server deadline `TRANSLATION_DEADLINE_SECONDS` is 150 s, below the app's 240 s. Per-call timeout is `TRANSLATION_TIMEOUT_SECONDS`. |
| B56 | H | The validator rejected a whole translation when the model altered an identifier, a dose or a clock time. | Identifiers, doses and clock times are restored from the source. Ambiguous partial identifier mismatches are still rejected. |
| B57 | M | Every failure showed the same message, so the cause was invisible. | Failures carry a reason (quota, auth, model, not configured, timeout, invalid output). The API returns `reason` and a matching patient-safe message, and logs the category and request ID with no report text. Final merged validation now runs in all environments. |
| B58 | M | Providers that were not configured or were out of quota were retried. Ollama was tried as an automatic translation fallback. | Cooling providers are skipped, persistent errors are not retried, and Ollama is no longer added automatically. |
| B59 | H | `ENVIRONMENT=production` (the compose default) blocks a direct Gemini API key. | New explicit opt-in `ALLOW_GEMINI_API_KEY_IN_PRODUCTION`. The free Gemini tier may use prompts for training, so do not send real patient data through it. |
| B60 | M | No way to test translation against real providers. | `python -m app.translation_check [hi ta ... | all]` runs a synthetic report and prints PASS/FAIL with the reason and a hint. |
| B61 | M | A slow chat provider could hang a request. | Chat answers are limited by `CHAT_TIMEOUT_SECONDS` (75 s) and then follow the existing 503 path. The app waits 90 s. |
| B62 | M | "Validation: PASSED" in the clinical view was a fixed label (open item from Addendum 1). | It now reflects the report's verification status (PASSED / NEEDS REVIEW / NOT VERIFIED). |
| B63 | L | Chat polish: a failed send left an orphan bubble, the copy action did nothing, bubbles were too wide on desktop. | The failed message is removed and its text returns to the input box. Copy really copies, assistant bubbles have a copy button, and the bubble width is capped. |
| B64 | L | The patient view gave no sign that a translation was running, and left `[TRANSLATION][FLUTTER]` debug prints in the code. | A translating banner is shown and the debug prints are gone. |
| B65 | L | Duplicate imports (ruff F811) in `auth.py` and `admin_alerts.py`. | Removed. No undefined names (F821) in the backend. |

| B66 | H | Timeouts and connection failures (the Gemini call raising `ReadTimeout`/`ConnectError`) were classified "unknown", so the app only said "temporarily unavailable" and the cause was invisible. | The error chain is inspected: timeouts are transient, connection/DNS/TLS failures are the new `network_unreachable` reason. Provider cool-down state keeps a key-free description of the last error. |
| B67 | M | In development the app gave no hint why translation failed. | When `ENVIRONMENT` is not production, the toast ends with `[dev info: reason; provider=kind (error chain)]`; the full traceback of non-provider bugs is logged. Never shown in production. |
| B68 | M | A wrong or retired Gemini model name (HTTP 400/404) failed every request. | `GEMINI_FALLBACK_MODELS` (default `gemini-2.5-flash-lite,gemini-2.5-flash`) is tried once; output is still fully validated. |
| B69 | L | `docker compose up` failed with "required variable ... missing" unless variables were exported. | `scripts/dev_up.sh` passes `mednarrate-backend/.env`; `scripts/dev_backend.sh` runs the local-venv API (stops the old process on port 8000, runs `translation_check`, starts uvicorn with reload). A backend started before the 17 Oct fixes keeps running the old code until restarted. |
| B70 | H | Tamil (and other Indic) translations were intermittently rejected as "not in the requested script". The check ignored vowel signs and virama marks (so Tamil/Telugu/Malayalam counted about half their letters) and counted every Latin test name (MCV, hemoglobin) against the text. | Combining marks of the target script now count as native letters; abbreviations, units and tokens of up to three letters are ignored. Untranslated English is still rejected for every language (tests). |
| B71 | H | Only one provider was really usable (OpenAI had no credits, Mistral rate-limited, Anthropic/Vertex not configured), so one bad Gemini answer failed the request. | The same Gemini key is tried on other models (`GEMINI_FALLBACK_MODELS`, default `gemini-2.5-flash,gemini-2.5-flash-lite`) as separate providers before OpenAI/Mistral. Free-tier quotas are per model, and the stronger model rescues scripts the lighter one gets wrong. |
| B72 | M | Only OpenAI, Anthropic, Mistral, Vertex and Gemini were supported, so extra free quota could not be added. | Generic OpenAI-compatible provider for Groq, Cerebras, OpenRouter and GitHub Models. Each activates with its key in `.env`; they join the translation and chat chains and `llm_check`. Their Indic-language quality is untested; run `translation_check all` per provider. |
| B73 | M | Chat UI: typed messages used the theme's `onSurface` colour on the green bubble (dark text on dark green in light mode), the amber disclaimer was low contrast, "Online" was hard-coded, and the two chat screens differed. | Shared `chat_widgets.dart` (bubble, composer, disclaimer, empty state, typing bubble) used by the full-screen assistant and the report tab: white text on the brand-green user bubble, soft neutral assistant bubble, readable disclaimer, real online/offline status, timestamps, copy button, starter questions, retry on load error, disabled send button while empty. |

| B74 | M | New feature: voice input (microphone in the chat box). Optional and off by default, kept separate from the rest of the app. | Backend: `app/services/speech_service.py` and `app/api/v1/speech.py` (`GET /speech/status`, `POST /speech/transcribe`). Records are sent to Whisper on Groq (`whisper-large-v3`, then `whisper-large-v3-turbo`), using the existing `GROQ_API_KEY`. Only active when `VOICE_INPUT_ENABLED=true` and a key is set; otherwise the status endpoint says disabled and the app shows no microphone, so the app behaves exactly as before. Login required, rate limited (`SPEECH_RATE_LIMIT`, 20/minute), 10 MB cap, audio type checked from the file's first bytes (not the filename), a rejected clip never puts a model on cool-down, silence and Whisper's invented "Thank you." are dropped, errors are friendly and key-free. Audio and transcript are processed in memory and never stored or logged (test). 36 tests. |
| B75 | M | Flutter: `lib/features/voice_input/` (recorder wrapper, controller, widgets, language list, text insertion). `ChatComposer` shows a mic inside the text box beside the text; tapping it replaces the box with a recording bar (discard, live level bars, timer, language chip, tick). The text appears in the box at the cursor and is never sent automatically. Languages: English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi (remembered; defaults to the app language). Recording is cancelled when the app goes to the background and stops at 120 s. Both chat screens get it through the shared composer. | Permissions added: Android `RECORD_AUDIO` (minSdk raised to 23, the plugin's minimum), iOS and macOS `NSMicrophoneUsageDescription`, macOS `com.apple.security.device.audio-input`. New dependency `record: ^6.0.0`. Privacy policy text updated (the recording goes through our server to a speech-to-text provider). Unit tests for the controller (fake recorder) and the text insertion. **Not compiled or run here**: run `flutter pub get`, `flutter analyze`, `flutter test test/features/voice_input`. |
| B76 | M | Yellow/black striped bars (Flutter "RenderFlex overflowed") in debug builds. Found by reading every Row/Column/dialog/sheet in `lib/`: text that could be wider than its space, mostly translated or dynamic text. Release builds do not paint the stripes, but the content is clipped. | Wrapped the overflowing text in `Expanded`/`Flexible` (no visual change when it fits): dashboard "Reports Compared" + trend chip (definitely wider than a phone), "Medications from Latest Report", clinical view diagnosis and compared-findings rows, patient view metadata rows, report-type chip, "Report at a Glance" header, result value, AI-attribution lines, settings legal rows and biometrics dialog title, delete-report dialog titles, dashboard banner, offline banner, primary button label, recording bar label. Scrollable wrappers added where content can exceed the screen: lab-result info sheet (long OCR excerpts), reminder-sound sheet, app-lock screen (landscape / small windows). Test-trend dropdown made `isExpanded` with ellipsis. |
| B77 | L | Terms of Service said "your local emergency emergency response number (e.g., 911 ...)". | "call your local emergency number (112 in India, 911 in the US)". The unused `disclaimerEmergency` strings in the `.arb` files were left alone (not shown anywhere in the app). |

| B78 | H | Switching the language left large parts of the app in English (login and sign-up, forms, upload, reminders, support, report details, chat, voice input, insights, error messages, report-type and status labels). | Every user-facing screen and message now follows the chosen language (English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi). About 480 new strings in all 8 `.arb` files (673 keys each, same keys and placeholders in every file). Strings are read with `AppLocalizations.of(context)` in widgets and `appL10n` (new `lib/core/l10n/app_l10n.dart`) in validators, services and controllers. Values that are stored in English (reminder frequency, support category and status, report type) are translated for display only (`display_labels.dart`), so saved data and the backend are unchanged. |
| B79 | M | Error messages from the server and the app ("Incorrect email or password", "Voice input is busy...", offline notices) were always English. | `ApiException.message` is now a getter that maps the known fixed messages to the chosen language (`server_messages.dart`); the original text is kept in `rawMessage`, and any message without a translation is shown unchanged. |
| B80 | M | Report detail screens (headings, chips, lab labels) ignored the app language until a report was translated. | A bundled copy of the backend's `translation_ui_labels.json` (`report_ui_labels_data.dart`) is used for Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali and Marathi. A translated report's own labels still take priority. |
| B81 | L | Frontend name and allergy validators rejected non-Latin text that the backend accepts. | Unicode letters and combining marks are accepted (Devanagari, Tamil, and so on). Password rules stay ASCII, as in the backend. |
| B82 | L | Dates in insights and on cards used English month names. | Date formats use the app language. |

| B83 | M | Settings showed two "Coming Soon" rows (Health App Sync, Connected Devices) that did nothing. | Removed the Integrations group and its placeholder sheet. Real smartwatch sync is a separate project (see the note after this table). |
| B84 | H | The AI chat opened from the assistant screen (no report) answered "I cannot ... there is no information in the provided report" to every general question, and forgot earlier messages. | A chat with no report is now a general health assistant (fitness, food, sleep, common symptoms, what test terms mean). It stays on health topics, does not diagnose or prescribe, and politely declines unrelated questions (maths, coding). It knows the titles, dates and types of the user's own reports (no lab values) and the last 6 messages. Report chats still answer from the report and may add clearly-labelled general explanations. The assistant screen shows health-specific starter questions and hint text. Emergency and diagnosis routing is unchanged. 2 tests added. |
| B85 | M | Yellow/black "RIGHT OVERFLOWED BY 18 PIXELS" on the dashboard's Today's Health Tip header in Tamil. | The title is wrapped in `Expanded` (two lines at most). |
| B86 | H | Health Insights showed two selected reports and nothing else. The comparison matched a test only when name AND unit were identical; one report stored blank units, the other "pg", "%" and so on, and the same test was spelled differently ("Mean Corpuscular Volume" vs "MCV", "rbc_count" vs "Total RBC Count", "RDW" vs "RDW-CV"), so no test ever matched. | The backend now matches tests by a canonical name (`comparison_name`, used only for comparison and trend; stored names are not changed). A missing unit no longer blocks a match; two different non-empty units (g/dL vs g/L) stay separate. Reference ranges are formatted and hidden when absent. The trend endpoint accepts the same aliases. When the reports share no numeric test the screen now says so and how to choose reports. 2 tests added; backend suite run in the sandbox: 497 passed; `test_production_hardening.py` (18 tests) was not run there because it needs the production environment, so run the full suite on your machine. |

| B87 | M | Listing medication schedules returned a server error (500) as soon as the account had a reminder added by hand, because the response schema required a report id and hand-made reminders have none. | `report_id` is optional in the response. Regression test added. |

| B88 | L | The chat API accepted empty and 20,000-character messages and sent them to the AI. | A message must contain text and be at most 2000 characters (the app already caps at 500). Regression test added. |

| B89 | M | On the report details screen the type badge under the title showed the caption "Report type" instead of the report's own type (Blood Test, Pathology and so on) in every language except English; the Clinical View showed the raw stored word ("pathology"). | Both now show the type name in the language the report is displayed in. |

| B90 | L | Report details polish: the title was cut off ("Report D...") because it was centred between a wide back button and two icons; the three summary counts wrapped into a loose list; the tab bar started with a large empty gap. | Title sits left of the icons and shows in full; the counts are three equal tiles; tabs start at the left edge with tighter spacing. |
| B91 | H | Course requirement: every deep-learning model's performance measures and the XAI algorithms must be visible in the UI and the document. Nothing in the product showed model quality. | New measured-results pipeline. `app/ml/evaluators.py` and six small hand-labelled test sets (`app/ml/eval_data/`) score the NER model (span P/R/F1, type accuracy), the three embedding models (recall@k, MRR, with a BM25 baseline), the LLM chain (grounded-QA accuracy, abstention, number preservation, chrF for Hindi), Qwen, Whisper (word error rate) and the lab extractor. `python scripts/evaluate_models.py` runs them, saves after every part (a failed re-run keeps the previous good result) and writes `docs/MODEL_RESULTS.md`. A model that was not measured shows "Not evaluated yet"; no number is typed in by hand. 28 tests. |
| B92 | H | XAI. Four explanation methods in `app/ml/xai.py` (plain numpy): LIME-style local surrogate with fidelity R squared, exact linear attribution (SHAP for linear models; contributions plus intercept equal the decision function, tested), occlusion saliency for the NER model, and the rule trace for High/Low lab flags. Worked examples are stored with the report. | Admin page **Model Performance & XAI** (summary cards, performance tab, XAI tab, "Explain your own text" box; endpoints `/admin/ml/*` need `ai.view`, only the text length is audited). App: **Settings > AI models & explainability** and a **Why flagged?** sheet on every lab result (works offline, uses the same flag logic as the server, including a laboratory marking that contradicts the range). 80 new strings in all 8 languages. Document: `docs/ML_MODELS_AND_XAI.md`. 7 endpoint tests; admin jest test; Dart widget test. |
| B93 | M | The word-error-rate tokenizer split Devanagari words at vowel signs, so Hindi error rates were meaningless. Number metrics were inflated by sentences that contain no number. | Punctuation is stripped by Unicode category and words are split on whitespace; number preservation is scored only on sentences that contain numbers. |
| B94 | L | The rule-only lab parser used inside the production extractor could not be scored separately. | `extract_lab_values_rules` exposes it (production behaviour unchanged). Measured: precision 100%, recall 81.0%, F1 89.5% on 42 values; pipe-separated and some thyroid layouts rely on the LLM fall-back. |
| B95 | M | The admin portal logged every failed background poll (alerts, health, break-glass summary) with `console.error`, so the Next.js dev overlay popped up on each one. The 500 response also never said what failed. | Server errors (5xx) are logged with `console.warn` plus the request reference. In local development only (`development`, `dev`, `local`, `test`) the 500 body carries a `debug` field with the exception name and message, with long token-like strings hidden; production and staging never include it. 4 tests in `tests/test_error_responses.py`. The root cause of the user's 500s on `/admin/alerts`, `/admin/health` and `/admin/break-glass/summary` was not reproduced (all return 200 on a clean database); it needs the backend traceback or the new `debug` text. |
| B96 | L | The admin sidebar had pages that duplicated others or could never hold data: Governance Center, Privacy Center and the Jobs page (Automation Jobs already covers jobs), and a "Pending Privacy Requests" card on Security Overview. Several items shared one icon. | Removed those pages and the card (the backend routes are left in place). Every sidebar item has its own icon; "Model Performance & XAI" is now "Models & XAI". |
| B97 | L | Admin pages used different title sizes, spacing and widths. | Ten pages (Roles, Audit Logs, Break-Glass, Feature Flags, AI Configuration, App Settings, Announcements, Analytics, Admin Accounts, Security) share one header pattern; the layout already provides the width and padding. Health shows "Database", "Background Jobs" and "Knowledge Base (RAG)" instead of internal names. 2 admin tests updated; tsc, eslint and the 89 jest tests pass. |
| B98 | H | The AI Operations page counted every provider ATTEMPT as a request, so one chat answered after two failed providers looked like three requests and the success rate was wrong. `fallback_used is True` and `error_category is not None` were plain-Python checks that never became SQL, so fallback usage and the failure breakdown were wrong. | `/ai-ops/overview` and `/failures` count distinct requests, report who actually answered ("Who answered" table with friendly provider names) and list failed attempts per provider separately. 3 tests. |
| B99 | M | `sort_by` was passed to `getattr(Model, ...)` in six admin lists. `sort_by=metadata` or `__class__` returned 500, and the users list could be ordered by `hashed_password`. | `resolve_sort_column()` accepts only real table columns and never secret ones; unknown values fall back to the default. 21 parametrized cases. |
| B100 | M | AI Configuration showed environment defaults, not what the app really uses, accepted any text as a provider and left a dead "masked key" block. | GET returns the effective config and which values are overridden; PUT validates provider and model names (422 on bad input). Provider lists match what the backend can run. |
| B101 | M | With `AI_PROVIDER=dev_gemini` retrieval embeddings were silently switched off, so chat only used keyword search. | `dev_gemini` and `gemini` both select the Gemini embedder; if the call fails BM25 still answers. Behaviour change: Gemini embedding calls now happen for dev_gemini. Test added. |
| B102 | L | The model catalogue listed PubMedBERT retrieval, but nothing in the app reads its output. | Removed from the catalogue, the evaluation script and the docs (8 models remain, 6 deep learning). The report-type classifier stays, labelled "research model, not in the live app". |
| B103 | H | Support Desk queue was always empty: the page read `data.tickets` but the API returns `items`. The "unassigned" filter used `is None` in Python (so it never filtered), searching by ticket id returned 500 on UUID `ilike`, `assigned_admin_id=abc` returned 500 and there was no pagination. | Page reads `items` with Previous/Next and a count, Open tab uses `open_only`, filters are real SQL, ticket id and user e-mail search work, bad ids return 422. Tests added. |
| B104 | H | Admin replies to a support ticket returned 500 (`sender_id` was sent as text to a UUID column), so no admin reply ever reached the app. Timeline events printed raw enum and ids. | Reply stores a UUID. Public replies appear in the app, internal notes stay private. Timeline reads "Status changed to Resolved" and "Assigned to <name>". New "Assigned to / Assign to me / Unassign" control on the ticket page. Tests added. |
| B105 | H | Reset Password and Break-Glass Approve always failed: the backend demands a step-up token and the portal never asked for one. | New step-up dialog (password and authenticator code) used by both actions. Controls the admin's role cannot use are hidden instead of failing. |
| B106 | M | Global search in the top bar returned 500 (audit-log rows read a `severity` column that does not exist), the notification search returned 500 and the audit permission name never matched. | Fixed; the fuzz run of 141 odd requests now gives 0 server errors. |
| B107 | H | Sending a broadcast notification returned 500 (wrong token field, a log column that does not exist, wrong audit call). The notification list on the user page crashed as soon as a user had a notification. | Fixed in `admin_notifications.py`, `admin_users.py`, `admin_automation_ops.py`. The result now says how many were delivered and how many failed. Tests added. |
| B108 | M | On the user page three tabs returned 500 for any user with data: Analyses (no `status` column), Chats (no `updated_at`) and Support (`subject` is `title`). | Fixed; a test opens every tab for a user who has data. Raw analysis error text is not shown, only the failure category. |
| B109 | M | Roles accepted misspelled permission names and silently created empty permissions, so a role looked configured but granted nothing. | Unknown permission names return 422 on create and update. |
| B110 | L | The Feature Flags page gave no hint which flags the app reads (`rag_hallucination_guard`, `experimental_medical_verifier`); a missing flag counts as off. | "Flags the app uses" panel with one-click Add; delete asks for confirmation. |
| B111 | L | Admin Copilot answered from a hard-coded model, ignored the app's provider chain and swallowed errors. Governance, Privacy and Jobs pages duplicated other pages. | Removed with their backend routes, tests and six stray one-off conversion scripts in the admin folder. |
| B112 | L | Several admin pages called the API with raw `fetch`, showing only "Action failed". | They use the shared client and show the server's message. |

Update to B33: `app/ml/` is still not used for live predictions, but it now holds the evaluation and XAI code, and the classifier is shown in the UI as classical ML (not deep learning) with its measured scores. Its 100% test accuracy is probably a property of the three MRAD sources, not clinical accuracy; this is stated in the UI and the document.

Model performance feature, not run here: scores for the deep-learning models (NER, Gemini and MiniLM retrieval, LLM chain, Qwen, Whisper) need your machine (model downloads, API keys, macOS `say` for the speech test). Run `cd mednarrate-backend && python scripts/evaluate_models.py`. Dart files were only syntax-checked; run `flutter pub get`, `flutter analyze`, `flutter test test/ai_models_test.dart`.

Not built: reading data from a smartwatch over Bluetooth. Most watches (Apple, Samsung, Fitbit, Garmin, Mi Band) do not expose readings over open Bluetooth; they sync to their own app or to Apple Health / Health Connect. The practical route is Apple HealthKit and Android Health Connect (one integration covers most watches) and needs native permissions, a privacy-policy update and a real device to test.

Left in English on purpose: drug names and the specialty list, the exported PDF, the developer boot screen and the dev reset-token label, the support ticket's pre-filled subject, the Android notification channel name, the Terms of Service and Privacy Policy text, the 366 daily health tips, and report content produced by the AI (use the Translate button). The translations are machine-drafted: have a native speaker review them before release. **Not compiled or run here**: run `flutter gen-l10n` (or `flutter pub get` / `flutter run`, which regenerate it), then `flutter analyze` and `flutter test`.

Not done: live Groq calls and real-device recording were not exercised from the sandbox (Android, iOS, macOS microphones and Indic-language accuracy are untested). Run `llm_check` and `translation_check` on your machine, and try the microphone in each language you plan to support.

## Addendum 4 - pre-deployment audit and cleanup (2026-10-18)

Nothing here has been committed, pushed or deployed. Flutter could not be compiled in the sandbox, so the Dart changes (read-aloud, two removed files) need `flutter pub get && flutter analyze && flutter test` on your machine.

**Verified in the sandbox**

- Backend suite on SQLite: 594 passed, 3 skipped.
- Backend suite on a real PostgreSQL 16 with pgvector: 594 passed, 3 skipped (593 on the full run, plus the new provider-list test run on its own).
- Fresh PostgreSQL: all 35 Alembic migrations apply (42 tables) to the single head `110ba6a7df09`; `downgrade base` then `upgrade head` works; `scripts/smoke_http.py --require-migrations` passes (auth, per-user isolation, reports, admin denial, cleanup).
- The same migrated PostgreSQL database, driven through the admin API: every admin GET (103 paths), a query-parameter fuzz (141 requests, 0 server errors) and 21 create/edit/delete flows pass.
- Admin portal: `tsc` clean, `eslint` clean, 89 Jest tests pass, `next build` succeeds (32 pages), `npm audit --omit=dev` finds 0 vulnerabilities.
- Static scan of `app/`, `tests/`, `scripts/`: no undefined names or syntax errors. `bandit` (medium and above): 4 hits, all reviewed (below).
- Routes without a login dependency: 13, all intended (login, signup, refresh, password reset, MFA verify and recover, logout, health, the public maintenance flag and announcements, the account-deletion page).
- No API keys or credentials in the working tree or in git history (the only `AIza...` strings are fake keys in redaction tests).

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| B113 | M | `GET /admin/automation-ops/jobs?status=<anything else>` returned 500 on PostgreSQL: the column is a native enum and the raw string reached the database. SQLite does not enforce enums, so no test saw it. Found by running the API on PostgreSQL. | The value is validated and the endpoint answers 422 with the allowed values. Test added. |
| B114 | M | The default `GEMINI_FALLBACK_MODELS` named two retired models (`gemini-2.5-flash`, `-flash-lite`). Every translation made two calls that always returned 404. | Default is empty; set it only to models your key can call. |
| B115 | M | In development every SQL statement and its parameters (hashes, report text, embeddings) was printed to the terminal, which buried real errors. | New `DB_ECHO` setting, default false. |
| B116 | M | `.gitignore` gaps: the backend `.gitignore` ended in UTF-16 text git cannot read (its model-file rules never applied); `storage/` was ignored only by the blanket `*.pdf` rule; a Firebase service-account key was not ignored. | Backend `.gitignore` rewritten; `storage/`, `uploads/`, service-account keys and one-off `*.tar.gz` bundles ignored at the root. |
| B117 | L | `test_retry_pending_orphan_files` wrote a PDF into the real `storage/` folder on every run and the test mocks the deletion, so the file stayed. | Test no longer writes files. |
| B118 | L | Start-up noise: two pydantic "protected namespace" warnings; ChromaDB telemetry errors on every start (it calls `posthog.capture` with the pre-6.0 signature); an unhelpful Firebase message. | `protected_namespaces=()` on the two schemas; `posthog<6` pinned; the Firebase message says what to set. |
| B119 | L | Dead code: 10 helpers with no call site (`mask_secret`, `require_all_permissions`, `require_active_break_glass`, `get_schema_revision`, `is_email_delivery_configured`, `classify_entity_category`, `get_embedding_model`, `get_all_jobs`, `OCRFailedError`, `catalog_entry`); unused imports and variables; a block of stream-of-consciousness comments in `admin_health.py`; 7 unused npm packages and 3 unused UI files in the admin portal; two unused Dart files (`app_constants.dart`, `report_repository.dart`). | Removed. Each removal was checked for references first. |
| B120 | M | About 110 scratch files from debugging were committed: root `test_*.py`, `debug_*.py`, `temp_*.py`, captured model output, one-off patch scripts that rewrite source files, and `scripts/seed_db.py`, which creates `test@mednarrate.com` with the password `password123` (and uses a column that no longer exists). | Removed (kept in a backup folder on your machine). 33 stale audit and status reports moved to `docs/archive/` with a note that they are historical. |
| B121 | L | `bandit` flagged MD5 in the feature-flag rollout bucketing. | `usedforsecurity=False` (it only spreads users into percentage buckets). |

**New: read-aloud.** The patient summary now has a Listen button. It uses the phone's own text-to-speech voice (`flutter_tts`), so nothing is sent anywhere and there is no cost or key. It reads the language of the translation on screen, shows a message when the phone has no voice for that language, and strips markdown before speaking. The new strings are in all eight `.arb` files and were not reviewed by native speakers. Not tested on a device.

**Reviewed and left as is**

- Migrations are PostgreSQL-only (`DEFAULT now()`, `CREATE EXTENSION vector`). A fresh SQLite database cannot be built from them, so `run_server.py` on a new checkout with SQLite stops at `001_initial`. PostgreSQL is the documented and production database; your existing SQLite file works because it predates this. Do not expect to move local SQLite data to PostgreSQL with Alembic.
- `alembic check` reports type differences between the models and the migrated schema (JSON vs JSONB, naive vs timezone-aware timestamps, `Enum` vs `VARCHAR`, `String(36)` vs `UUID` on `support_ticket_help_articles.attached_by`). The migrated schema passes the smoke test, the fuzz and the write flows, so these are not failing today, but the test suite builds its PostgreSQL schema from the models, not from the migrations. A migration that aligns them is the proper fix and is a decision for you.
- `/health` is public and shows the database driver and schema revision. It is used by Docker and CI health checks; it holds no secrets.
- `hf_hub_download` for the optional local Qwen model is not pinned to a revision (bandit B615). It only runs if you enable the local model.
- Gemini's free tier allows 15 requests a minute. A single report plus a translation can exceed it, which produced the 429 errors in your log. Make Groq the primary provider in Admin, AI Configuration, and keep Gemini as the fallback.
- The `lib/l10n/app_localizations*.dart` files in git are old build output (199 of 766 strings). Flutter regenerates them on every build, so they are harmless, but they are better removed from git.
- Several source files that the app needs are not yet in git (for example `lib/core/l10n/*`, `lib/features/voice_input/*`, `lib/features/settings/screens/ai_models_screen.dart`, `mednarrate-backend/app/api/v1/speech.py`, `app/ml/`). Run `git status` and add them before committing, or the build from a fresh clone will fail.

**Late fix (B122).** The admin AI Configuration page offered only Gemini, Vertex AI and Ollama as the primary provider, so Groq could not be chosen from the UI. The page now also lists Groq (gpt-oss), Groq (Qwen) and OpenRouter, and the server accepts `groq_qwen`. A test checks that every provider the page offers is accepted.
