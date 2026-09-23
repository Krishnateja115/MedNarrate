# MedNarrate Admin — RBAC Roles & Permissions Matrix

## Privilege Hierarchy
1. **Super Admin**: Bypasses granular permission checks. Full access across all governance, security, and infrastructure tools.
2. **Security Admin**: Access to `/security`, `/admins`, `/roles`, `/audit`, `/breakglass`, and `/privacy`.
3. **Support Admin**: Access to `/support`, `/users`, `/reports`, `/help-center`. Restricted from modifying role permissions or granting break-glass access.
4. **AI & Data Ops Admin**: Access to `/ai-ops`, `/chat-ops`, `/rag-ops`, `/ai-config`, `/feature-flags`.

## Permission Codes Inventory
| Permission Code | Category | Target Resource | Description |
|---|---|---|---|
| `admin` | SuperAdmin | Global | Full administrative bypass |
| `users.view` | Core Ops | Users | View user accounts & profiles |
| `users.manage` | Core Ops | Users | Deactivate / reset user accounts |
| `reports.view` | Core Ops | Reports | View medical reports & diagnostics |
| `reports.manage` | Core Ops | Reports | Reprocess / retry report pipelines |
| `support.view` | Support | Support | View support tickets |
| `support.manage` | Support | Support | Assign, update ticket status & reply |
| `security.view` | Security | Security | View security overview & active sessions |
| `security.manage` | Security | Security | Revoke admin sessions & manage admins |
| `roles.manage` | Security | RBAC | Manage role definitions & permissions |
| `audit.view` | Audit | Audit | View and export audit log streams |
| `breakglass.request`| Security | Privacy | Request temporary sensitive access |
| `privacy.manage` | Privacy | GDPR | Action data subject requests |
| `ai.view` | AI Ops | AI | View LLM telemetry & health |
| `ai.manage` | AI Ops | AI | Update LLM configuration & thresholds |
| `system.view` | Infra | System | View system health & incidents |
| `analytics.view` | Analytics | Metrics | View product & performance analytics |
