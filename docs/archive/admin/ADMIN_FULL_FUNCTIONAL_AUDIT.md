# MedNarrate Admin — Full Functional Audit

Audit baseline: commit `27614b0`. The inventory covered 108 first-party Admin web files excluding `node_modules`/`.next`, 68 authored desktop files excluding `node_modules`/`target`/generated Tauri schemas, all 30 `app/api/v1/admin*.py` routers, supporting models/services/schemas/RBAC/auth/database/migrations, and backend/frontend tests. Lockfiles, generated bundles, Tauri generated schemas, and vendored dependencies were classified rather than reviewed line by line.

`WORKING` requires frontend, backend, persistence, authorization, errors, and tests to agree. `PARTIAL` means a real implementation exists but final browser verification or a required surface remains.

| Feature | Frontend | Backend/DB | RBAC/Audit | Tests/runtime | Status | Immediate action |
|---|---|---|---|---|---|---|
| Command Center | metrics/health/alerts | real aggregates | dashboard/system health | API/build; browser pending | PARTIAL | browser smoke |
| Analytics | time-range charts | aggregate routes | analytics/dashboard | correctness tests; browser pending | PARTIAL | browser smoke |
| User Management | search/filter/mutations | users/sessions/profiles | users + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| User Detail | profile/tabs/actions | scoped detail routes | users + grants | backend coverage; browser pending | PARTIAL | browser smoke |
| Medical Reports | list/filter | reports/diagnostics | reports + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Report Detail | detail/sensitive/actions | detail/sensitive/retry | grant-protected/audited | backend coverage; browser pending | PARTIAL | browser smoke |
| Support Desk | queue/search/filter | ticket actions | support + audit | support tests; browser pending | PARTIAL | browser smoke |
| Support Ticket Detail | grounded articles/attachment | suggestions/link/reply/escalate | support + audit | help/support tests; browser pending | PARTIAL | browser smoke |
| Incidents | list/detail/create/update | incident routes | incidents + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Admin Copilot | prompt/history | bounded read-only chat | dashboard + audit | copilot tests; browser pending | PARTIAL | browser smoke |
| AI Operations | overview/traces/failures | telemetry routes | ai.view | failure tests; browser pending | PARTIAL | browser smoke |
| AI Configuration | view/update/test | config routes | ai config + audit | security tests; browser pending | PARTIAL | browser smoke |
| Chat Operations | paginated metadata/safety | sessions/events/messages | chat/grant + audit | regression tests; browser pending | PARTIAL | browser smoke |
| RAG Knowledge Ops | status/doc lifecycle | documents/status | rag + audit | regression tests; browser pending | PARTIAL | browser smoke |
| Automation Jobs | notification/reminder/jobs | automation routes | automation + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Notifications | no standalone page | dispatch/log/retry | notifications + audit | backend only | BACKEND_ONLY | implement Admin UI |
| Help Center | CRUD/publish/archive/search/preview/history | article/version routes | help/support + audit | backend tests; browser pending | PARTIAL | verify fresh seed content |
| Security Overview | exact metrics/events | security routes | security + audit | exact-count tests; browser pending | PARTIAL | browser smoke |
| Governance Center | status/incidents/actions/controls | governance overview | scoped controls/audit | backend route; browser pending | PARTIAL | browser smoke |
| Admin Accounts | list/create/status/sessions | lifecycle/detail | hierarchy + audit | 15 account tests; browser pending | PARTIAL | browser smoke |
| Admin Detail | direct/roles/audit/tickets | direct/detail/support/audit | admins + audit | UI/backend tests; browser pending | PARTIAL | browser smoke |
| Roles & Permissions | matrix/create/update | roles/catalog | roles + audit | contract/RBAC tests; browser pending | PARTIAL | browser smoke |
| Audit Logs | search/filter/pagination | audit list/detail | audit read | backend coverage; browser pending | PARTIAL | browser smoke |
| Break-glass | request/approve/revoke/summary | grant lifecycle | directional permissions/audit | security tests; browser pending | PARTIAL | browser smoke |
| Privacy | requests/history | privacy routes | privacy + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Settings/Maintenance | persisted controls | settings/maintenance | settings + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Feature Flags | CRUD/toggle | flag routes | flags + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Announcements | CRUD | announcement routes | announcements + audit | backend coverage; browser pending | PARTIAL | browser smoke |
| Health | service cards/refresh | real probes | system health | health tests; browser pending | PARTIAL | browser smoke |
| Global Search | debounced result modal | scoped search | per-result permissions | partial tests; browser pending | PARTIAL | browser/error coverage |
| Topbar | alerts/search/admin/summary | lightweight alert/search/summary | auth + audit | component tests; browser pending | PARTIAL | browser smoke |
| Admin desktop integration | Tauri starter shell | no shared Admin wiring | not exercised | starter only | PLACEHOLDER | replace shell |

## Release conclusion

Automated repository gates are green, but the final browser smoke pass was blocked by the local browser-control usage-limit reviewer after the login page was opened. The missing Notifications UI and starter Tauri shell remain real gaps.
