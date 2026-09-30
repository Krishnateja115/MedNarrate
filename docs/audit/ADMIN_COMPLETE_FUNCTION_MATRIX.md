# Admin Complete Function Matrix

| Feature | UI Exists? | Button Works? | Calls Backend? | Endpoint Exists? | Mutates Real Data? | Real Product Effect? | RBAC Protected? | Audited? | Tested? |
|---|---|---|---|---|---|---|---|---|---|
| Command Center | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Partial |
| Analytics | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Partial |
| Users | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Medical Reports | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Support Desk | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Incidents | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Admin Copilot | Yes | Yes | Yes | Yes | No | No (Placeholder) | Yes | Yes | Partial |
| AI Configuration | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Chat Operations | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Yes |
| RAG Knowledge Ops | Yes | Yes | Yes | Yes (Status/List) | Yes (Status change) | No (No upload) | Yes | Yes | Partial |
| Automation Ops | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Jobs | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Help Center | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Security | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Yes |
| Governance | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Admin Accounts | Yes | Yes | Yes | Yes | Yes (role_ids=[])| No (Unusable Admin) | Yes | Yes | Partial |
| Roles & Permissions | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Audit | Yes | Yes | Yes | Yes | No (Read-only) | N/A | Yes | No | Yes |
| Break Glass | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Privacy | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Settings (Maintenance)| Yes | Yes | Yes | Yes | Yes | No (DB Row only)| Yes | Yes | Partial |
| Feature Flags | Yes | Yes | Yes | Yes (Bug on Update)| Yes | No (No Evaluator)| Yes | Yes | Partial |
| Announcements | Yes | Yes | Yes | Yes | Yes | No (No frontend fetch)| Yes | Yes | Partial |
| Health | Yes | Yes | Yes | Yes | No | N/A | Yes | No | Yes |
| Global Search | Yes | Yes | Yes | Yes | No | N/A | Yes | No | Partial |
