# Admin Health Diagnosis

**Current status**: `degraded`

**Degraded services**: 
- `llm_provider`

**Root cause**:
The LLM provider (`dev_gemini`) is marked as `configured: false` and `reachable: false`. The `admin_health.py` logic strictly requires a successful test request and a success rate >= 80% across the last 10 requests to mark the LLM service as `healthy`. Without proper configuration for the dev environment, it returns `unknown` and drops the overall system health to `degraded`.

**Evidence**:
`GET /api/v1/admin/system/health` returns:
```json
{
  "status": "degraded",
  "services": {
    "llm_provider": {
      "status": "unknown",
      "error_summary": "Provider not configured",
      "details": {
        "provider": "dev_gemini",
        "configured": false,
        "reachable": false,
        "healthy": false,
        "recent_success_rate": 60.0,
        "threshold_required": 80.0
      }
    }
  }
}
```

**Affected dependency**:
- The Primary LLM Provider API (`dev_gemini` / `google.generativeai` / `google.genai`).

**How to reproduce**:
1. Run the backend server without configuring valid Gemini API credentials.
2. Authenticate as an admin.
3. Make a `GET` request to `/api/v1/admin/system/health`.

**Correct fix**:
1. Configure the `.env` file with a valid API key for the LLM Provider (`GEMINI_API_KEY`).
2. Ensure the LLM client correctly attempts a health check request.
3. Fix the deprecation and `chromadb` import errors in `app/services/rag.py` to ensure other AI health checks do not fail after LLM is restored.

**Required tests**:
- Unit test mocking the `llm_client_instance.get_provider` to return `reachable: true` and a recent success rate of `100.0`, verifying the health endpoint returns `healthy`.
- Unit test mocking a failure to verify the endpoint correctly falls back to `degraded`.
