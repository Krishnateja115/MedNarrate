# MedNarrate Admin — API Reference

## Base URL
`/api/v1/admin`

## Endpoints Summary

### Analytics & Operations
- `GET /api/v1/admin/analytics?timeframe=7d`: Aggregated system metrics (Product, Reports, AI, Chat, Notifications).
- `GET /api/v1/admin/search?q={query}`: Cross-domain search across Users, Reports, Tickets, Incidents, and Audit Logs.
- `GET /api/v1/admin/alerts`: Active system operational alerts.
- `POST /api/v1/admin/alerts/{id}/acknowledge`: Mark alert as acknowledged.

### Governance & Security
- `GET /api/v1/admin/security/overview`: Real-time active sessions and threat metrics.
- `GET /api/v1/admin/security/events`: Administrative sign-in and session audit events.
- `POST /api/v1/admin/security/revoke-session`: Emergency session revocation.
- `GET /api/v1/admin/admins`: Administrative accounts management.
- `GET /api/v1/admin/roles`: RBAC Role & Granular Permission management.
- `GET /api/v1/admin/audit-logs`: Comprehensive audit log query and CSV export.
- `GET /api/v1/admin/break-glass`: Temporary sensitive data access grants.
- `GET /api/v1/admin/privacy/requests`: GDPR / HIPAA data subject requests.
- `GET /api/v1/admin/feature-flags`: Feature flag rollout configurations.
- `GET /api/v1/admin/settings`: Application settings and maintenance mode controls.
- `GET /api/v1/admin/announcements`: System announcement broadcasts.
