# MedNarrate Pre-Release Security Baseline 2026
**Phase 1: Forensic Security Baseline**
**Target Repository:** `Krishnateja115/MedNarrate`
**Branch:** `main`

## Executive Summary
This document establishes the verified forensic security baseline of the MedNarrate application before any remediation is performed. The assessment evaluates the repository across core security controls, mapping both strengths and critical vulnerabilities.

---

## 1. Authentication & Token Management
*   **Git Secret Scan:** **FAIL**
    *   *Evidence:* `gitleaks` identified two exposed secrets in git history: a test environment JWT in `mednarrate-backend/out.txt` and a test API key in `mednarrate-backend/tests/test_llm_and_pipeline.py`.
*   **Token Storage (Frontend):** **FAIL**
    *   *Evidence:* The Flutter client (`lib/core/services/storage_service.dart`) stores JWTs in insecure `SharedPreferences` instead of `flutter_secure_storage`.
*   **Cookie Security (Backend):** **PASS**
    *   *Evidence:* `app/api/v1/auth.py` correctly sets `httponly=True`, `secure=settings.ENVIRONMENT == "production"`, and `samesite="strict"` for both access and refresh tokens.
*   **MFA (Multi-Factor Authentication):** **FAIL**
    *   *Evidence:* No implementation of TOTP, OTP, or recovery codes exists across the backend or frontend. WebAuthn is only used for local device-level biometric locking, not as a second factor for API authentication.

## 2. API & Network Security
*   **CORS Configuration:** **PASS**
    *   *Evidence:* `app/main.py` explicitly whitelists trusted origins (`http://localhost:3000`, `https://app.mednarrate.com`, etc.) and correctly configures `allow_credentials=True`.
*   **Rate Limiting:** **PARTIAL**
    *   *Evidence:* `slowapi` rate limits (`5/minute`) are enforced on `/auth/login`, `/auth/signup`, and password reset endpoints. However, core operational endpoints (e.g., LLM analysis, file uploads, search) lack rate-limiting protection.
*   **XSS Protection (Admin Portal):** **PASS**
    *   *Evidence:* The Next.js admin portal leverages React's default DOM escaping. No instances of `dangerouslySetInnerHTML` exist in the codebase.
*   **SQL Injection:** **PASS**
    *   *Evidence:* The backend strictly uses SQLAlchemy's async ORM. No instances of raw `text()` execution concatenating user input or dynamic `ORDER BY` vulnerabilities were found.

## 3. Data Protection & File Uploads
*   **File Upload Security:** **PASS**
    *   *Evidence:* `app/services/file_storage.py` validates maximum file size (`MAX_UPLOAD_MB`), enforces allowed extensions, verifies magic bytes (`%PDF-`, `\xff\xd8\xff`), and utilizes UUID-based randomized storage paths (`{user_id}/{uuid}.{ext}`) to prevent directory traversal.
*   **File Download Security:** **PASS**
    *   *Evidence:* `app/api/v1/reports.py` validates ownership (`verify_report_ownership`) before download. Files are served as `application/octet-stream` with `Content-Disposition: inline`, preventing browser-based execution of polyglot payloads.
*   **User & Audit Deletion (Privacy):** **FAIL**
    *   *Evidence:* The admin portal (`app/api/v1/admin_users.py`) supports account suspension but lacks hard-delete or privacy erasure endpoints. `app/api/v1/admin_audit.py` lacks data retention, archive, or purge capabilities.

## 4. LLM & AI Security
*   **AI Abuse Limits & Spend Cap:** **FAIL**
    *   *Evidence:* `app/services/llm_client.py` and `app/core/config.py` enforce `MAX_OUTPUT_TOKENS`, but no global spend cap, API budgeting logic, or circuit breakers exist.
*   **Prompt Injection Protection:** **PASS**
    *   *Evidence:* `app/main.py` implements a `prompt_injection_middleware` leveraging a regex-based blocklist (`blocklist.txt`) to intercept malicious LLM manipulation attempts before they reach the controller.

## 5. Application Configuration & Identity
*   **Production Configuration:** **FAIL**
    *   *Evidence:* `docker-compose.yml` silently defaults `JWT_SECRET` to the unsafe string `please_change_this_secret_in_production` if unconfigured. Additionally, FastAPI's `/docs` URL remains exposed in production environments (`app.py` does not disable `docs_url`).
*   **Brute Force & Password Policy:** **PARTIAL**
    *   *Evidence:* While signup (`SignupRequest` in `app/schemas/auth.py`) enforces strict password complexity (min 8 chars, upper, number, special char), the password reset flow (`ResetPasswordRequest` in `app/api/v1/password_reset.py`) completely lacks complexity validation, accepting any arbitrary string.
*   **Exception Leakage:** **PASS**
    *   *Evidence:* `app/exceptions.py` utilizes custom exception handlers (`unhandled_exception_handler`) that mask stack traces and return a generic `500 Internal Server Error` with a correlation `request_id` to the client.
