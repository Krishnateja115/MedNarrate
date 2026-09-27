# Admin Dead / Placeholder Feature Audit

| Location | Control | Evidence | Classification | Action |
|---|---|---|---|---|
| `mednarrate-admin-desktop/src/index.html` | Tauri welcome/greet form | starter template and `greet` Rust command; no Admin routes | DEAD/PLACEHOLDER | replace before desktop release |
| `mednarrate-admin/src/app/(protected)/rag-ops/page.tsx` | document upload | explicitly disabled “coming soon”; no ingestion route | INCOMPLETE | keep honestly disabled until backend exists |
| `mednarrate-admin/src/components/layout/topbar.tsx` | Governance Operational badge | label is not itself an action/metric | DECORATIVE | replace with query-backed status or remove |
| Notifications route | dispatch/log/retry UI | backend exists, no page | BACKEND_ONLY | implement if operationally required |
| Admin create form | role IDs | intentionally creates no roles; Admin Detail assigns roles | INTENTIONAL WORKFLOW | optionally add role selection later |
| AI Operations cards | failed API fallback | previously displayed zero-like values | BROKEN (fixed) | bounded errors and tests now present |
| Admin Detail tickets | stale fields | caused backend 500 | BROKEN (fixed) | canonical fields and retry state |
| Roles matrix | stale endpoint | called nonexistent `/permissions` child path | BROKEN (fixed) | canonical PUT path and contract test |

Input `placeholder=` text, skeletons, and empty-state copy are not fake functionality. Operational counts and charts are backend-derived.
