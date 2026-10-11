# MedNarrate deployment path

## Hosting recommendation

Use Google Cloud Run for the API, Cloud SQL for PostgreSQL/pgvector, Cloud
Storage for uploaded files, and a separate report-analysis worker. Cloud Run's
free allowance can cover a small prototype, but **no reliable free stack can
promise thousands of users** here: the always-available database, OCR/AI
requests, storage, bandwidth and worker compute have real costs. Set budgets
and alerts before inviting users. Do not upload real patient data until access
control, retention, backups, privacy terms and operational review are complete.

The code does not deploy itself. A GCP project, billing account, domain, secrets,
database, bucket and monitored worker runtime are still required.

## Report jobs

For local development, `ANALYSIS_EXECUTION_MODE=background` keeps the existing
single-process behavior. For any multi-instance/production deployment, set
`ANALYSIS_EXECUTION_MODE=worker` on the API and start the worker separately:

```sh
python -m app.analysis_worker
```

The `/process` endpoint commits `processing` to PostgreSQL; the worker polls
those rows. PostgreSQL advisory locks avoid duplicate concurrent execution and
release automatically if a worker process dies, allowing another process to
resume. No Alembic migration is needed for this mode. The worker must run
continuously; Cloud Run API scale-to-zero does not keep a background loop alive.
For Docker Compose, set `ANALYSIS_EXECUTION_MODE=worker` and start with the
`worker` profile; the profile shares the local upload volume.

For Cloud Run, run the worker in a suitable managed worker runtime or as a
scheduled Cloud Run Job using `python -m app.analysis_worker --once`. A scheduled
job adds queue delay and needs concurrency and duration sizing. The API should
not be considered production-ready until the worker runtime has been configured
and tested against real uploads.

## Required production configuration

- Apply all Alembic migrations to a managed PostgreSQL database before API and
  worker startup; use the project's expected schema revision.
- Set a strong `JWT_SECRET`, explicit `CORS_ORIGINS`, `ENVIRONMENT=production`,
  `ANALYSIS_EXECUTION_MODE=worker`, and a reachable `DATABASE_URL`.
- Use `STORAGE_BACKEND=gcs` and `STORAGE_BUCKET_NAME` for shared files. Local
  disk is not shared or durable across Cloud Run instances. Grant the API and
  worker only the storage/database permissions they need.
- Configure the chosen AI provider and authentication; check API quotas and
  per-report cost. The worker needs the same secrets as the API.
- Add monitoring for queued reports, stage durations, failed reports, worker
  restarts, database saturation and AI-provider failures. Configure backups and
  retention for patient data.
- Use a shared rate-limit store before running multiple API replicas. Current
  in-process counters do not coordinate across replicas.

## Rollout checks

1. Verify `/health` and one login on the deployed API.
2. Upload a known lab report and a non-medical invoice. The report should
   finish; the invoice should receive `NOT_MEDICAL_REPORT`.
3. Restart the worker during a test report and confirm it resumes rather than
   leaving the report permanently processing.
4. Check Android upload, Reports, provisional-range labeling, and translation.
5. Load-test with synthetic documents before increasing traffic; tune worker
   replicas and AI quotas based on measured stage timing, not a free-tier claim.
