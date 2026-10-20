# Admin Frontend → Backend Contract Matrix

All paths are under `/api/v1/admin` unless stated. Read routes return database-backed data. Mutation routes write audit rows through the shared audit service. `Super Admin` bypasses granular checks; all other access is server-authoritative.

| Frontend surface | Method/path family | Contract | Permission | Result |
|---|---|---|---|---|
| Command Center | GET `dashboard/summary`, `system/health`, `dashboard/alerts` | summary/services/alerts JSON | dashboard/system health | tests green |
| Analytics | GET `analytics`, `analytics/timeseries` | timeframe query + aggregates | analytics/dashboard | correctness green |
| Users | GET `users`, `{id}` and child tabs; POST actions | paginated `items`; detail/action bodies | users.view/manage | tests green |
| Reports | GET list/detail/sensitive; POST retry/reprocess | pagination/detail; grant-protected sensitive | reports.view/manage + grant | tests green |
| Support | GET queue/detail/suggestions; POST/PATCH/DELETE actions | ticket timeline, grounded article IDs, mutation bodies | support.view/manage/escalate | tests green |
| Incidents | GET list/detail; POST/PATCH | incident records and explicit update body | incidents.view/manage | tests green |
| Copilot | POST `copilot/chat` | bounded prompt, grounded response | dashboard.view | tests green |
| AI Ops | GET `ai-ops/overview/traces/failures` | `overview`, `traces`, `failures` | ai.view | bounded failure states |
| AI Config | GET/PUT `ai-config`; POST credential test | config fields; secrets write-only | ai aliases | tests green |
| Chat Ops | GET sessions/detail/messages/safety | pagination `items`; content requires grant | chat + sensitive grant | regression green |
| RAG Ops | GET documents/status; PATCH document status | pagination `items`; lifecycle enum | rag.view/manage | regression green |
| Automation | GET notifications/medications/jobs; POST retry | paginated operational rows | automation.view/manage | backend coverage |
| Notifications | GET logs; POST dispatch/retry | real backend contracts, no current page | notifications.view/manage | backend only |
| Help Center | GET/POST/PATCH articles; GET versions | article/status/category/version model | help_center.view/manage | help tests green |
| Security | GET overview/events | exact current counts/event rows | security.view | exact-count tests |
| Governance | GET overview | services/incidents/actions/controls/audit | scoped dashboard/security/health | route present |
| Admin Accounts | GET list/detail; POST create/status/roles/logout | safe admin record, role IDs, no secrets | admins.view/manage | account tests green |
| Admin Detail | GET `{id}/audit_logs`, `{id}/support_tickets` | `logs` and `tickets`; nullable fields safe | admins.view | 500 fixed |
| Roles | GET roles/permissions; POST role; PUT `{id}` | matrix and `permission_names` body | roles.view/manage | stale path fixed |
| Audit | GET `audit-logs`, `{id}` | paginated actor/metadata rows | `audit_logs:read` accepts `audit.view` | tests green |
| Break-glass | POST request/approve; GET grants/summary/detail; POST revoke | grant lifecycle and summary count | directional request/read/approve/revoke | tests green |
| Privacy | GET requests/history; PATCH status | privacy records | privacy aliases | backend coverage |
| Settings | GET/PUT settings/maintenance; POST maintenance | persisted settings bodies | settings aliases | backend coverage |
| Feature Flags | GET/POST/PUT/DELETE | flag records/toggle body | flag aliases | backend coverage |
| Announcements | GET/POST/PUT/DELETE | announcement records | announcement aliases | backend coverage |
| Topbar | GET alerts/search/grant summary; POST acknowledge | lightweight operational data only | endpoint permissions | component tests |

## Defects repaired

- Admin Detail now calls direct `GET /admins/{id}` rather than loading all admins.
- Support tickets use canonical `assigned_admin_id` and `title`, returning `200 {status, tickets}` for zero/nullable rows.
- Roles uses implemented `PUT /roles/{id}`, not nonexistent `/roles/{id}/permissions`.
- Admin status uses `currentIsActive`: active → deactivate, inactive → reactivate.
- Permission compatibility is directional; narrow read access cannot authorize approval/revoke/mutation routes.
