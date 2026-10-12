# Automated testing

Every push and pull request starts the [CI workflow](.github/workflows/ci.yml).
The **Automated release gate** turns green only when all required jobs pass.
You can also start the workflow manually from GitHub Actions.

| Check | What it exercises |
| --- | --- |
| Backend on SQLite | FastAPI endpoint and service tests without external AI calls. |
| Backend on PostgreSQL | Fresh Alembic migration, downgrade and upgrade, real HTTP authentication and access checks, then the full backend suite on an isolated PostgreSQL database. |
| Flutter | Static analysis and widget/unit tests. |
| Mobile UI | Launches the app in an iPhone simulator and checks login form validation, signup navigation, and privacy navigation. |
| Admin | Lint, type checking, Jest tests, and a production build. |
| Admin browser | Chromium checks protected-route redirects, invalid login, and patient access denial. |
| Docker and security | Backend image build and hardening checks, Git secret scan, and a production npm dependency audit. |

The separate Python dependency audit publishes a report but is currently
advisory because the pinned ML packages have unresolved advisories. Review
that report before a release; a green gate does not clear those findings.

## Run locally

Use the repository versions of Python, Flutter, Node, and required system
dependencies described in [README.md](README.md). From the repository root:

```sh
cd mednarrate-backend
PYTHONPATH=. pytest -q
```

```sh
flutter analyze --no-fatal-infos
flutter test
flutter test integration_test/mobile_auth_smoke_test.dart -d <booted-ios-simulator-id>
```

```sh
cd mednarrate-admin
npm ci
npm run lint
npm run typecheck
npm test -- --ci
npm run test:e2e
MEDNARRATE_API_PROXY_URL=https://api.example.com npm run build
npm audit --omit=dev --audit-level=high
```

The browser test starts a temporary local admin server. The iOS integration
test needs Xcode and a booted iPhone simulator. Linux CI runs the Flutter
unit/widget suite; macOS CI runs the iPhone simulator suite.

The HTTP smoke script runs only against a local disposable backend and
database. After applying Alembic migrations and starting the API, run:

```sh
cd mednarrate-backend
python scripts/smoke_http.py --require-migrations
```

It creates a synthetic account, tests access boundaries, and deletes the
account. Never point tests at patient data. CI prepares its own PostgreSQL
database and runs this script automatically.

## Checks still needed for a release

Automation cannot establish clinical accuracy, third-party AI reliability,
or behavior on every physical device. Follow the deployed-environment checks
in [RELEASE_READINESS.md](RELEASE_READINESS.md): signed Android and iOS builds,
real device upload and offline flows, worker recovery, admin actions, backups,
alerts, and an approved privacy policy. Live AI tests are opt-in with
`RUN_LIVE_LLM_TESTS=1` and must use synthetic documents.
