# MedNarrate Admin — Operational Workflows & Incident Management

## 1. Support Ticket Lifecycle Workflow
```
[User Report / Ticket Submitted] 
       │
       ▼
[Support Admin Views Ticket] ───► Check Related Report / User ID
       │
       ▼
[Trigger Automatic Diagnostic Run] ──► Inspect LLM Telemetry & OCR Errors
       │
       ▼
[Execute Report Retry / Resolution] ──► Update Ticket Status to Resolved
```

## 2. Failed Report Investigation Workflow
1. Navigate to `/reports` or click alert notification in Topbar.
2. Open Report details page `/reports/[id]`.
3. Inspect processing stage failure (OCR, Extraction, AI Structuring, Verification).
4. Trigger **Retry Processing**. Audit log captures `RETRY_REPORT_PROCESSING`.

## 3. Temporary Break-Glass Access Workflow
1. Navigate to `/breakglass`.
2. Click **Request Temporary Access**, input mandatory justification reason & duration.
3. System grants timed token; active status countdown timer starts.
4. Access automatically expires or can be revoked by Security Admin manually.
