# Admin Dead Features

1. **Feature Flags**: Admin portal can manage feature flags, but they are never evaluated anywhere in the codebase.
2. **Maintenance Mode**: Admin portal can enable maintenance mode, but it only writes to the DB. No middleware or business logic blocks user requests based on this status.
3. **Announcements**: Announcements can be created in the Admin portal, but no Flutter frontend or mobile app endpoint ever fetches or displays them to the user.
4. **RAG Upload**: The RAG Ops UI exists, but backend lacks any ingestion, upload, chunking, or indexing endpoints. It only supports changing document status in the DB.
5. **Admin Copilot**: Uses keyword string matching ("user", "incident") instead of an LLM. It's a placeholder feature.
6. **Tauri Desktop**: The `mednarrate-admin-desktop` directory is an unmodified Tauri template application with no integration into MedNarrate.
