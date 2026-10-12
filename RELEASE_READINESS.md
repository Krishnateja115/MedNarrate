# MedNarrate release readiness

This checklist separates reproducible code checks from deployment inputs. A
successful local build with an example URL is not a deployable package.

## Verified in this repository

- Backend migrations have one Alembic head. Production startup requires an
  applied schema and rejects SQLite, weak JWT secrets, wildcard CORS, and
  in-process report analysis.
- Flutter release builds require a public HTTPS `API_BASE_URL`. Offline cache
  and queued report bytes use encrypted Hive boxes scoped to the signed-in
  account. Medicine alerts run on the phone in local time; server push is off
  in production to avoid duplicate or timezone-incorrect reminders.
- Admin web builds require an explicit HTTPS `MEDNARRATE_API_PROXY_URL`.
  Desktop builds require an explicit HTTPS `NEXT_PUBLIC_API_BASE_URL`.
- Android release signing no longer falls back to a debug key.

## Configure before deployment

1. **Identity and domains:** Choose the permanent Android application ID,
   Apple bundle ID, API domain, and admin portal domain. Register the domains
   and certificates. Replace the current `com.example.mednarrate` IDs before
   uploading to an app store or registering Firebase apps.
2. **Backend:** Provision managed PostgreSQL, shared object storage, an API
   service, and an independent analysis worker. Put `DATABASE_URL`,
   `JWT_SECRET`, `ENVIRONMENT=production`, `ANALYSIS_EXECUTION_MODE=worker`,
   exact `CORS_ORIGINS`, `ADMIN_APP_ORIGIN`, storage settings, and chosen AI
   provider credentials in the host's secret manager. Apply `alembic upgrade
   head` before starting the API and worker. Configure a shared rate-limit
   store for multiple API replicas. Set backup, restore, retention, and alert
   procedures for medical data.
3. **Mobile:** Supply a public HTTPS URL with
   `--dart-define=API_BASE_URL=https://your-api-domain` and
   `--dart-define=ENVIRONMENT=production`. Create `android/key.properties`
   from `android/key.properties.example` using a release keystore kept outside
   Git. Configure Apple signing in Xcode. If remote push is required, create
   Firebase apps for the final identifiers and install the Android/iOS config
   files through a secure release pipeline. Local medicine alarms do not need
   Firebase.
4. **Admin:** Set `MEDNARRATE_API_PROXY_URL` for the web build, or
   `NEXT_PUBLIC_API_BASE_URL` for Tauri. Configure and verify secure admin
   cookies, CORS, and production TLS. Sign desktop packages for distribution.
5. **Public policy:** Replace the in-app privacy policy's provisional
   third-party-service paragraph with the actual hosting, storage, AI,
   monitoring, retention, and deletion terms. Have the final text reviewed for
   the jurisdictions where the app will launch.

## Release verification on the deployed environment

- Run backend tests against PostgreSQL and migrate a fresh database.
- Verify login, MFA, admin permissions, and account deletion with test users.
- Upload a synthetic medical report and an unrelated document; confirm the
  worker completes one and rejects the other. Restart the worker during a job
  and confirm it resumes. Check object download and deletion permissions.
- On real Android and iOS devices, check upload, analysis, every supported
  translation, chat, offline cache, queued upload, local medication alarm,
  notification tap, biometric lock, logout, and account switching.
- Exercise admin pages and mutations against the deployed API. Check failed
  provider responses, rate limits, 401/403 behavior, logs without patient
  content, backup restore, and alerts.
- Build and sign the final app artifacts using the actual domains and IDs.
  Do not distribute an APK built with `api.example.com` or a debug key.

## Optional live tests

The normal backend suite does not contact an AI provider. Use
`RUN_LIVE_LLM_TESTS=1 pytest -q` in a controlled environment after credentials
and quotas are configured. Use synthetic documents only.
