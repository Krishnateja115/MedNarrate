# Admin Frontend Integration Mapping

This document maps all verified pages in the MedNarrate Admin Web Application to their corresponding backend API endpoints, detailing the data flow, mutations, and required permissions.

## 1. Core Operations

### Dashboard (Command Center)
- **Path**: `/`
- **APIs**:
  - `GET /api/v1/admin/dashboard/metrics` (System metrics)
- **Permissions**: `dashboard.view`

### Analytics
- **Path**: `/analytics`
- **APIs**:
  - `GET /api/v1/admin/analytics/overview` (User, report, AI usage trends)
- **Permissions**: `analytics.view`

### User Management
- **Path**: `/users`, `/users/detail?id={id}`
- **APIs**:
  - `GET /api/v1/admin/users` (List users with pagination & filtering)
  - `GET /api/v1/admin/users/{id}` (User metadata)
  - `GET /api/v1/admin/users/{id}/sessions` (Active sessions)
  - `GET /api/v1/admin/users/{id}/reports` (User's reports)
  - `GET /api/v1/admin/users/{id}/medical_profile` (Sensitive medical details)
  - `GET /api/v1/admin/users/{id}/doctor_profile` (Clinician credentials)
  - `GET /api/v1/admin/users/{id}/caregiver_profile` (Caregiver relations)
  - `GET /api/v1/admin/users/{id}/security` (Security audit logs)
  - `POST /api/v1/admin/users/{id}/actions/{action}` (Suspend, reset password, etc.)
- **Permissions**: `users.view`, `users.manage`

### Medical Reports
- **Path**: `/reports`, `/reports/detail?id={id}`
- **APIs**:
  - `GET /api/v1/admin/reports` (List metadata)
  - `GET /api/v1/admin/reports/{id}` (Report metadata + analysis status)
  - `GET /api/v1/admin/reports/{id}/sensitive` (Break-glass full clinical payload)
  - `POST /api/v1/admin/reports/{id}/actions/retry` (Retry processing)
  - `POST /api/v1/admin/reports/{id}/actions/reprocess` (Full reprocessing)
- **Permissions**: `reports.view`, `reports.manage`, `reports.sensitive_view`

### Support Desk
- **Path**: `/support`
- **APIs**:
  - `GET /api/v1/admin/support/tickets` (List tickets)
  - `POST /api/v1/admin/support/tickets/{id}/reply` (Reply to ticket)
  - `POST /api/v1/admin/support/tickets/{id}/status` (Update status)
- **Permissions**: `support.view`, `support.manage`

### System Incidents
- **Path**: `/incidents`
- **APIs**:
  - `GET /api/v1/admin/incidents` (List active and resolved incidents)
  - `POST /api/v1/admin/incidents` (Declare incident)
  - `POST /api/v1/admin/incidents/{id}/resolve` (Resolve incident)
- **Permissions**: `incidents.view`, `incidents.manage`

## 2. AI & Data Ops

### Admin Copilot
- **Path**: `/admin-copilot`
- **APIs**:
  - `POST /api/v1/admin/copilot/chat` (Admin AI Assistant)
- **Permissions**: `dashboard.view`, `copilot.chat`

### AI Operations
- **Path**: `/ai-ops`
- **APIs**:
  - `GET /api/v1/admin/ai-ops/overview` (LLM telemetry metrics)
  - `GET /api/v1/admin/ai-ops/traces` (Recent traces)
  - `GET /api/v1/admin/ai-ops/failures` (Failure diagnostics)
- **Permissions**: `ai.view`, `ai.manage`

### Chat Operations
- **Path**: `/chat-ops`
- **APIs**:
  - `GET /api/v1/admin/chat-ops/sessions` (Active sessions)
  - `GET /api/v1/admin/chat-ops/safety-events` (Safety & moderation events)
- **Permissions**: `chat.view`

### RAG Knowledge Ops
- **Path**: `/rag-ops`
- **APIs**:
  - `GET /api/v1/admin/rag/status` (Vector DB status)
  - `POST /api/v1/admin/rag/reindex` (Trigger knowledge reindexing)
- **Permissions**: `knowledge_base.view`, `knowledge_base.manage`

### Automation Jobs
- **Path**: `/automation-ops`
- **APIs**:
  - `GET /api/v1/admin/jobs` (Scheduler jobs)
  - `POST /api/v1/admin/jobs/{id}/run` (Force run)
- **Permissions**: `automation.view`, `automation.manage`

### Help Center
- **Path**: `/help-center`
- **APIs**:
  - `GET /api/v1/admin/help-center/articles`
  - `POST /api/v1/admin/help-center/articles`
- **Permissions**: `help_center.view`, `help_center.manage`

## 3. Governance & Security

### Security Overview
- **Path**: `/security`
- **APIs**:
  - `GET /api/v1/admin/security/overview` (Active alerts, login attempts)
  - `GET /api/v1/admin/security/blocked-ips`
- **Permissions**: `security.view`

### Admin Accounts
- **Path**: `/admins`
- **APIs**:
  - `GET /api/v1/admin/admins`
  - `POST /api/v1/admin/admins` (Invite admin)
- **Permissions**: `roles.view`, `users.manage`

### Roles & Permissions
- **Path**: `/roles`
- **APIs**:
  - `GET /api/v1/admin/roles`
- **Permissions**: `roles.view`

### Audit Logs
- **Path**: `/audit`
- **APIs**:
  - `GET /api/v1/admin/audit/logs`
- **Permissions**: `audit_logs.view`

### Break-Glass Access
- **Path**: `/breakglass`
- **APIs**:
  - `GET /api/v1/admin/break-glass/grants`
  - `POST /api/v1/admin/break-glass/request`
  - `POST /api/v1/admin/break-glass/grants/{id}/approve`
- **Permissions**: `security.view`, `break_glass.approve`

### Privacy Center
- **Path**: `/privacy`
- **APIs**:
  - `GET /api/v1/admin/privacy/requests` (Data export/deletion requests)
- **Permissions**: `privacy.view`

### Feature Flags
- **Path**: `/feature-flags`
- **APIs**:
  - `GET /api/v1/admin/feature-flags`
  - `PUT /api/v1/admin/feature-flags/{id}`
- **Permissions**: `feature_flags.view`, `feature_flags.manage`

### AI Configuration
- **Path**: `/ai-config`
- **APIs**:
  - `GET /api/v1/admin/ai-config/providers`
  - `PUT /api/v1/admin/ai-config/providers/{id}`
- **Permissions**: `ai.manage`

### System Health
- **Path**: `/health`
- **APIs**:
  - `GET /api/v1/admin/system/health` (Infrastructure diagnostics)
- **Permissions**: `system.health.view`

### App Settings
- **Path**: `/settings`
- **APIs**:
  - `GET /api/v1/admin/settings`
  - `PUT /api/v1/admin/settings`
- **Permissions**: `configuration.view`, `configuration.manage`

### Announcements
- **Path**: `/announcements`
- **APIs**:
  - `GET /api/v1/admin/announcements`
  - `POST /api/v1/admin/announcements`
  - `DELETE /api/v1/admin/announcements/{id}`
- **Permissions**: `support.manage`

---

## Global Services
- **Global Search**: `GET /api/v1/admin/search?q={query}` (Available on all pages)
- **Alerts Popover**: `GET /api/v1/admin/alerts` (Available on all pages)
