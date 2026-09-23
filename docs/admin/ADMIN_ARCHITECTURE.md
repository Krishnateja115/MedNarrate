# MedNarrate Admin — System Architecture

## Overview
MedNarrate Admin is an enterprise-grade administrative and security governance web application built independently from the primary MedNarrate consumer platform.

## Architecture Stack
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide Icons, Client-side Contexts.
- **Backend API**: FastAPI (Python 3.11), Pydantic v2, SQLAlchemy (Async), PostgreSQL / SQLite.
- **Authentication**: JWT Bearer Tokens with Granular RBAC (`AdminContext`) and Audit Logging (`AdminAuditLog`).
- **Data Boundary**: Zero PHI/PII stored in diagnostic telemetry or audit logs.

## Core Component Modules
1. **Command Center (`/`)**: High-level platform health, system alerts, quick operational metrics.
2. **Analytics (`/analytics`)**: Product retention, Report pipelines, AI telemetry, Chat safety, Notification delivery.
3. **Security Center (`/security`)**: Real-time administrative session tracking, threat signals, emergency session revocation.
4. **Admin Management (`/admins`, `/roles`)**: Granular role-based access control, custom permission trees, role assignments.
5. **Break-Glass Access (`/breakglass`)**: Strictly timed temporary sensitive access grants with mandatory justification logs.
6. **Privacy Center (`/privacy`)**: GDPR / HIPAA Data Subject Request management (export, rectification, erasure).
7. **Feature Flags & Settings (`/feature-flags`, `/settings`)**: Dynamic feature toggling, maintenance mode controls.
8. **System Incidents & Diagnostics (`/incidents`, `/ai-ops`, `/rag-ops`)**: Operational monitoring, AI request tracing, RAG vector index operations.
