# MedNarrate Admin - Deployment Guide

## Architecture Overview
The MedNarrate platform comprises three decoupled tiers:
1. **Flutter Mobile App**: Patient-facing clinical portal.
2. **FastAPI Backend**: Core API powering both the mobile app and the admin portal. (State resides in PostgreSQL).
3. **Next.js Admin Frontend**: Independent React application for administrative governance.

## CI/CD Pipeline
A GitHub Actions workflow (`ci.yml`) automatically triggers on push to `main` and `develop`. It validates:
- `pytest` suite running against an ephemeral `aiosqlite` container.
- Docker build integrity for the backend.
- `flutter test` and `flutter analyze` for the mobile codebase.
- `npm run lint` and `npm run build` for the Next.js admin frontend.

## Environment Configuration
### Backend `.env`
Required variables for the FastAPI server:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
JWT_SECRET=super_secure_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
```
*(Note: GEMINI_API_KEY is configured via the Admin UI, not `.env`, to support dynamic failover).*

### Frontend `.env.local`
Required variables for the Next.js admin app:
```
NEXT_PUBLIC_API_URL=https://api.mednarrate.com
```

## Deployment Strategy
**Admin Frontend**:
- Run `npm ci` and `npm run build`.
- Deploy the resulting `.next` standalone folder or use a managed provider like Vercel. Ensure `NEXT_PUBLIC_API_URL` correctly targets the environment's FastAPI backend.

**FastAPI Backend**:
- Run via Docker: `docker build -t mednarrate-backend .`
- Or run natively: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
- Apply Alembic migrations prior to backend initialization: `alembic upgrade head`.
