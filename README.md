# 🏥 MedNarrate — AI Medical Report Analysis

MedNarrate is a full-stack AI-powered application that helps patients and clinicians understand complex medical lab reports through plain-language summaries, trend analysis, RAG-based Q&A, and multilingual support.

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Backend (FastAPI)](#backend-fastapi)
  - [Flutter App](#flutter-app)
  - [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Running Tests](#running-tests)
- [CI/CD](#cicd)
- [Project Structure](#project-structure)

---

## Architecture Overview

```
┌────────────────────────────────┐     ┌─────────────────────────────┐
│      Flutter Mobile App        │────▶│     FastAPI Backend (Python) │
│  (Reports, Chat, Insights)     │◀────│  Auth · Reports · Analysis   │
└────────────────────────────────┘     │  RAG · Notifications         │
                                       └──────────┬──────────────────┘
                                                  │
                                    ┌─────────────▼─────────────┐
                                    │   PostgreSQL / SQLite      │
                                    │   (prod / test)           │
                                    └───────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile | Flutter 3.x (Dart) |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 16 (prod) / SQLite (testing) |
| Auth | JWT (access + refresh tokens, bcrypt hashes) |
| AI | Google Gemini 1.5 Flash (summaries) |
| NLP | HuggingFace Transformers (NER pipeline) |
| RAG | BM25 + Gemini Embedding (text-embedding-004) |
| OCR | PyMuPDF / google_mlkit_text_recognition |
| Storage | Local filesystem (Docker volume) |
| CI/CD | GitHub Actions |

---

## Features

- 📄 **PDF/Image Report Upload** — secure upload with magic-byte validation and UUID file naming
- 🤖 **AI Analysis Pipeline** — NER → lab value extraction → Gemini summaries (clinician + patient)
- 💊 **Medication Scheduling** — AI-extracted medication reminders with local notifications
- 🌐 **Multilingual** — patient summaries translated to Hindi (`hi`) and Telugu (`te`)
- 💬 **RAG Chat** — per-report chat sessions with BM25 / semantic retrieval
- 📊 **Health Insights** — cross-report trend charts with fl_chart
- 🔐 **Security** — refresh token rotation, ownership middleware, rate-limiting (slowapi), security headers
- 📴 **Offline Mode** — cached reports via Hive with connectivity banner
- 🔑 **Biometric Auth** — local_auth fingerprint / face unlock
- 🌍 **Professional Mode** — role-aware prompts for doctors vs. patients

---

## Getting Started

### Prerequisites

- Python 3.11+
- Flutter SDK 3.22+
- PostgreSQL 16 (for production) or Docker

---

### Backend (FastAPI)

```bash
cd mednarrate-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, GEMINI_API_KEY

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### MRAD Dataset Ingestion

The backend uses a local ChromaDB instance populated from the MRAD dataset for context. To ingest the data:

```bash
cd mednarrate-backend
# First ingest general knowledge and examples
python scripts/ingest_mrad_dataset.py

# Then ingest lab reference ranges
python scripts/ingest_mrad_lab_references.py
```

The API will be available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

### Flutter App

```bash
# From the project root
flutter pub get

# Run on device/emulator
flutter run

# Build release APK
flutter build apk --release
```

---

### Docker Deployment

```bash
cd mednarrate-backend

# Copy and configure environment
cp .env.example .env
# Edit DATABASE_URL (use the Docker service name 'db'), SECRET_KEY, GEMINI_API_KEY

# Start all services
docker compose up --build -d

# View logs
docker compose logs -f backend

# Run migrations inside container
docker compose exec backend alembic upgrade head
```

---

## Environment Variables

Create `mednarrate-backend/.env` based on:

```env
# Database
DATABASE_URL=postgresql+asyncpg://mednarrate:mednarrate_pass@localhost:5432/mednarrate_db

# JWT Auth
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Firebase / Notifications (Optional)
FIREBASE_SERVICE_ACCOUNT_JSON=path/to/service-account.json

# Storage
UPLOAD_DIR=uploads

# App
ENVIRONMENT=development   # production | development | test
MAX_UPLOAD_SIZE_MB=10
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/signup` | Register new user |
| `POST` | `/api/v1/auth/login` | Login → access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token |
| `GET`  | `/api/v1/auth/me` | Get current user profile |
| `POST` | `/api/v1/reports/upload` | Upload medical report (PDF/image) |
| `GET`  | `/api/v1/reports` | List reports (paginated) |
| `GET`  | `/api/v1/reports/{id}` | Get report details |
| `PATCH`| `/api/v1/reports/{id}` | Update report metadata |
| `DELETE`| `/api/v1/reports/{id}` | Delete report + file |
| `GET`  | `/api/v1/reports/{id}/analysis` | Get AI analysis |
| `POST` | `/api/v1/chat/session` | Create chat session |
| `POST` | `/api/v1/chat/message` | Send message to RAG chat |
| `GET`  | `/api/v1/notifications/medications` | List medication schedules |
| `GET`  | `/health` | Health check |

---

## Running Tests

### Backend

```bash
cd mednarrate-backend
source venv/bin/activate

# All tests (uses SQLite in-memory)
PYTHONPATH=. pytest -v

# With coverage
PYTHONPATH=. pytest --cov=app --cov-report=term-missing
```

**Test suites:**
- `test_auth.py` — signup, login, token rotation, logout
- `test_reports.py` — upload, list, patch, delete, ownership
- `test_analysis.py` — lab value extraction, pipeline mocking, defensive filtering
- `test_rag.py` — chat session creation and ownership
- `test_chat_safety.py` — emergency routing, diagnosis safety checks
- `test_normalization.py` — lab value unit normalization
- `test_extraction_pipeline.py` — end-to-end extraction flow

### Flutter

```bash
# From project root
flutter test test/medication_card_test.dart \
              test/biometric_service_test.dart \
              test/insights_screen_test.dart \
              test/offline_banner_test.dart
```

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to `main` and `develop`:

1. **Backend Tests** — Python 3.11, pytest with SQLite in-memory DB
2. **Flutter Tests** — Flutter 3.22, `flutter analyze` + widget/unit tests
3. **Docker Build** — validates the Dockerfile builds successfully

---

## Project Structure

```
mednarrate/
├── lib/                          # Flutter app
│   ├── core/
│   │   ├── services/             # API, auth, biometric, cache, connectivity
│   │   ├── constants/            # App-wide constants
│   │   └── theme/                # Dark/light theme
│   ├── features/
│   │   ├── auth/                 # Login, signup screens
│   │   ├── reports/              # Upload, list, detail, analysis tabs
│   │   ├── insights/             # Multi-report comparison & charts
│   │   ├── chat/                 # RAG chat sessions
│   │   ├── reminders/            # Medication schedules
│   │   └── dashboard/            # Home dashboard
│   └── shared/widgets/           # Reusable UI components
├── test/                         # Flutter unit & widget tests
├── mednarrate-backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/v1/               # API route handlers
│   │   ├── core/                 # Config, DB, security
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response models
│   │   └── services/             # Business logic (analysis, RAG, storage)
│   ├── alembic/                  # Database migrations
│   ├── tests/                    # Pytest test suite
│   ├── Dockerfile
│   └── docker-compose.yml
└── .github/workflows/ci.yml      # GitHub Actions CI/CD
```

---

## License

MIT © 2024 MedNarrate Team
