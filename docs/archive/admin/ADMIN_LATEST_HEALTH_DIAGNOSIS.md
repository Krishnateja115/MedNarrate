# Admin Health Diagnosis

## 1. Overall Status
**Current State**: `DEGRADED`

## 2. Dependency Probe Results

The `admin_health.py` service performs the following dependency probes:

| Service | Real Status | Cause |
| :--- | :--- | :--- |
| **API** | `healthy` | Serving requests normally. |
| **Database** | `healthy` | `SELECT 1` completes successfully (latency ~2ms). |
| **LLM Provider** | `reachable` | Provider is reachable, but recent success rate is 70% (threshold requires 80%). The health service explicitly downgrades `healthy` to `reachable` if the telemetry success rate is poor. |
| **Storage** | `healthy` | File write check passed on `UPLOAD_DIR`. |
| **Scheduler** | `stopped` | `APScheduler is not running`. |
| **RAG** | `healthy` | Vector store responds correctly. |

## 3. Root Cause of DEGRADED Status

The `DEGRADED` status in the MedNarrate Admin platform is strictly caused by:

1. **LLM Provider Success Rate Drop**:
   - The probe checks the last 10 requests in `llm_diagnostic_events`.
   - The required threshold for `healthy` is 80.0%.
   - The actual recent success rate is 70.0%.
   - This sets `llm_status = "reachable"`.
   - The final assertion checks: `all_healthy = all(health_status["services"][s] == "healthy" for s in core_services)`. Because `llm_provider` is only `"reachable"`, `all_healthy` is `False`, pushing the overall status to `DEGRADED`.

2. **Scheduler Stopped**:
   - `scheduler.running` returns `False`.
   - The health probe correctly notes `APScheduler is not running` and forces the overall status to `DEGRADED`.

## 4. Remediation

Do **NOT** simply change the threshold or mock the health values to "healthy".
To resolve the `DEGRADED` status:
- The APScheduler must be explicitly started (`scheduler.start()`).
- The LLM diagnostic event table's success rate must rise above 80% (either by sending successful requests or clearing legacy failed telemetry).
