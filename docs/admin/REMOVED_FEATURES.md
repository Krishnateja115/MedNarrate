# Admin features removed (October 2026)

These admin pages were removed because they duplicated other pages, could never hold data, or did not work.
Older documents in this folder (status matrices, backend matrix, repair manifest) still mention them; read those as history.

| Removed | Why | Use instead |
|---|---|---|
| Admin Copilot (`/admin-copilot`, `POST /admin/copilot/chat`) | Hard-coded model, bypassed the app's AI provider chain, swallowed errors, repeated what the dashboard, incidents, audit and health pages show | Command Center, System Incidents, Audit Logs, System Health |
| Governance Center (`/governance`, `/admin/governance/*`) | Read-only page; maintenance mode is set in App Settings | App Settings |
| Privacy Operations (`/privacy`, `/admin/privacy/*`) | Could never hold data | Audit Logs, Break-Glass Access |
| Background Jobs (`/jobs`, `/admin/jobs/*`) | Duplicate of Automation Jobs | Automation Jobs (`/automation-ops`) |
| PubMedBERT retrieval model | Nothing in the app reads its output | Gemini embeddings (or BM25) for reports, MiniLM for the knowledge base |
