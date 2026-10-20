# Admin Frontend Backend Contracts

### Misalignments Found:
1. **Admin Creation**: Frontend sends `role_ids: []` but backend expects a valid list of roles for the admin to be functional.
2. **Notification Dispatch**: Frontend expects a real dispatch, backend mocks it out.
3. **Feature Flags**: Frontend allows updating by name, backend crashes on `uuid.UUID(name)`.
4. **RAG Ops**: Frontend has "Upload coming soon", backend is completely missing endpoints for actual document ingestion.
