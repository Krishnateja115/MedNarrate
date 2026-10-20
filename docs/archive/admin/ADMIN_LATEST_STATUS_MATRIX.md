# Admin Feature Status Matrix

This matrix evaluates the current (latest) state of the MedNarrate Admin Web Application and its backend components.

| Feature | Frontend | Backend | Database | Tests | Integration | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dashboard / Command Center | Complete | Complete | Complete | Partial | Complete | |
| Users | Complete | Complete | Complete | Complete | Complete | Pagination integrated |
| User Detail | Complete | Complete | Complete | Complete | Complete | Extended profiles wired successfully |
| Admin Team | Complete | Complete | Complete | Complete | Complete | |
| Roles & Permissions | Complete | Complete | Complete | Complete | Complete | |
| Reports | Complete | Complete | Complete | Complete | Complete | |
| Report Detail | Complete | Complete | Complete | Complete | Complete | Break-glass access required for sensitive data |
| Support | Complete | Complete | Complete | Partial | Complete | |
| Help Center | Partial | Complete | Complete | Missing | Broken | Frontend mapped correctly, but Database table `help_articles` has 0 entries (Missing seed data). |
| AI Operations | Complete | Complete | Complete | Partial | Complete | Traces & Failures wired correctly. |
| Chat Operations | Broken | Complete | Complete | Partial | Broken | **Bug**: Frontend expects `sessionsData.sessions.map` but backend pagination returns `items`. |
| RAG Operations | Broken | Complete | Complete | Partial | Broken | **Bug**: Frontend expects `documentsData.documents.map` but backend pagination returns `items`. |
| Notifications | Missing | Complete | Complete | Partial | Missing | Backend endpoint exists, frontend UI missing completely. |
| Jobs (Scheduler) | Complete | Complete | Complete | Partial | Complete | Currently shows degraded because scheduler is stopped. |
| Incidents | Complete | Complete | Complete | Partial | Complete | |
| Analytics | Complete | Complete | Complete | Missing | Complete | |
| Health | Complete | Complete | Complete | Complete | Complete | Accurately reporting degraded status due to LLM success rate & scheduler. |
| Security | Broken | Complete | Complete | Partial | Broken | **Bug**: Frontend expects `active_admins_count` etc., but backend returns `total_admins` etc. Keys mismatch entirely. |
| Audit | Complete | Complete | Complete | Complete | Complete | |
| Break-glass | Complete | Complete | Complete | Complete | Complete | |
| Privacy | Complete | Complete | Complete | Missing | Complete | |
| Settings | Complete | Complete | Complete | Missing | Complete | |
| Feature Flags | Complete | Complete | Complete | Missing | Complete | |
| Maintenance | Missing | Partial | Missing | Missing | Missing | |
| Governance Controls | Partial | N/A | N/A | N/A | Partial | "Governance Operational" badge in topbar is nonfunctional (UI only). |
| Admin Copilot | Complete | Complete | Complete | Complete | Complete | Wired to chat interface. |
| Global Search | Complete | Complete | Complete | Partial | Complete | |
| Branding | Complete | N/A | N/A | N/A | Complete | Logo is currently just a generic Lucide Activity icon. Ready to be replaced. |
