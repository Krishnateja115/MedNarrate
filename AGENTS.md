# MedNarrate Agent Guidelines

These are the rules and guidelines for AI coding agents working on the MedNarrate repository.

## Architecture
- Backend: FastAPI, SQLAlchemy (asyncpg), PostgreSQL, Alembic
- Frontend: Flutter, GoRouter, Hive for local caching, Provider/Riverpod for state management (refer to existing code for exact state solution).

## Coding Standards
1. **Python**: Use typing hints for all function signatures. Use Pydantic for validation. Stick to PEP 8 standards.
2. **Flutter**: Use structured folder by feature (e.g., `lib/features/auth/`). Separate UI from business logic. Always handle offline network states.
3. **Security**: Never hardcode credentials. Use `.env`. All endpoints must be secured by JWT unless explicitly public (like `/auth/login`).
4. **Testing**: Write pytest tests for backend endpoints and services. Write flutter widget and unit tests for core frontend logic.

## AI Constraints
- Do not remove existing comments unless rewriting the entire block.
- For database schema changes, you must generate Alembic migrations (`alembic revision --autogenerate -m "msg"`).

## Git Workflow (MANDATORY)
- **After every modification to any file in this project**, you MUST immediately run:
  ```
  git add -A && git commit -m "<concise description of change>" && git push origin main
  ```
- This applies to ALL changes — bug fixes, new features, config updates, test additions, documentation edits — without exception.
- Do NOT batch changes across multiple user turns before pushing. Each logical change set must be committed and pushed before moving on.
- Never ask the user whether to push. Just do it automatically every time.
