# MedNarrate Admin Security Review

## Threat Matrix

### 1. Insecure Break-Glass Approval
**Attack scenario:** An admin requests sensitive access and immediately approves their own request, bypassing multi-party authorization.
**Current protection:** None previously.
**Defect:** `admin_breakglass.py` allowed self-approval or auto-activated requests for super admins.
**Fix:** Modified `admin_breakglass.py` to strictly enforce a REQUESTED -> APPROVED -> ACTIVE lifecycle. A separate `approve` endpoint ensures the `admin_ctx.user_id` does not match the requester ID.
**Test:** `tests/test_breakglass_security.py` (Scenario B)
**Result:** Pass
**Remaining limitation:** Super Admins can still manage roles, so a malicious Super Admin could theoretically create a secondary account to approve their requests. This requires external auditing of Super Admin actions.

### 2. Unauthorized Sensitive Data Access (IDOR/Privilege Escalation)
**Attack scenario:** An admin with basic `reports.view` permission queries `GET /api/v1/admin/reports/{id}` and accesses raw medical text.
**Current protection:** None previously.
**Defect:** The base report endpoint returned all fields, including `extracted_text`.
**Fix:** Separated endpoints. `GET /reports/{id}` strips sensitive fields. Created `GET /reports/{id}/sensitive` requiring both `reports.sensitive_view` and an active break-glass grant via `require_active_break_glass()`.
**Test:** `tests/test_breakglass_security.py` (Scenarios C & D)
**Result:** Pass
**Remaining limitation:** None.

### 3. Audit Log Manipulation & Atomicity Failures
**Attack scenario:** An admin performs a privileged action (e.g. reprocessing a report), the action succeeds, but the audit log write fails, leaving no trace.
**Current protection:** `log_admin_action` was called, but transaction commits were misaligned.
**Defect:** Audit logs were written after the business mutation commit, or committed in nested helpers.
**Fix:** Rewrote admin mutations to ensure the business mutation and audit log are added to the session, followed by a single atomic `await db.commit()`.
**Test:** `tests/test_security_regression.py` (Audit atomicity)
**Result:** Pass
**Remaining limitation:** Database-level manipulation by someone with raw SQL access cannot be prevented by application logic.

### 4. AI Configuration Secret Exposure
**Attack scenario:** An admin views the AI configuration settings and inspects the API response to retrieve the provider API key.
**Current protection:** A partial mask `sk-xxx****xxx` was used.
**Defect:** Partial masks can still leak prefix/suffix information which is a security risk.
**Fix:** The `GET /ai-config` endpoint now only returns an `is_set` boolean. Added a safe `/test-credential` endpoint that tests connectivity without returning the key.
**Test:** `tests/test_ai_config_security.py`
**Result:** Pass
**Remaining limitation:** API keys are stored in the database. A fully robust solution would use a dedicated secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).

### 5. Error Message Leakage
**Attack scenario:** An attacker intentionally sends malformed requests to trigger 500 errors, reading stack traces and SQL queries from the response to find vulnerabilities.
**Current protection:** Basic FastAPI exception handling.
**Defect:** Pydantic validation errors included raw input values (which might contain secrets). Unhandled exceptions could leak implementation details.
**Fix:** Updated `app/exceptions.py`. Validation errors are sanitized to remove raw inputs. 500 errors return a generic message with a correlation ID, while full stack traces are logged server-side only.
**Test:** `tests/test_security_regression.py` (Error leakage)
**Result:** Pass
**Remaining limitation:** Requires log management system to secure the server-side logs.

---

## Authorization Matrix

This matrix describes the permissions required for key admin actions.

| Resource | Action | Support Agent | AI Admin | Security Admin | Super Admin |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Users** | View | Yes | No | No | Yes |
| **Reports** | View (Metadata) | Yes | No | No | Yes |
| **Reports** | Sensitive View | *Requires Break-Glass* | No | No | *Requires Break-Glass* |
| **Reports** | Manage (Retry) | No | No | No | Yes |
| **Chat** | View (Metadata) | Yes | Yes | No | Yes |
| **Chat** | Sensitive View | *Requires Break-Glass* | *Requires Break-Glass* | No | *Requires Break-Glass* |
| **Roles** | Manage | No | No | No | Yes |
| **AI Config** | View / Configure | No | Yes | No | Yes |
| **Audit Logs** | View | No | No | Yes | Yes |
| **Break-Glass**| Request | Yes | Yes | Yes | Yes |
| **Break-Glass**| Approve | No | No | Yes | Yes |

*Note: Break-glass approval requires a different administrator than the requester.*
