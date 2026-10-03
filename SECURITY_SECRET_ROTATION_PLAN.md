# SECURITY SECRET ROTATION PLAN

This document provides the standard operating procedure (SOP) for rotating critical production credentials in the MedNarrate ecosystem safely.

## 1. Rotating Backend `JWT_SECRET`
A compromised or aged `JWT_SECRET` requires rotation. Because the frontend relies on JWTs for maintaining sessions, rolling this secret immediately logs out all active users.

### Step-by-Step Execution:
1. **Prepare New Secret**: Generate a secure, cryptographically random key.
   ```bash
   openssl rand -hex 32
   ```
2. **Communicate with Users/Clients**:
   - Send out an advance notification using the Admin "Announcements" feature, alerting clients of a mandatory re-authentication window.
   - If rolling due to a suspected breach, bypass advance notification and proceed immediately.
3. **Update Infrastructure Config**:
   - Set the newly generated key as the `JWT_SECRET` environment variable in your production orchestrator (e.g., Kubernetes Secrets, AWS Secrets Manager, or production `.env` if standalone).
4. **Deploy and Restart**:
   - Rolling restart backend services to pick up the new secret immediately.
   ```bash
   docker-compose up -d --force-recreate backend
   ```
5. **Clear Client Caches (If Supported)**:
   - For web users, existing access and refresh tokens will immediately 401. The Next.js and Flutter clients are built to intercept global 401s and return the user to the login screen, effectively self-healing.

### Verification:
```bash
# Obtain a new token (using an admin account)
curl -X POST https://api.mednarrate.com/api/v1/auth/login -d "username=admin&password=NEW_PASSWORD"

# Ensure the new token works on an authenticated route
curl -H "Authorization: Bearer <NEW_TOKEN>" https://api.mednarrate.com/api/v1/users/me
```

## 2. Rotating `GEMINI_API_KEY` (AI Provider Credentials)

MedNarrate supports updating AI Provider keys directly via the Admin dashboard without service restarts, since the AI Configuration is stored securely in the database (`system_settings`) and cached dynamically.

### Step-by-Step Execution:
1. **Generate New Credential**:
   - In Google Cloud Console / AI Studio, generate a new API key.
2. **Update via MedNarrate Admin Portal**:
   - Log into the Next.js Admin Panel.
   - Navigate to `AI Operations -> AI Configuration`.
   - Update the **API Key** field with the new credential.
   - Click **Save Changes**. The backend automatically encrypts the key using the current `JWT_SECRET`-derived master key and immediately propagates it.
3. **Verify Provider Health**:
   - In the same Admin Panel, click **Test Connection** to ensure the new credential is valid and the model is reachable.
4. **Revoke Old Credential**:
   - Once traffic successfully routes through the new key, return to Google Cloud Console / AI Studio and delete the old API key.

### Verification (CLI Fallback):
If the admin panel is inaccessible, you can rotate it directly by calling the API using an existing Admin JWT:
```bash
curl -X PUT https://api.mednarrate.com/api/v1/admin/ai-config \
  -H "Authorization: Bearer <ADMIN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_NEW_GEMINI_API_KEY"}'
```

## 3. Database URL Rotation
1. Update `DATABASE_URL` in your production orchestrator.
2. Ensure the new host strictly supports TLS/SSL connections.
3. Restart the MedNarrate Backend services. Verify by monitoring the `/api/v1/health` endpoint.

---
**CRITICAL**: *Never* commit updated `.env` configurations or raw API keys to Git history. Use secure secret management pipelines exclusively for production roll-outs.
