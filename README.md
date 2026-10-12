# MedNarrate

MedNarrate helps people review medical reports with a Flutter app, a FastAPI
service, and a staff admin portal. AI results are informational and must be
checked against the source report and a qualified clinician.

## Components

- `lib/`, `android/`, `ios/`, `macos/`, `windows/`: Flutter client. Reports and
  chat can be read from an encrypted account-scoped cache when offline. New
  report uploads can be queued in encrypted local storage and retried online.
- `mednarrate-backend/`: FastAPI, PostgreSQL, Alembic, report analysis worker,
  file storage, and admin APIs.
- `mednarrate-admin/`: Next.js admin portal.
- `mednarrate-admin-desktop/`: Tauri package for the admin portal.

## Local development

Use Python 3.11 and Flutter 3.47 or a compatible stable release. Configure the
backend from `mednarrate-backend/.env.example` using a local `.env` file. The
required secret is named `JWT_SECRET`. Apply migrations with
`cd mednarrate-backend && alembic upgrade head`, then start the API with
`python run_server.py`. Set up an AI provider before testing report analysis.

From the repository root, run `flutter pub get` and `flutter run`. On Android
emulators the local backend defaults to `10.0.2.2:8000`; other devices need an
explicit `--dart-define=API_BASE_URL=...`.

For the admin portal, run `cd mednarrate-admin && npm ci && npm run dev`. It
listens on port 3001 and proxies `/api/v1` to the local backend by default.

## Production release

Read [RELEASE_READINESS.md](RELEASE_READINESS.md) before deployment. Production
requires PostgreSQL migrations, an independent analysis worker, shared file
storage, configured AI credentials, a public HTTPS API, and a protected admin
origin. A release Flutter build refuses a local or non-HTTPS API URL. The admin
build refuses a missing API proxy URL. Mobile package IDs, signing credentials,
provider configuration, privacy terms, and live device checks must be completed
for the target environment.

## Automated checks

The [testing guide](TESTING.md) lists the local commands and the automated
release gate. CI exercises PostgreSQL migrations and HTTP access checks,
Flutter tests and an iPhone simulator, admin unit and Chromium browser tests,
the production build, Docker checks, and security scans.

Live AI-provider tests are opt-in with `RUN_LIVE_LLM_TESTS=1` and require valid
credentials. Do not put patient reports or secrets in test fixtures or Git.
