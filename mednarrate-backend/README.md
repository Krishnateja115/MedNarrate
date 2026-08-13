# MedNarrate Backend

Backend for the MedNarrate AI medical report analyzer.

## Setup

1. Copy `.env.example` to `.env` and fill the environment variables:
   - `DATABASE_URL`: The asyncpg connection string to the PostgreSQL database.
   - `JWT_SECRET`: Secret key for JWT signing.
   - `UPLOAD_DIR`: Directory where uploaded reports are stored.

2. Start the database and API via Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Run migrations:
   ```bash
   # Wait for the API container to start, it runs migrations on boot.
   # Alternatively run manually:
   docker-compose exec api alembic upgrade head
   ```

## Development
To run tests (requires a running DB instance):
```bash
docker-compose exec api pytest
```

## API Endpoints (Current Table)
| Method | Path | Description |
|---|---|---|
| POST | /api/v1/auth/signup | Register a new user |
| POST | /api/v1/auth/login | Login and obtain tokens |
| POST | /api/v1/auth/refresh | Refresh access token |
| POST | /api/v1/auth/logout | Logout user |
| GET | /api/v1/auth/me | Get current user info |
| GET | /api/v1/users/me | Get current user with medical profile |
| PATCH | /api/v1/users/me | Update user / medical profile |
| POST | /api/v1/reports/upload | Upload a medical report |
| GET | /api/v1/reports | List user's reports |
| GET | /api/v1/reports/{id} | Get report details |
| PATCH | /api/v1/reports/{id} | Update report details |
| DELETE | /api/v1/reports/{id} | Delete a report |

Note: If scaling past a single worker, `slowapi` rate limiting will require Redis setup.
