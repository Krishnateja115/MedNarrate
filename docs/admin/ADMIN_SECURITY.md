# MedNarrate Admin — Security Architecture & Governance Controls

## Security Model
1. **Least Privilege Enforcement**: Admin users are granted specific permission codes (e.g., `users.view`, `reports.manage`, `security.revoke`).
2. **Break-Glass Emergency Access**: Sensitive data viewing requires explicit justification logs and expires automatically after a set duration.
3. **Immutable Audit Logs**: Every administrative mutation generates an `AdminAuditLog` record containing actor ID, target resource, timestamp, IP address, user agent, and action severity.
4. **CORS & Credentials Hardening**: Strict origin matching. `allow_credentials=True` is disabled when wildcard origins `*` are configured.
5. **Prompt Injection & AI Guardrails**: Backend input sanitization middleware checks POST payloads for prompt override patterns.
6. **PHI / PII Redaction**: Diagnostic logs and LLM telemetry strictly exclude raw medical report text and patient identifying information.
