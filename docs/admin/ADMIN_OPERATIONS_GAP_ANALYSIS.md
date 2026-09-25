# MedNarrate Admin Operations Platform: Gap Analysis

## Overview
This document evaluates the current state of the MedNarrate Admin Platform against the requirements of the Operations Platform Upgrade.

## 1. Command Center
**Status:** PARTIAL
- **Current Implementation:** `src/app/(protected)/page.tsx` provides high-level metrics for users, reports, AI analysis, system incidents, and a time-series chart. The backend `admin_dashboard.py` serves real data.
- **Backend Support:** `admin_dashboard.py` exists and is functional. Support tickets query is uninstrumented.
- **Frontend Support:** `page.tsx` exists and displays data nicely.
- **Missing Parts:** 
  - System Status checks (API, Database, LLMs, RAG, etc. are not broken down). 
  - "Needs Attention" area does not highlight support tickets.
- **Priority:** High

## 2. Complete User Management
**Status:** PARTIAL
- **Current Implementation:** Users list (`src/app/(protected)/users/page.tsx`) exists. Actions like suspend, activate, force_logout, change_role, and reset_password exist in `admin_users.py`.
- **Backend Support:** `admin_users.py` handles most basic requirements.
- **Frontend Support:** Exists.
- **Missing Parts:** Detailed profile view (`/users/[id]`) needs comprehensive tabs (Profile, Authentication, Sessions, Reports, Analyses, Chats, Reminders, Notifications, Support, Activity, Security) displaying real backend queries (e.g., Timeline of safe activity).
- **Priority:** High

## 3. Admin Team / Multiple Administrators
**Status:** PARTIAL
- **Current Implementation:** `admin_admins.py` handles listing admins, creating admins, assigning roles, deactivating. RBAC backend is robust (`AdminRole`, `AdminPermission`, `AdminRoleAssignment`).
- **Backend Support:** Strong RBAC data structures exist, APIs exist. Missing invitation workflow with pending status.
- **Frontend Support:** `/admins` page exists but requires UX evaluation and integration with Invitation workflow.
- **Missing Parts:** Formal Invitation Workflow (Email, Pending, Accepted), UI for the Role Matrix, Privilege Escalation Protection visualization.
- **Priority:** High

## 4. Reports as a Real Operations Center
**Status:** PARTIAL
- **Current Implementation:** Backend `admin_reports.py` and frontend `/reports` exist.
- **Missing Parts:** Detailed Processing pipeline UI per report (Upload -> Ext -> NER -> RAG -> Validation). Operations to Reprocess, Retry, and Open Incident.
- **Priority:** High

## 5. Support Desk
**Status:** PARTIAL
- **Current Implementation:** Backend models (`SupportTicket`, `SupportTicketMessage`) exist. Frontend `/support` exists.
- **Missing Parts:** Automatic diagnostic snapshot generation on ticket creation. UX for assignment, internal notes, and resolving tickets.
- **Priority:** High

## 6. AI Operations
**Status:** PARTIAL
- **Current Implementation:** `/ai-ops` exists in frontend, `admin_ai_ops.py` exists in backend.
- **Missing Parts:** Real metrics on provider health, latency tracking, fallback usage per request, and safe prompt visualization.
- **Priority:** Medium

## 7. AI / Admin Copilot
**Status:** MISSING
- **Current Implementation:** Not implemented. No backend endpoint, no frontend sidebar entry, no tool implementations.
- **Priority:** Critical

## 8. Chat / Copilot Sidebar Experience
**Status:** MISSING
- **Current Implementation:** Not implemented.
- **Priority:** Critical

## 9. RAG / Knowledge Management
**Status:** PARTIAL
- **Current Implementation:** `/rag-ops` frontend and `admin_rag_ops.py` backend.
- **Missing Parts:** Granular ingestion status, chunk visualization, document archival.
- **Priority:** Medium

## 10. Notifications / Jobs / Incidents
**Status:** PARTIAL
- **Current Implementation:** Incidents and Jobs have basic backend models and admin routes.
- **Missing Parts:** Notification admin endpoints. Incident assignment/investigation workflows.
- **Priority:** Medium

## 11. Analytics That Actually Matter
**Status:** PARTIAL
- **Current Implementation:** `/analytics` exists.
- **Missing Parts:** Strict alignment with specified metrics (Users, Reports, AI, Support, Notifications, Security) without fabricated charts.
- **Priority:** Medium

## 12. Security / Audit
**Status:** PARTIAL
- **Current Implementation:** `AdminAuditLog` model exists. `admin_audit.py` backend exists.
- **Missing Parts:** Advanced filtering for Who/What/When/Why. Distinction between general authentication events and sensitive access grants.
- **Priority:** High

## 13. Global Search
**Status:** PARTIAL
- **Current Implementation:** `admin_search.py` backend exists.
- **Missing Parts:** Frontend integration (e.g., search bar in Topbar triggering global search).
- **Priority:** High

## 14. Settings
**Status:** PARTIAL
- **Current Implementation:** Basic app settings.
- **Missing Parts:** Hiding raw secrets, displaying "Configured/Healthy" instead.
- **Priority:** Low

## 15. User Privacy / Sensitive Data
**Status:** PARTIAL
- **Current Implementation:** Break-glass access models exist (`SensitiveAccessGrant`).
- **Missing Parts:** Frontend UX to lock sensitive fields behind "Request Sensitive Access" workflows.
- **Priority:** High

## 16. Performance
**Status:** UNVERIFIED
- **Current Implementation:** Mostly raw FastAPI -> SQLAlchemy endpoints.
- **Missing Parts:** Need to audit N+1 queries and implement query caching/lazy loading where data gets large.
- **Priority:** Medium

## 17. Professional UX
**Status:** UNVERIFIED
- **Current Implementation:** Next.js + Tailwind + shadcn/ui.
- **Missing Parts:** Deep polish, transitions, skeletons for all new comprehensive data views.
- **Priority:** Medium
