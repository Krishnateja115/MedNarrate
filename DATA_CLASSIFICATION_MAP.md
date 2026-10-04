# MedNarrate Data Classification Map

## Classification Categories
- **PUBLIC**: Safe for unauthenticated or broad exposure.
- **INTERNAL**: Application metadata, foreign keys, internal IDs not meant for exposure but not sensitive.
- **PII**: Personally Identifiable Information (name, email, DOB, phone).
- **PHI**: Protected Health Information (reports, analysis, chat content, profiles).
- **AUTH SECRET**: Cryptographic material, tokens, passwords.
- **SECURITY AUDIT**: Immutable audit records, access logs.
- **OPERATIONAL**: System configuration, feature flags, metrics, retry queues.

## Models

### User (user.py)
- `id`: INTERNAL
- `email`: PII
- `hashed_password`: AUTH SECRET
- `full_name`: PII
- `role`: INTERNAL
- `preferred_language`: PII
- `date_of_birth`: PII / PHI (depending on context, strict PII)
- `gender`: PII
- `is_active`: INTERNAL
- `created_at`, `updated_at`: INTERNAL
- `mfa_enabled`: INTERNAL
- `mfa_secret`: AUTH SECRET
- `mfa_recovery_codes`: AUTH SECRET
- `session_version`: AUTH SECRET (invalidates sessions)
- `last_totp_counter`: INTERNAL

### Report (report.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `file_path`: INTERNAL (Storage locator)
- `title`: PHI (may contain condition names)
- `hospital`: PHI / PII
- `report_date`: PHI
- `file_name`: PHI (may contain names)
- `file_type`: INTERNAL
- `report_type`: PHI
- `processing_status`: INTERNAL
- `created_at`, `updated_at`: INTERNAL

### ReportAnalysis (report_analysis.py)
- `id`: INTERNAL
- `report_id`: INTERNAL
- `extracted_text`: PHI
- `clinician_summary`: PHI
- `patient_summary`: PHI
- `structured_data`: PHI
- `model_version`: INTERNAL
- `is_verified`: INTERNAL
- `created_at`, `updated_at`: INTERNAL

### ReportTranslation & AnalysisTranslation (report_translation.py, analysis_translation.py)
- `id`: INTERNAL
- `report_id` / `analysis_id`: INTERNAL
- `target_language`: INTERNAL
- `translated_text`: PHI
- `created_at`: INTERNAL

### ChatSession & ChatMessage (chat.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `report_id`: INTERNAL
- `title`: PHI
- `created_at`, `updated_at`: INTERNAL
- (Message) `session_id`: INTERNAL
- (Message) `role`: INTERNAL
- (Message) `content`: PHI
- (Message) `created_at`: INTERNAL

### ChatSafetyEvent (chat_safety.py)
- `id`: INTERNAL
- `message_id`: INTERNAL
- `user_id`: INTERNAL
- `event_type`: SECURITY AUDIT
- `severity`: SECURITY AUDIT
- `details`: PHI / SECURITY AUDIT (can contain message snippet)
- `created_at`: INTERNAL

### MedicalProfile, DoctorProfile, CaregiverProfile
- `id`: INTERNAL
- `user_id`: INTERNAL
- `blood_group`: PHI
- `allergies`: PHI
- `chronic_conditions`: PHI
- `emergency_contact_name`: PII
- `emergency_contact_phone`: PII
- (Doctor) `specialty`, `license_number`: PII
- (Doctor) `hospital_affiliation`: PII
- (Caregiver) `relationship_to_patient`: PII
- `created_at`, `updated_at`: INTERNAL

### MedicationSchedule (medication_schedule.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `medication_name`: PHI
- `dosage`: PHI
- `frequency`: PHI
- `time_of_day`: PHI
- `start_date`, `end_date`: PHI
- `notes`: PHI
- `created_at`, `updated_at`: INTERNAL

**Access policy:** the admin endpoint `GET /api/v1/admin/users/{id}/reminders` (`users.view`) returns only `id`, `is_active`, `created_at` unless the admin holds an active break-glass grant for `medical_profile` on that user; medication name, dosage and frequency are then returned and the disclosure is audited as `SENSITIVE_MEDICATION_ACCESS`. Patient-side PATCH accepts an allowlisted field set only; `user_id` is immutable.

### SupportTicket & SupportTicketMessage (support.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `subject`: PII / PHI (if they mention health info)
- `status`: INTERNAL
- `category`: INTERNAL
- `priority`: INTERNAL
- `assigned_to`: INTERNAL
- `created_at`, `updated_at`: INTERNAL
- (Message) `ticket_id`: INTERNAL
- (Message) `sender_id`: INTERNAL
- (Message) `message`: PII / PHI
- (Message) `is_internal`: INTERNAL
- (Message) `created_at`: INTERNAL

### NotificationLog (notification_log.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `notification_type`: INTERNAL
- `title`: PII
- `body`: PII / PHI (can contain med reminders)
- `status`: INTERNAL
- `created_at`: INTERNAL

### PrivacyDataRequest (privacy.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `request_type`: INTERNAL
- `status`: INTERNAL
- `reason`: PII
- `admin_notes`: INTERNAL
- `requested_at`, `reviewed_at`, `completed_at`: INTERNAL

### AdminAuditLog (admin.py)
- `id`: INTERNAL
- `actor_admin_id`: INTERNAL
- `action`: SECURITY AUDIT
- `resource_type`, `resource_id`: INTERNAL
- `reason`: SECURITY AUDIT
- `result`: SECURITY AUDIT
- `ip_address`: SECURITY AUDIT
- `metadata_payload`: SECURITY AUDIT
- `timestamp`: INTERNAL

### SensitiveAccessGrant (admin.py)
- `id`: INTERNAL
- `admin_id`: INTERNAL
- `resource_type`, `resource_id`: INTERNAL
- `status`: SECURITY AUDIT
- `reason`: SECURITY AUDIT
- `expires_at`: SECURITY AUDIT
- `created_at`, `updated_at`: INTERNAL

### RagChunk (rag_chunk.py)
- `id`: INTERNAL
- `user_id`: INTERNAL
- `report_id`: INTERNAL
- `chunk_index`: INTERNAL
- `content`: PHI
- `embedding`: PHI (Vectorized PHI)
- `created_at`: INTERNAL

### OrphanFile (orphan_file.py)
- `id`: INTERNAL
- `file_path`: INTERNAL
- `storage_backend`: INTERNAL
- `status`: OPERATIONAL
- `retry_count`: OPERATIONAL
- `last_error_code`: OPERATIONAL
- `created_at`, `last_attempt_at`, `resolved_at`: OPERATIONAL
