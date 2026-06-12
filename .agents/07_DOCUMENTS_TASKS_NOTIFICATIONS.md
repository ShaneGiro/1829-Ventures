# Agent 07: Documents, Tasks, And Notifications

## Goal

Implement S3-compatible document storage flow, tasks, task reminders, notification records, SendGrid email dispatch, and daily digests.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `02_MODELS_MIGRATIONS.md`
- `04_CORE_CRM_API.md`

## May Edit

- `backend/app/api/routes/tasks.py`
- `backend/app/api/routes/documents.py`
- `backend/app/services/task_service.py`
- `backend/app/services/document_service.py`
- `backend/app/services/notification_service.py`
- `backend/app/integrations/storage.py`
- `backend/app/integrations/minio_storage.py`
- `backend/app/integrations/sendgrid.py`
- `backend/app/workers/jobs/notification_jobs.py`
- Related repositories, schemas, and tests.

## Avoid

- Ritchie agent behavior (Agent 10). There is no proposal/approval email workflow in the plan — do not build one.
- Gmail ingestion (Agent 09).
- Frontend UI.

## Expected Output

- Document metadata persists in Postgres.
- Presigned upload flow exists through storage abstraction.
- MinIO implements S3-compatible storage locally.
- Tasks support owner, creator/source, watchers, due date, status, priority, linked entity, and completion history.
- Task reassignment notifies new owner.
- Daily digest bundles overdue, due today, and optional upcoming tasks.
- Unassigned tasks appear in shared queue and are not emailed to everyone in v1.

## Tests To Add Or Run

- Task assignment and reassignment tests.
- Digest selection tests.
- Document metadata and storage adapter tests.

## Definition Of Done

- Tasks and documents can support company detail workflows.
- Notification service is channel-agnostic.
- SendGrid integration reads credentials from environment variables.
